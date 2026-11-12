"""一次跑完全部檢查項目，印出摘要表，並把完整輸出寫進記錄檔。

用法：check.py [--config <路徑>] [--only <項目名稱>] [--list]

exit code：0 全部通過；1 至少一項失敗；2 參數錯誤。
標準輸出的最後一行是記錄檔路徑（相對於 repo 根目錄）。
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path(__file__).resolve().with_name("check_steps.toml")
LOG_DIR = Path("outputs") / "check"
PYTEST_NO_TESTS = 5
NOT_FOUND_CODE = 127


@dataclass
class Step:
    name: str
    command: list[str]


@dataclass
class Outcome:
    step: Step
    argv: list[str]
    exit_code: int
    output: str
    passed: bool
    note: str = ""


class ConfigError(Exception):
    """設定檔讀不到或格式不對。"""


def load_steps(path: Path) -> list[Step]:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except OSError as exc:
        raise ConfigError(f"讀不到設定檔 {path}：{exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"設定檔 {path} 不是合法的 TOML：{exc}") from exc
    steps: list[Step] = []
    for index, raw in enumerate(data.get("step", []), start=1):
        name = raw.get("name")
        command = raw.get("command")
        if not isinstance(name, str) or not name:
            raise ConfigError(f"設定檔第 {index} 個 [[step]] 缺少 name")
        if not isinstance(command, list) or not command or not all(isinstance(part, str) for part in command):
            raise ConfigError(f"設定檔的項目 {name} 的 command 必須是非空的字串陣列")
        steps.append(Step(name=name, command=list(command)))
    if not steps:
        raise ConfigError(f"設定檔 {path} 沒有任何 [[step]]")
    names = [step.name for step in steps]
    if len(set(names)) != len(names):
        raise ConfigError(f"設定檔 {path} 的項目名稱重複")
    return steps


def env_bin_dir() -> Path:
    """目前環境放執行檔的目錄（venv 的 Scripts 或 bin）。"""
    return Path(sys.executable).parent


def resolve_command(command: list[str]) -> list[str]:
    """把指令第一個元素解析成實際的執行檔。

    Windows 的 venv python.exe 只是 launcher，直接寫 "python" 會跑到 base interpreter
    （見 docs/lessons/L-0003），所以 "python" 一律換成 sys.executable；
    其他執行檔先找目前環境的目錄，再找 PATH。
    """
    head, *rest = command
    if head == "python":
        return [sys.executable, *rest]
    found = shutil.which(head, path=str(env_bin_dir())) or shutil.which(head)
    return [found or head, *rest]


def child_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PATH"] = str(env_bin_dir()) + os.pathsep + env.get("PATH", "")
    return env


def is_pytest(command: list[str]) -> bool:
    return any(Path(part).stem.lower() == "pytest" for part in command)


def run_step(step: Step) -> Outcome:
    argv = resolve_command(step.command)
    try:
        proc = subprocess.run(
            argv,
            cwd=REPO_ROOT,
            env=child_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as exc:
        return Outcome(
            step=step,
            argv=argv,
            exit_code=NOT_FOUND_CODE,
            output=f"無法啟動指令：{exc}\n",
            passed=False,
        )
    output = proc.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
    if proc.returncode == 0:
        return Outcome(step, argv, 0, output, passed=True)
    if proc.returncode == PYTEST_NO_TESTS and is_pytest(step.command):
        return Outcome(step, argv, proc.returncode, output, passed=True, note="無測試")
    return Outcome(step, argv, proc.returncode, output, passed=False)


def format_summary(outcomes: list[Outcome]) -> str:
    name_width = max(len("項目"), *(len(o.step.name) for o in outcomes))
    lines = [f"{'項目'.ljust(name_width)}  exit code  結果"]
    for o in outcomes:
        verdict = "通過" if o.passed else "失敗"
        if o.note:
            verdict += f"（{o.note}）"
        lines.append(f"{o.step.name.ljust(name_width)}  {str(o.exit_code).ljust(9)}  {verdict}")
    return "\n".join(lines)


def format_log(outcomes: list[Outcome], started: datetime) -> str:
    parts = [f"check.py 記錄檔 {started.strftime('%Y-%m-%d %H:%M:%S')}\n"]
    for o in outcomes:
        parts.append(
            f"\n===== {o.step.name} =====\n"
            f"指令：{subprocess.list2cmdline(o.argv)}\n"
            f"----- 輸出 -----\n"
            f"{o.output}"
            f"{'' if o.output.endswith(chr(10)) or not o.output else chr(10)}"
            f"----- exit code：{o.exit_code} -----\n"
        )
    return "".join(parts)


def write_log(text: str, started: datetime) -> Path:
    log_dir = REPO_ROOT / LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    stem = started.strftime("%Y%m%d-%H%M%S")
    path = log_dir / f"{stem}.log"
    counter = 1
    while path.exists():
        counter += 1
        path = log_dir / f"{stem}-{counter}.log"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="check.py", description="依序執行全部檢查項目，並把完整輸出寫進記錄檔")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="檢查設定檔（TOML），預設 scripts/check_steps.toml",
    )
    parser.add_argument("--only", metavar="項目名稱", help="只執行指定的項目")
    parser.add_argument("--list", action="store_true", help="每行印一個項目名稱，不執行任何項目")
    return parser


def use_utf8_output() -> None:
    """不論主控台的編碼為何，stdout 與 stderr 一律以 UTF-8 輸出。"""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        steps = load_steps(args.config)
    except ConfigError as exc:
        print(f"參數錯誤：{exc}", file=sys.stderr)
        return 2

    if args.list:
        for step in steps:
            print(step.name)
        return 0

    if args.only is not None:
        selected = [step for step in steps if step.name == args.only]
        if not selected:
            available = "、".join(step.name for step in steps)
            print(f"參數錯誤：沒有名為 {args.only} 的項目。可用的項目：{available}", file=sys.stderr)
            return 2
        steps = selected

    started = datetime.now()
    outcomes = [run_step(step) for step in steps]

    log_path = write_log(format_log(outcomes, started), started)
    print(format_summary(outcomes))
    print(log_path.relative_to(REPO_ROOT).as_posix())
    return 0 if all(o.passed for o in outcomes) else 1


if __name__ == "__main__":
    use_utf8_output()
    sys.exit(main())
