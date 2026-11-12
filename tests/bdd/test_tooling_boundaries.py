"""features/tooling/boundaries.feature 的 step definitions。"""

from __future__ import annotations

from pathlib import Path

import bdd_support as bs
from pytest_bdd import given, parsers, scenarios, then, when

scenarios(str(bs.FEATURES_DIR / "boundaries.feature"))


# ---------------------------------------------------------------- Given


@given('一份已執行過 "uv sync" 的 repo 副本，沒有任何修改')
def unmodified_synced_copy(ctx: dict, synced_repo: Path) -> None:
    ctx["repo"] = synced_repo


@given('一份已執行過 "uv sync" 的 repo 副本')
def own_synced_copy(ctx: dict, work_dir: Path) -> None:
    # 接下來會在 src/ 新增檔案，所以每個情境用自己的副本，不碰共用副本。
    ctx["repo"] = bs.make_synced_copy(work_dir / "repo")


@given(
    parsers.parse(
        '在 "src/ragdoc/{package}/" 新增一個檔案 "{filename}"，內容是 "{content}"'
    )
)
def add_source_file(ctx: dict, package: str, filename: str, content: str) -> None:
    repo: Path = ctx["repo"]
    pkg_dir = repo / "src" / "ragdoc" / Path(package)
    assert pkg_dir.is_dir(), f"尚未實作：套件目錄 src/ragdoc/{package}/ 不存在"
    target = pkg_dir / filename
    assert not target.exists(), f"{target} 已經存在"
    target.write_text(content + "\n", encoding="utf-8")


# ---------------------------------------------------------------- When


@when(parsers.parse('執行 "check.py{args}"'))
def run_check(ctx: dict, args: str) -> None:
    ctx["result"] = bs.run_check(ctx["repo"], args.split())


# ---------------------------------------------------------------- Then


@then(parsers.parse("整體 exit code 是 {code:d}"))
def overall_exit_code(ctx: dict, code: int) -> None:
    result: bs.Result = ctx["result"]
    assert result.returncode == code, result.describe()


@then(parsers.parse('boundaries 這一項的結果是 "{verdict}"'))
def boundaries_verdict(ctx: dict, verdict: str) -> None:
    result: bs.Result = ctx["result"]
    row = bs.summary_row(result.stdout, "boundaries")
    assert row is not None, "摘要表沒有 boundaries 這一列\n" + result.describe()
    other = {"通過": "失敗", "失敗": "通過"}[verdict]
    assert verdict in row and other not in row, (
        f"boundaries 那列不是 {verdict!r}：{row!r}\n" + result.describe()
    )


@then(parsers.parse('記錄檔中 boundaries 的輸出包含 "{text}"'))
def log_contains(ctx: dict, text: str) -> None:
    result: bs.Result = ctx["result"]
    repo: Path = ctx["repo"]
    path = bs.log_path_from_stdout(repo, result.stdout)
    assert path.is_file(), (
        f"標準輸出最後一行不是存在的記錄檔：{bs.last_nonempty_line(result.stdout)!r}\n"
        + result.describe()
    )
    log = path.read_text(encoding="utf-8", errors="replace")
    # 只執行了 boundaries 一項，整份記錄檔就是 boundaries 的輸出。
    assert text in log, f"記錄檔沒有 {text!r}：{path}\n{log[:3000]}"
