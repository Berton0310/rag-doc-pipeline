"""features/tooling/scope_check.feature 的 step definitions。

每個情境在 work_dir 建一個獨立的 git repo，Background 照真實流程建立兩個 commit：

1. 「initial」commit：repo 工作目錄的 `scripts/`（受測的 scope_check.py 與 scope.toml）、
   `.gitignore` 與幾個範例檔案。這時還沒有任務檔（給「base commit 中沒有任務檔」的情境用）。
2. 任務檔（照 `docs/tasks/` 的真實格式，base commit 欄是佔位文字、允許路徑兩條）寫好後 commit，
   這個 commit 就是 base commit。
3. 把 base commit 的雜湊值填進工作目錄的任務檔，不 commit。

任務檔由 ctx 中的狀態（欄位表、允許路徑、公開介面、完成條件、紀錄）產生，
base 版本與工作目錄版本只在 step 有意修改的地方不同。

以 `uv run --project <已 sync 的 repo 副本> python scripts/scope_check.py T-901` 執行，
cwd 是暫存 git repo 的根目錄（Python 環境借用 repo 副本，避免每個情境都 uv sync）。
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import bdd_support as bs
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios(str(bs.FEATURES_DIR / "scope_check.feature"))

PLACEHOLDER_BASE = "（派 implementer 前由主 session 填）"
MISSING_HASH = "1234567890abcdef1234567890abcdef12345678"

# initial commit（base commit 之前）就存在、已追蹤的範例檔案
SEED_FILES = {
    "README.md": "# sample repo\n",
    ".gitignore": "outputs/\n__pycache__/\n",
    "src/ragdoc/probe/detect.py": "VALUE = 1\n",
    "features/tooling/check.feature": "Feature: sample\n",
    "tests/bdd/test_check.py": "def test_sample():\n    pass\n",
}

# 開頭欄位表的列，依真實任務檔的順序
FIELD_ORDER = ("狀態", "feature", "模組", "依賴任務", "base commit", "重工次數")


def _git_env(tmp_root: Path) -> dict[str, str]:
    global_cfg = tmp_root / "gitconfig-global"
    if not global_cfg.exists():
        global_cfg.write_text("", encoding="utf-8")
    return {
        "GIT_CONFIG_GLOBAL": str(global_cfg),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "bdd",
        "GIT_AUTHOR_EMAIL": "bdd@example.invalid",
        "GIT_COMMITTER_NAME": "bdd",
        "GIT_COMMITTER_EMAIL": "bdd@example.invalid",
    }


def _git_result(ctx: dict, *args: str) -> bs.Result:
    return bs.run(["git", *args], cwd=ctx["repo"], env_extra=ctx["git_env"])


def _git(ctx: dict, *args: str) -> str:
    result = _git_result(ctx, *args)
    assert result.returncode == 0, result.describe()
    return result.stdout.strip()


def _task_text(ctx: dict) -> str:
    task = ctx["task"]
    task_id = ctx["task_id"]
    rows = "\n".join(f"| {k} | {task['fields'][k]} |" for k in FIELD_ORDER)
    interface = "\n".join(f"- {line}" for line in task["interface"])
    allowed = "\n".join(f"- {p}" for p in task["allowed"])
    done = "\n".join(f"- {line}" for line in task["done"])
    log = "\n".join(f"| {d} | {s} | {r} |" for d, s, r in task["log"])
    return f"""# {task_id} 範例任務

| 欄位 | 內容 |
|---|---|
{rows}

## 公開介面

{interface}

## 允許修改的路徑（implementer）

{allowed}

（固定放行、不必列出：`docs/reports/{task_id}-impl.md`、`docs/lessons/`。定義見 `docs/ARCHITECTURE.md`「目錄與歸屬」。）

## 完成條件

{done}

## 紀錄

