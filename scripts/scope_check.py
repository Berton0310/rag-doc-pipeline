"""檢查 implementer 修改的檔案是否都在任務允許的路徑內。

用法（在 repo 根目錄）：scope_check.py T-xxx

- base commit 從工作目錄的任務檔讀；允許路徑從 base commit 版本的任務檔讀。
- 比對 base commit 到目前工作目錄的所有變動：已 commit、未 commit、未追蹤（不含 .gitignore 忽略的）、刪除。
- 任務檔本身：忽略欄位表的「狀態」「base commit」「重工次數」三列與「## 紀錄」段落，其餘有差異即標「嚴重」。
- 固定放行路徑定義在 scripts/scope.toml。

exit code：0 沒有越界；1 有越界；2 任務檔或 base commit 有問題。
只用標準函式庫。
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

SCOPE_TOML = Path(__file__).resolve().with_name("scope.toml")
TASKS_DIR = "docs/tasks"
SEVERE_PREFIXES = ("features/", "tests/bdd/")
MAINTAINED_ROWS = ("狀態", "base commit", "重工次數")
ALLOWED_HEADING = "## 允許修改的路徑（implementer）"
LOG_HEADING = "## 紀錄"
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{7,40}$")


class ScopeError(Exception):
    """任務檔或 base commit 有問題（exit code 2）。"""


@dataclass
class Violation:
    path: str
    severe: bool
    reason: str = ""


# ---------------------------------------------------------------- git


def run_git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-c", "core.quotepath=off", *args],
        capture_output=True,
        check=False,
    )


def git(*args: str) -> bytes:
    """執行 git；失敗就丟 ScopeError。"""
    proc = run_git(*args)
    if proc.returncode != 0:
        message = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ScopeError(f"git {' '.join(args)} 失敗：{message}")
    return proc.stdout


def git_ok(*args: str) -> bool:
    return run_git(*args).returncode == 0


def split_z(data: bytes) -> list[str]:
    return [item.decode("utf-8") for item in data.split(b"\0") if item]


def changed_paths(base: str) -> list[str]:
    """base 到工作目錄的變動：已追蹤的修改、新增、刪除，加上未追蹤且未被忽略的檔案。"""
    tracked = split_z(git("diff", "--name-only", "--no-renames", "-z", base, "--"))
    untracked = split_z(git("ls-files", "--others", "--exclude-standard", "-z"))
    return sorted(set(tracked) | set(untracked))


# ---------------------------------------------------------------- 任務檔


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def find_task_file(task_id: str) -> Path:
    matches = sorted(Path(TASKS_DIR).glob(f"{task_id}-*.md")) if Path(TASKS_DIR).is_dir() else []
    if not matches:
        raise ScopeError(f"找不到 {task_id} 的任務檔（docs/tasks/{task_id}-*.md）")
    return matches[0]


def read_base_commit_field(text: str) -> str | None:
    for line in normalize(text).split("\n"):
        match = re.match(r"^\|\s*base commit\s*\|(.*)\|\s*$", line)
        if match:
            return match.group(1).strip().strip("`").strip()
    return None


def section_lines(text: str, heading: str) -> list[str]:
    """某個 `## ` 標題（整行比對）底下的行，到下一個 `## ` 標題為止。"""
    lines = normalize(text).split("\n")
    collected: list[str] = []
    inside = False
    for line in lines:
        if line.startswith("## "):
            inside = line.strip() == heading
            continue
        if inside:
            collected.append(line)
    return collected


def parse_allowed(text: str) -> list[str]:
    entries: list[str] = []
    for line in section_lines(text, ALLOWED_HEADING):
        match = re.match(r"^\s*[-*]\s+(.*\S)\s*$", line)
        if not match:
            continue
        entry = match.group(1).replace("`", "")
        entry = entry.split("（", 1)[0].strip()
        entry = entry.replace("\\", "/")
        if entry.startswith("./"):
            entry = entry[2:]
        if entry:
            entries.append(entry)
    return entries


def strip_maintained(text: str) -> str:
    """移除主 session 維護的部分：欄位表的三列，以及「## 紀錄」段落。"""
    kept: list[str] = []
    in_header = True
    in_log = False
    for line in normalize(text).split("\n"):
        if line.startswith("## "):
            in_header = False
            in_log = line.strip() == LOG_HEADING
            if in_log:
                continue
        elif in_log:
            continue
        if in_header and any(re.match(rf"^\|\s*{row}\s*\|", line) for row in MAINTAINED_ROWS):
            continue
        kept.append(line)
    return "\n".join(kept).strip("\n")


def load_fixed_paths(task_id: str) -> list[str]:
    with SCOPE_TOML.open("rb") as handle:
        data = tomllib.load(handle)
    return [str(item).replace("{task}", task_id) for item in data.get("fixed", {}).get("paths", [])]


# ---------------------------------------------------------------- 比對


def is_allowed(path: str, allowed: list[str]) -> bool:
    for entry in allowed:
        if entry.endswith("/"):
            if path.startswith(entry):
                return True
        elif path == entry:
            return True
    return False


def check(task_id: str) -> list[Violation]:
    task_file = find_task_file(task_id)
    task_path = task_file.as_posix()
    work_text = task_file.read_text(encoding="utf-8")

    base = read_base_commit_field(work_text)
    if base is None or not SHA_PATTERN.match(base):
        raise ScopeError("任務檔沒有填 base commit（欄位是空的或不是 7 到 40 位的十六進位字串）")
    if not git_ok("rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"):
        raise ScopeError(f"base commit 不存在：{base}")
    shown = run_git("show", f"{base}:{task_path}")
    if shown.returncode != 0:
        raise ScopeError(f"base commit 中沒有 {task_id} 的任務檔（{base}:{task_path}）")
    base_text = normalize(shown.stdout.decode("utf-8"))

    allowed = parse_allowed(base_text) + load_fixed_paths(task_id)

    violations: list[Violation] = []
    for path in changed_paths(base):
        if path == task_path:
            if strip_maintained(base_text) != strip_maintained(work_text):
                violations.append(
                    Violation(
                        path, True, "任務檔在主 session 維護的部分（狀態、base commit、重工次數、紀錄）以外被修改"
                    )
                )
            continue
        if is_allowed(path, allowed):
            continue
        severe = path.startswith(SEVERE_PREFIXES)
        violations.append(Violation(path, severe, "不在任務允許的路徑內"))
    return violations


def use_utf8_output() -> None:
    """不論主控台的編碼為何，stdout 與 stderr 一律以 UTF-8 輸出。"""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not re.fullmatch(r"T-\d+", argv[1]):
        print("用法：scope_check.py T-xxx（在 repo 根目錄執行）", file=sys.stderr)
        return 2
    task_id = argv[1]
    try:
        violations = check(task_id)
    except ScopeError as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    if not violations:
        print(f"{task_id}：沒有超出範圍")
        return 0
    print(f"{task_id}：超出範圍的檔案共 {len(violations)} 個")
    for item in violations:
        tag = "嚴重" if item.severe else "越界"
        print(f"  [{tag}] {item.path}  （{item.reason}）")
    return 1


if __name__ == "__main__":
    use_utf8_output()
    sys.exit(main(sys.argv))
