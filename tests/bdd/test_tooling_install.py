"""features/tooling/install.feature 的 step definitions。"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import bdd_support as bs
from pytest_bdd import given, parsers, scenarios, then, when

scenarios(str(bs.FEATURES_DIR / "install.feature"))


# ---------------------------------------------------------------- Given


@given("一份剛 clone 下來、沒有虛擬環境的 repo 副本")
def fresh_clone(ctx: dict, work_dir: Path) -> None:
    repo = bs.copy_worktree(work_dir / "repo")
    assert not (repo / ".venv").exists(), "repo 副本不應該有 .venv"
    ctx["repo"] = repo


@given('一份已執行過 "uv sync" 的 repo 副本')
def synced_clone(ctx: dict, synced_repo: Path) -> None:
    ctx["repo"] = synced_repo


@given("一台沒有裝過本專案的 GPU 機器")
def gpu_machine() -> None:
    bs.skip_manual()


# ---------------------------------------------------------------- When


@when(parsers.parse('在 repo 根目錄執行 "{command}"'))
def run_in_repo_root(ctx: dict, command: str) -> None:
    args = command.split()
    assert args[0] == "uv", f"此步驟只支援 uv 指令：{command}"
    ctx["result"] = bs.run([bs.uv_exe(), *args[1:]], cwd=ctx["repo"])


@when(parsers.parse('透過 "uv run python" 執行 import "{module}"'))
def import_module(ctx: dict, module: str) -> None:
    ctx["result"] = bs.run(
        [bs.uv_exe(), "run", "python", "-c", f"import {module}"], cwd=ctx["repo"]
    )


@when("使用者照 README.md 的「安裝」段落逐步操作")
def follow_readme() -> None:
    bs.skip_manual()


# ---------------------------------------------------------------- Then


@then(parsers.parse("指令的 exit code 是 {code:d}"))
def exit_code_is(ctx: dict, code: int) -> None:
    result: bs.Result = ctx["result"]
    assert result.returncode == code, result.describe()


@then(parsers.parse("指令的 exit code 不是 {code:d}"))
def exit_code_is_not(ctx: dict, code: int) -> None:
    result: bs.Result = ctx["result"]
    assert result.returncode != code, result.describe()


@then(
    '執行 "uv run ragdoc --version" 印出的版本號與 pyproject.toml 的 version 欄位相同'
)
def version_matches(ctx: dict) -> None:
    repo: Path = ctx["repo"]
    pyproject = bs.require_file(repo, "pyproject.toml")
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    assert isinstance(version, str) and version, (
        "pyproject.toml 沒有 [project] version 欄位"
    )

    result = bs.run([bs.uv_exe(), "run", "ragdoc", "--version"], cwd=repo)
    assert result.returncode == 0, result.describe()
    # 允許前面帶程式名稱（例如 "ragdoc 0.1.0"），但版本號必須是完整的一個詞。
    pat = re.compile(rf"(?<![\w.]){re.escape(version)}(?![\w.])")
    assert pat.search(result.stdout), (
        f"標準輸出沒有印出 pyproject.toml 的 version {version!r}\n" + result.describe()
    )


@then(parsers.parse('輸出包含 "{text}"'))
def output_contains(ctx: dict, text: str) -> None:
    result: bs.Result = ctx["result"]
    assert text in result.output, result.describe()


@then("人工確認不需要 README 以外的步驟就能完成安裝")
def manual_readme_only() -> None:
    bs.skip_manual()


@then('人工確認 "uv run ragdoc --version" 印出版本號')
def manual_version() -> None:
    bs.skip_manual()
