"""tests/bdd 共用工具（由 verifier 撰寫）。

只透過任務檔「公開介面」列出的指令與腳本操作系統，不 import `src/` 的內部實作。
所有會產生檔案的動作（uv sync、check.py、git repo）都在 pytest 的 tmp_path 底下的副本進行，
不修改 repo 本身。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = REPO_ROOT / "features" / "tooling"
COMMAND_TIMEOUT = 900  # 秒；uv sync 第一次可能要下載套件

# 子程序不應繼承的環境變數：外層 uv run / pytest 的環境不能漏進 repo 副本。
_DROP_ENV = (
    "VIRTUAL_ENV",
    "UV_PROJECT_ENVIRONMENT",
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONSTARTUP",
    "CONDA_PREFIX",
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
    "PYTEST_CURRENT_TEST",
    # Claude Code 會把它設成真實 repo；子程序在副本中執行，不能讓它指向真實 repo。
    "CLAUDE_PROJECT_DIR",
)


@dataclass
class Result:
    args: list[str]
    cwd: Path
    returncode: int
    stdout: str
    stderr: str

    @property
    def output(self) -> str:
        """標準輸出與標準錯誤合併。"""
        return self.stdout + "\n" + self.stderr

    def describe(self, limit: int = 4000) -> str:
        def cut(text: str) -> str:
            return (
                text
                if len(text) <= limit
                else text[:limit] + f"\n...（截斷，共 {len(text)} 字元）"
            )

        return (
            f"指令：{self.args}\n工作目錄：{self.cwd}\nexit code：{self.returncode}\n"
            f"--- stdout ---\n{cut(self.stdout)}\n--- stderr ---\n{cut(self.stderr)}"
        )


def child_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    for key in _DROP_ENV:
        env.pop(key, None)
    # 開發機 locale 是 cp950；要求子程序以 UTF-8 輸出，才能比對中文訊息。
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    # 避免在 repo 副本或暫存 git repo 裡產生 __pycache__。
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra:
        env.update(extra)
    return env


def _decode(data: bytes | None) -> str:
    if not data:
        return ""
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n")


def run(
    args: list[str],
    cwd: Path,
    *,
    stdin: str | None = None,
    env_extra: dict[str, str] | None = None,
    timeout: int = COMMAND_TIMEOUT,
) -> Result:
    proc = subprocess.run(
        [str(a) for a in args],
        cwd=str(cwd),
        input=stdin.encode("utf-8") if stdin is not None else None,
        capture_output=True,
        env=child_env(env_extra),
        timeout=timeout,
        check=False,
    )
    return Result(
        args=[str(a) for a in args],
        cwd=cwd,
        returncode=proc.returncode,
        stdout=_decode(proc.stdout),
        stderr=_decode(proc.stderr),
    )


def uv_exe() -> str:
    exe = shutil.which("uv")
    assert exe, "找不到 uv 執行檔（PATH 中沒有 uv）"
    return exe


# ---------------------------------------------------------------- repo 副本


def worktree_files() -> list[Path]:
    """repo 工作目錄中「會被 clone 帶走」的檔案：已追蹤 + 未追蹤但未被 .gitignore 忽略。

    用工作目錄而不是 git clone，verify 階段才看得到 implementer 尚未 commit 的修改。
    """
    git = shutil.which("git")
    assert git, "找不到 git 執行檔"
    proc = subprocess.run(
        [git, "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        check=True,
    )
    names = [n for n in proc.stdout.decode("utf-8").split("\0") if n]
    return [Path(n) for n in names if (REPO_ROOT / n).is_file()]


def copy_worktree(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    for rel in worktree_files():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / rel, target)
    return dest


def require_file(root: Path, rel: str) -> Path:
    path = root / rel
    assert path.is_file(), f"尚未實作：{rel} 不存在（{path}）"
    return path


def uv_sync(repo: Path, *extra: str) -> Result:
    return run([uv_exe(), "sync", *extra], cwd=repo)


def make_synced_copy(dest: Path) -> Path:
    """建立 repo 副本並執行 uv sync；失敗時直接讓情境失敗並附上輸出。"""
    copy_worktree(dest)
    require_file(dest, "pyproject.toml")
    result = uv_sync(dest)
    assert result.returncode == 0, "repo 副本的 uv sync 失敗\n" + result.describe()
    return dest


def run_check(repo: Path, args: list[str]) -> Result:
    require_file(repo, "scripts/check.py")
    return run([uv_exe(), "run", "python", "scripts/check.py", *args], cwd=repo)


# ---------------------------------------------------------------- 輸出解析


def word_pattern(word: str) -> re.Pattern[str]:
    """整個詞比對：前後不能是英數、底線或連字號。"""
    return re.compile(rf"(?<![\w-]){re.escape(word)}(?![\w-])")


def has_number_token(text: str, number: int) -> bool:
    """text 中有單獨的數字 number（前後不是英數、底線或小數點）。"""
    return re.search(rf"(?<![\w.]){number}(?![\w.])", text) is not None


def summary_row(stdout: str, name: str) -> str | None:
    """摘要表中某一項的那一列：含項目名稱（整個詞）且含「通過」或「失敗」的最後一行。"""
    pat = word_pattern(name)
    rows = [
        line
        for line in stdout.splitlines()
        if pat.search(line) and ("通過" in line or "失敗" in line)
    ]
    return rows[-1] if rows else None


def last_nonempty_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def log_path_from_stdout(repo: Path, stdout: str) -> Path:
    line = last_nonempty_line(stdout).strip("\"'")
    path = Path(line)
    if not path.is_absolute():
        path = repo / path
    return path


def skip_manual() -> None:
    pytest.skip(
        "待人工：@manual 情境只能由使用者驗證（見 docs/manual-checks/T-000.md）"
    )
