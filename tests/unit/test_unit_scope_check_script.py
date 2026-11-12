from __future__ import annotations

from script_loader import load_script

scope = load_script("scripts/scope_check.py", "scope_check_under_test")

TASK = """# T-901 sample

| 欄位 | 內容 |
|---|---|
| 狀態 | steps |
| feature | features/probe/sample.feature |
| base commit | abc1234 |
| 重工次數 | 0 / 3 |

## 公開介面

文中提到 `## 允許修改的路徑（implementer）` 與 `## 紀錄` 不算標題。

## 允許修改的路徑（implementer）

- src/ragdoc/probe/
- `tests/unit/probe/`
- .claude/agents/implementer.md（只能加 frontmatter 的 `hooks`）

（固定放行、不必列出）

## 完成條件

- 全部通過

## 紀錄

| 日期 | 狀態 | 原因 |
|---|---|---|
| 2026-11-12 | steps | 建立 |
"""


def test_parse_allowed_strips_backticks_and_comments() -> None:
    assert scope.parse_allowed(TASK) == [
        "src/ragdoc/probe/",
        "tests/unit/probe/",
        ".claude/agents/implementer.md",
    ]


def test_is_allowed_respects_path_segments() -> None:
    allowed = ["src/ragdoc/probe/", "pyproject.toml"]
    assert scope.is_allowed("src/ragdoc/probe/detect.py", allowed)
    assert not scope.is_allowed("src/ragdoc/probe_extra/x.py", allowed)
    assert scope.is_allowed("pyproject.toml", allowed)
    assert not scope.is_allowed("pyproject.toml.bak", allowed)


def test_base_commit_field_is_read_from_the_header_table() -> None:
    assert scope.read_base_commit_field(TASK) == "abc1234"
    assert scope.read_base_commit_field("# 沒有欄位表") is None


def test_sha_pattern_rejects_placeholders() -> None:
    assert scope.SHA_PATTERN.match("9d6d0a75d1f849617888d718dcb1450d68587a70")
    assert not scope.SHA_PATTERN.match("")
    assert not scope.SHA_PATTERN.match("（派 implementer 前由主 session 填）")
    assert not scope.SHA_PATTERN.match("abc12")


def test_strip_maintained_ignores_only_maintained_parts() -> None:
    edited = (
        TASK.replace("| 狀態 | steps |", "| 狀態 | impl |")
        .replace("| 重工次數 | 0 / 3 |", "| 重工次數 | 1 / 3 |")
        .replace("| base commit | abc1234 |", "| base commit | fffffff |")
        + "| 2026-11-13 | impl | 派發 |\n"
    )
    assert scope.strip_maintained(edited) == scope.strip_maintained(TASK)


def test_strip_maintained_detects_other_changes() -> None:
    added_line = TASK.replace("- 全部通過", "- 全部通過\n- 新增一條")
    other_feature = TASK.replace("features/probe/sample.feature", "features/probe/other.feature")
    assert scope.strip_maintained(added_line) != scope.strip_maintained(TASK)
    assert scope.strip_maintained(other_feature) != scope.strip_maintained(TASK)
