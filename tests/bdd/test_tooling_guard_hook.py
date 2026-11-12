"""features/tooling/guard_hook.feature 的 step definitions。

hook 只讀 stdin、不寫檔，在共用的 repo 副本中以 `uv run python scripts/hooks/guard_paths.py` 執行，
cwd 與 hook 輸入的 `cwd` 欄位都是副本的根目錄。
"""

from __future__ import annotations

import json
from pathlib import Path

import bdd_support as bs
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios(str(bs.FEATURES_DIR / "guard_hook.feature"))

HOOK = "scripts/hooks/guard_paths.py"


def _hook_repo(ctx: dict, request: pytest.FixtureRequest) -> Path:
    bs.require_file(bs.REPO_ROOT, HOOK)
    if "repo" not in ctx:
        ctx["repo"] = request.getfixturevalue("synced_repo")
    return ctx["repo"]


def _payload(repo: Path, tool: str, file_path: str) -> str:
    if tool == "Write":
        tool_input = {"file_path": file_path, "content": "x\n"}
    elif tool == "Edit":
        tool_input = {"file_path": file_path, "old_string": "a", "new_string": "b"}
    else:
        raise AssertionError(f"未支援的工具：{tool}")
    return json.dumps(
        {
            "session_id": "bdd-guard-hook",
            "transcript_path": "",
            "cwd": str(repo),
            "hook_event_name": "PreToolUse",
            "tool_name": tool,
            "tool_input": tool_input,
        },
        ensure_ascii=False,
    )


# ---------------------------------------------------------------- Given


@given(
    parsers.parse('防護 hook 收到 implementer 的 "{tool}" 請求，目標檔案是 "{path}"')
)
def request_for_path(
    ctx: dict, request: pytest.FixtureRequest, tool: str, path: str
) -> None:
    repo = _hook_repo(ctx, request)
    ctx["path"] = path
    ctx["stdin"] = _payload(repo, tool, path)


@given(
    parsers.parse(
        '防護 hook 收到 implementer 的 "{tool}" 請求，目標檔案是 repo 根目錄下 "{rel}" 的絕對路徑，使用反斜線分隔'
    )
)
def request_for_windows_abs_path(
    ctx: dict, request: pytest.FixtureRequest, tool: str, rel: str
) -> None:
    repo = _hook_repo(ctx, request)
    abs_path = (
        str(repo.resolve()).replace("/", "\\").rstrip("\\")
        + "\\"
        + rel.replace("/", "\\")
    )
    ctx["path"] = abs_path
    ctx["stdin"] = _payload(repo, tool, abs_path)


@given("防護 hook 收到一段不是合法 JSON 的輸入")
def request_not_json(ctx: dict, request: pytest.FixtureRequest) -> None:
    _hook_repo(ctx, request)
    ctx["stdin"] = (
        '{"tool_name": "Write", "tool_input": {"file_path": features/x.feature'
    )


@given(parsers.parse('一個要求修改 "{path}" 的測試任務'))
def manual_task(path: str) -> None:
    bs.skip_manual()


@given("主 session 與 verifier 各要修改一個 tests/bdd/ 底下的檔案")
def manual_main_and_verifier() -> None:
    bs.skip_manual()


# ---------------------------------------------------------------- When


@when("hook 執行完畢")
def run_hook(ctx: dict) -> None:
    # Claude Code 執行 hook 時會提供 CLAUDE_PROJECT_DIR；這裡讓它與 cwd、JSON 的 cwd 一致，都指向副本根目錄。
    ctx["result"] = bs.run(
        [bs.uv_exe(), "run", "python", HOOK],
        cwd=ctx["repo"],
        stdin=ctx["stdin"],
        env_extra={"CLAUDE_PROJECT_DIR": str(ctx["repo"])},
    )


@when("主 session 派發 implementer 執行這個任務")
def manual_dispatch() -> None:
    bs.skip_manual()


@when("它們用 Edit 修改")
def manual_edit() -> None:
    bs.skip_manual()


# ---------------------------------------------------------------- Then


@then("這個請求被擋下")
def blocked(ctx: dict) -> None:
    result: bs.Result = ctx["result"]
    assert result.returncode == 2, result.describe()


@then("這個請求被放行")
def allowed(ctx: dict) -> None:
    result: bs.Result = ctx["result"]
    assert result.returncode == 0, result.describe()


@then(parsers.parse('回給 implementer 的訊息包含 "{text}"'))
def message_contains(ctx: dict, text: str) -> None:
    result: bs.Result = ctx["result"]
    # exit code 2 時 Claude Code 把 stderr 回給 agent。
    assert text in result.stderr, result.describe()


@then("回給 implementer 的訊息說明應改為寫進實作報告的「疑義」欄")
def message_mentions_doubts(ctx: dict) -> None:
    result: bs.Result = ctx["result"]
    assert "疑義" in result.stderr, result.describe()


@then("訊息說明無法解析請求")
def message_unparsable(ctx: dict) -> None:
    result: bs.Result = ctx["result"]
    assert "無法解析" in result.stderr, result.describe()


@then("人工確認 features/tooling/check.feature 沒有被修改")
def manual_not_modified() -> None:
    bs.skip_manual()


@then("人工確認 implementer 的回報中能看出它被擋下的原因")
def manual_reason_visible() -> None:
    bs.skip_manual()


@then("人工確認兩者都修改成功")
def manual_both_succeed() -> None:
    bs.skip_manual()