| 日期 | 狀態 | 原因 |
|---|---|---|
{log}
"""


def _render_task(ctx: dict) -> None:
    path: Path = ctx["repo"] / ctx["task_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_task_text(ctx), encoding="utf-8")


def _write(ctx: dict, rel: str, content: str) -> Path:
    path: Path = ctx["repo"] / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _is_tracked(ctx: dict, rel: str) -> bool:
    return _git_result(ctx, "ls-files", "--error-unmatch", "--", rel).returncode == 0


def _set_base(ctx: dict, commit: str) -> None:
    """把 base commit 的雜湊值填進工作目錄的任務檔（不 commit）。"""
    ctx["base"] = commit
    ctx["task"]["fields"]["base commit"] = commit
    _render_task(ctx)


def _ensure_tracked_at_base(ctx: dict, rel: str) -> None:
    """讓 rel 成為 base commit 中已追蹤的檔案（只給「各種形式的越界修改」的已追蹤變體用）。

    Background 的 base commit 沒有這個檔案，而同一個 Examples 的「新增了尚未追蹤的檔案」
    又需要它不存在，所以在這裡補一個只含這個檔案的 commit（用 pathspec，任務檔維持未 commit），
    並把工作目錄任務檔的 base commit 改成新的 HEAD。新 base 中的任務檔與原 base 相同。
    """
    assert not _is_tracked(ctx, rel), f"{rel} 已被追蹤"
    _write(ctx, rel, "ORIGINAL = True\n")
    _git(ctx, "add", "--", rel)
    _git(ctx, "commit", "-q", "-m", f"seed {rel}", "--", rel)
    _set_base(ctx, _git(ctx, "rev-parse", "HEAD"))


# ---------------------------------------------------------------- Background


@given(parsers.parse('一個 git repo，裡面有任務檔 "{task_path}"'))
def git_repo_with_task(ctx: dict, work_dir: Path, task_path: str) -> None:
    repo = work_dir / "repo"
    repo.mkdir()
    ctx["repo"] = repo
    ctx["git_env"] = _git_env(work_dir)
    ctx["task_path"] = task_path
    m = re.match(r"(T-\d+)-", Path(task_path).name)
    assert m, task_path
    ctx["task_id"] = m.group(1)
    ctx["base"] = None
    ctx["task"] = {
        "fields": {
            "狀態": "steps",
            "feature": "features/probe/sample.feature",
            "模組": "probe",
            "依賴任務": "無",
            "base commit": PLACEHOLDER_BASE,
            "重工次數": "0 / 3",
        },
        "interface": ["`detect(path)`：回傳偵測結果"],
        "allowed": [],
        "done": ["sample.feature 所有情境 PASS", "check.py 全部通過"],
        "log": [("2026-11-12", "draft", "建立")],
    }

    _git(ctx, "init", "-q", "-b", "main")
    _git(ctx, "config", "core.autocrlf", "false")
    # 受測腳本（scope_check.py、scope.toml 等）在 base commit 之前就在 repo 裡。
    scripts_src = bs.REPO_ROOT / "scripts"
    if scripts_src.is_dir():
        shutil.copytree(
            scripts_src,
            repo / "scripts",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    for rel, content in SEED_FILES.items():
        _write(ctx, rel, content)
    _git(ctx, "add", "-A")
    _git(ctx, "commit", "-q", "-m", "initial")
    # 任務檔還不存在的 commit
    ctx["pre_task_commit"] = _git(ctx, "rev-parse", "HEAD")

    _render_task(ctx)


@given(parsers.parse('任務檔允許修改的路徑是 "{first}" 與 "{second}"'))
def allowed_paths(ctx: dict, first: str, second: str) -> None:
    ctx["task"]["allowed"] = [first, second]
    _render_task(ctx)


@given("以上內容已經 commit，這個 commit 是 base commit")
def commit_as_base(ctx: dict) -> None:
    _git(ctx, "add", "-A")
    _git(ctx, "commit", "-q", "-m", f"{ctx['task_id']}: task")
    ctx["base"] = _git(ctx, "rev-parse", "HEAD")
    status = _git(ctx, "status", "--porcelain")
    assert status == "", f"base commit 之後工作目錄應該是乾淨的：\n{status}"


@given("base commit 的雜湊值已經填進任務檔，尚未 commit")
def fill_base_hash(ctx: dict) -> None:
    assert ctx["base"], "base commit 尚未建立"
    _set_base(ctx, ctx["base"])


# ---------------------------------------------------------------- 變動


def _modify_tracked(ctx: dict, rel: str) -> None:
    path: Path = ctx["repo"] / rel
    path.write_text(path.read_text(encoding="utf-8") + "# modified\n", encoding="utf-8")


def _add_new(ctx: dict, rel: str) -> None:
    assert not (ctx["repo"] / rel).exists(), f"{rel} 已經存在"
    _write(ctx, rel, "new file\n")


@given(parsers.parse('修改了 "{rel}"，尚未 commit'))
def modify_uncommitted(ctx: dict, rel: str) -> None:
    assert _is_tracked(ctx, rel), f"{rel} 應該是 base commit 中已追蹤的檔案"
    _modify_tracked(ctx, rel)


@given(parsers.parse('新增了 "{rel}"，尚未 commit'))
def add_untracked(ctx: dict, rel: str) -> None:
    _add_new(ctx, rel)


@given(parsers.parse('新增了 "{rel}"'))
def add_file(ctx: dict, rel: str) -> None:
    _add_new(ctx, rel)


@given(parsers.parse('修改了已追蹤的檔案，尚未 commit "{rel}"'))
def variant_modify_tracked(ctx: dict, rel: str) -> None:
    _ensure_tracked_at_base(ctx, rel)
    _modify_tracked(ctx, rel)


@given(parsers.parse('新增了尚未追蹤的檔案 "{rel}"'))
def variant_add_untracked(ctx: dict, rel: str) -> None:
    assert not _is_tracked(ctx, rel), f"{rel} 已被追蹤"
    _add_new(ctx, rel)


@given(parsers.parse('修改後已經 commit "{rel}"'))
def variant_modify_committed(ctx: dict, rel: str) -> None:
    _ensure_tracked_at_base(ctx, rel)
    _modify_tracked(ctx, rel)
    _git(ctx, "add", "--", rel)
    _git(ctx, "commit", "-q", "-m", f"modify {rel}", "--", rel)


@given(parsers.parse('刪除了已追蹤的檔案 "{rel}"'))
def variant_delete_tracked(ctx: dict, rel: str) -> None:
    _ensure_tracked_at_base(ctx, rel)
    (ctx["repo"] / rel).unlink()


@given(parsers.parse('.gitignore 忽略 "{pattern}"'))
def gitignore_has(ctx: dict, pattern: str) -> None:
    # .gitignore 必須在 base commit 中（否則 .gitignore 本身就是一個變動），已在 Background 放入。
    lines = (ctx["repo"] / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert pattern in lines, f".gitignore 沒有 {pattern}"
    assert _is_tracked(ctx, ".gitignore")


# ---------------------------------------------------------------- 任務檔本身的變動


@given(
    parsers.parse(
        '任務檔的狀態欄改成 "{status}"、重工次數欄改成 "{rework}"，'
        "並在紀錄段落加了一行，尚未 commit"
    )
)
def task_maintained_parts_changed(ctx: dict, status: str, rework: str) -> None:
    task = ctx["task"]
    task["fields"]["狀態"] = status
    task["fields"]["重工次數"] = rework
    task["log"].append(("2026-11-13", status, "派 implementer"))
    _render_task(ctx)


@given(parsers.parse('任務檔的允許路徑在 base commit 之後加上了 "{rel}"，尚未 commit'))
def task_allowed_path_added(ctx: dict, rel: str) -> None:
    assert rel not in ctx["task"]["allowed"]
    ctx["task"]["allowed"].append(rel)
    _render_task(ctx)


@given("任務檔的「公開介面」段落多了一行，尚未 commit")
def task_interface_line_added(ctx: dict) -> None:
    ctx["task"]["interface"].append("`detect_all(paths)`：一次偵測多個檔案")
    _render_task(ctx)


@given("任務檔的「完成條件」段落刪掉一行，尚未 commit")
def task_done_line_removed(ctx: dict) -> None:
    done = ctx["task"]["done"]
    assert len(done) >= 2, "完成條件至少要有兩行，刪掉一行後段落才不會變空"
    done.pop()
    _render_task(ctx)


@given("任務檔開頭欄位表的 feature 欄改成其他檔案，尚未 commit")
def task_feature_field_changed(ctx: dict) -> None:
    fields = ctx["task"]["fields"]
    assert fields["feature"] != "features/probe/other.feature"
    fields["feature"] = "features/probe/other.feature"
    _render_task(ctx)


# ---------------------------------------------------------------- 任務檔有問題


@given("刪除了任務檔")
def delete_task_file(ctx: dict) -> None:
    (ctx["repo"] / ctx["task_path"]).unlink()


@given("任務檔的 base commit 欄位是空的")
def empty_base(ctx: dict) -> None:
    _set_base(ctx, "")


@given("任務檔的 base commit 是不存在的雜湊值")
def missing_base(ctx: dict) -> None:
    result = _git_result(ctx, "cat-file", "-e", f"{MISSING_HASH}^{{commit}}")
    assert result.returncode != 0, f"{MISSING_HASH} 意外存在於暫存 repo"
    _set_base(ctx, MISSING_HASH)


@given("任務檔的 base commit 指向任務檔還不存在的 commit")
def base_without_task(ctx: dict) -> None:
    commit = ctx["pre_task_commit"]
    _git(ctx, "cat-file", "-e", f"{commit}^{{commit}}")
    shown = _git_result(ctx, "show", f"{commit}:{ctx['task_path']}")
    assert shown.returncode != 0, f"{commit} 中不應該有任務檔"
    _set_base(ctx, commit)


# ---------------------------------------------------------------- When


@when(parsers.parse('在 repo 根目錄執行 "scope_check.py {task_id}"'))
def run_scope_check(ctx: dict, request: pytest.FixtureRequest, task_id: str) -> None:
    repo: Path = ctx["repo"]
    bs.require_file(repo, "scripts/scope_check.py")
    env_repo: Path = request.getfixturevalue("synced_repo")
    ctx["result"] = bs.run(
        [
            bs.uv_exe(),
            "run",
            "--project",
            str(env_repo),
            "python",
            "scripts/scope_check.py",
            task_id,
        ],
        cwd=repo,
        env_extra=ctx["git_env"],
    )


# ---------------------------------------------------------------- Then


def _lines(ctx: dict) -> list[str]:
    result: bs.Result = ctx["result"]
    return [line.replace("\\", "/") for line in result.output.splitlines()]


@then(parsers.parse("exit code 是 {code:d}"))
def exit_code_is(ctx: dict, code: int) -> None:
    result: bs.Result = ctx["result"]
    assert result.returncode == code, result.describe()


@then(parsers.parse('輸出包含 "{text}"'))
def output_contains(ctx: dict, text: str) -> None:
    result: bs.Result = ctx["result"]
    assert text in result.output, result.describe()


@then(parsers.parse('超出範圍的清單包含 "{rel}"'))
def out_of_scope_lists(ctx: dict, rel: str) -> None:
    assert any(rel in line for line in _lines(ctx)), (
        f"輸出沒有列出 {rel}\n" + ctx["result"].describe()
    )


@then(parsers.parse('"{rel}" 在輸出中被標為 "{label}"'))
def marked_as(ctx: dict, rel: str, label: str) -> None:
    assert any(rel in line and label in line for line in _lines(ctx)), (
        f"輸出中沒有同一行同時出現 {rel} 與 {label}\n" + ctx["result"].describe()
    )


@then(parsers.parse("輸出說明 {reason}"))
def output_explains(ctx: dict, reason: str) -> None:
    result: bs.Result = ctx["result"]
    assert reason in result.output, f"輸出沒有說明「{reason}」\n" + result.describe()
