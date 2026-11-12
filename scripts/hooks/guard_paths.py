"""Claude Code PreToolUse hook：擋下 implementer 用 Write / Edit 修改受保護的路徑。

從 stdin 讀 hook 的 JSON 輸入，取 tool_input.file_path。
受保護路徑：features/、tests/bdd/、docs/tasks/。
exit code：0 放行；2 擋下（stderr 會回給 agent）。輸入無法解析時一律擋下。

只用標準函式庫，且 repo 根目錄以本檔位置推得（scripts/hooks/ 往上兩層）。
"""

from __future__ import annotations

import json
import posixpath
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED = ("features", "tests/bdd", "docs/tasks")
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:/")

EXIT_ALLOW = 0
EXIT_BLOCK = 2


def relative_to_repo(raw: str, root: Path = REPO_ROOT) -> str | None:
    """把 file_path 正規化成相對於 repo 根目錄、以 / 分隔的小寫路徑。

    支援相對路徑、`..`、Windows 絕對路徑與反斜線。不在 repo 底下時回傳 None。
    """
    text = raw.strip().replace("\\", "/")
    if text.startswith("/") or _WINDOWS_ABSOLUTE.match(text):
        root_text = root.resolve().as_posix()
        absolute = Path(text).resolve().as_posix() if _WINDOWS_ABSOLUTE.match(text) else text
        absolute = posixpath.normpath(absolute)
        prefix = root_text.rstrip("/") + "/"
        if absolute.lower() == root_text.lower():
            relative = "."
        elif absolute.lower().startswith(prefix.lower()):
            relative = absolute[len(prefix) :]
        else:
            return None
    else:
        relative = text
    normalized = posixpath.normpath(relative)
    if normalized == ".." or normalized.startswith("../") or normalized.startswith("/"):
        return None
    return normalized.lower()


def protected_prefix(raw: str, root: Path = REPO_ROOT) -> str | None:
    """路徑落在受保護目錄底下時，回傳該目錄；否則回傳 None。"""
    relative = relative_to_repo(raw, root)
    if relative is None:
        return None
    for prefix in PROTECTED:
        if relative == prefix or relative.startswith(prefix + "/"):
            return prefix
    return None


def parse_file_path(stdin_bytes: bytes) -> str:
    """從 hook 輸入取出 tool_input.file_path；格式不對就丟 ValueError。"""
    try:
        # utf-8-sig：PowerShell 5.1 經管線傳入時會在開頭加 BOM。
        payload = json.loads(stdin_bytes.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"不是合法的 JSON：{exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("最上層不是 JSON 物件")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        raise ValueError("缺少 tool_input")
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path.strip():
        raise ValueError("缺少 tool_input.file_path")
    return file_path


def use_utf8_output() -> None:
    """不論主控台的編碼為何，stdout 與 stderr 一律以 UTF-8 輸出。"""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")


def main() -> int:
    try:
        file_path = parse_file_path(sys.stdin.buffer.read())
    except ValueError as exc:
        print(f"已擋下：無法解析 hook 的輸入（{exc}），為安全起見一律不放行。", file=sys.stderr)
        return EXIT_BLOCK
    prefix = protected_prefix(file_path)
    if prefix is None:
        return EXIT_ALLOW
    print(
        f"已擋下對受保護路徑的修改：{file_path}（屬於 {prefix}/）。\n"
        "implementer 不得修改 features/、tests/bdd/、docs/tasks/。\n"
        "如果你認為規格、測試或任務檔需要修改，請不要動它，"
        "改為把問題寫進實作報告 docs/reports/T-xxx-impl.md 的「疑義」欄，由主 session 判斷。",
        file=sys.stderr,
    )
    return EXIT_BLOCK


if __name__ == "__main__":
    use_utf8_output()
    sys.exit(main())
