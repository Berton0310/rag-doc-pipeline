"""features/tooling/check.feature 的 step definitions。

設定檔中每個項目執行一個暫存的 Python 小腳本：除了 feature 指定的輸出與 exit code，
還會把自己的名稱附加到 trace 檔，用來觀察「哪些項目被執行、順序為何」。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import bdd_support as bs
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios(str(bs.FEATURES_DIR / "check.feature"))

_PRINT_TEXT = re.compile(r'^印出 "(?P<text>.+)"，exit code (?P<code>\d+)$')
_PRINT_LINES = re.compile(r"^印出 (?P<n>\d+) 行文字，exit code (?P<code>\d+)$")


def _beta_like_lines(name: str, n: int) -> list[str]:
    return [f"{name} output line {i:03d} of {n}" for i in range(1, n + 1)]


def _write_step_script(
    dir_: Path, name: str, trace: Path, lines: list[str], code: int
) -> Path:
    script = dir_ / f"{name}_step.py"
    script.write_text(
        "import sys\n"
        f"with open({trace.as_posix()!r}, 'a', encoding='utf-8') as f:\n"
        f"    f.write({name!r} + '\\n')\n"
        f"for line in {lines!r}:\n"
        "    print(line)\n"
        f"sys.exit({code})\n",
        encoding="utf-8",
    )
    return script


def _write_config(path: Path, steps: list[tuple[str, list[str]]]) -> None:
    parts = []
    for name, command in steps:
        # 路徑一律用正斜線，JSON 字串同時是合法的 TOML basic string。
        parts.append(
            "[[step]]\n"
            f"name = {json.dumps(name)}\n"
            f"command = [{', '.join(json.dumps(c) for c in command)}]\n"
        )
    path.write_text("\n".join(parts), encoding="utf-8")


def _trace(ctx: dict) -> list[str]:
    trace: Path = ctx["trace"]
    if not trace.exists():
        return []
    return [line for line in trace.read_text(encoding="utf-8").splitlines() if line]


def _repo(ctx: dict, request: pytest.FixtureRequest) -> Path:
    if "repo" not in ctx:
        ctx["repo"] = request.getfixturevalue("synced_repo")
    return ctx["repo"]


# ---------------------------------------------------------------- Given


@given("一份名為「混合」的檢查設定檔，依序定義三個項目：")
def mixed_config(ctx: dict, work_dir: Path, datatable: list[list[str]]) -> None:
    header, *rows = datatable
    assert header == ["名稱", "行為"], header
    steps_dir = work_dir / "steps"
    steps_dir.mkdir()
    trace = work_dir / "trace.txt"
    items: dict[str, dict] = {}
    for name, behaviour in rows:
        if m := _PRINT_TEXT.match(behaviour):
            lines, code = [m["text"]], int(m["code"])
        elif m := _PRINT_LINES.match(behaviour):
            lines, code = _beta_like_lines(name, int(m["n"])), int(m["code"])
        else:
            raise AssertionError(f"無法解讀行為描述：{behaviour!r}")
        script = _write_step_script(steps_dir, name, trace, lines, code)
        items[name] = {
            "lines": lines,
            "code": code,
            "command": ["python", script.as_posix()],
            "script_name": script.name,
        }
    ctx["items"] = items
    ctx["trace"] = trace
    ctx["configs"] = {}
    mixed = work_dir / "mixed.toml"
    _write_config(mixed, [(n, items[n]["command"]) for n in items])
    ctx["configs"]["混合"] = mixed


@given("一份名為「全通過」的檢查設定檔，定義兩個項目 alpha 與 gamma，行為同上")
def all_pass_config(ctx: dict, work_dir: Path) -> None:
    items = ctx["items"]
    path = work_dir / "all_pass.toml"
    _write_config(path, [(n, items[n]["command"]) for n in ("alpha", "gamma")])
    ctx["configs"]["全通過"] = path


@given("一份檢查設定檔，唯一的項目是對一個空的測試目錄執行 pytest")
def empty_pytest_config(ctx: dict, work_dir: Path) -> None:
    empty = work_dir / "empty_tests"
    empty.mkdir()
    path = work_dir / "empty_pytest.toml"
    # 用 pytest 執行檔（uv run 時在 PATH 上），不依賴 check.py 如何解析 "python"。
    _write_config(path, [("empty-tests", ["pytest", empty.as_posix()])])
    ctx["configs"]["這份"] = path
    ctx["empty_item"] = "empty-tests"


@given("tests/bdd 裡各有一個標記 manual、gpu、network 的測試，以及一個沒有標記的測試")
def marker_probe_tests(ctx: dict, work_dir: Path) -> None:
    # 會修改 tests/bdd，所以用獨立的 repo 副本。
    # 先移除副本中原有的 test_*.py（包含本檔），避免 check.py --only bdd 在副本裡遞迴執行整套 BDD 測試。
    repo = bs.make_synced_copy(work_dir / "repo")
    bdd_dir = repo / "tests" / "bdd"
    for old in bdd_dir.glob("test_*.py"):
        old.unlink()
    probe_dir = work_dir / "probe_trace"
    probe_dir.mkdir()
    body = [
        "from pathlib import Path",
        "import pytest",
        "",
        f"TRACE = Path({probe_dir.as_posix()!r})",
        "",
        "",
        "def _hit(name):",
        "    (TRACE / name).write_text('x', encoding='utf-8')",
        "",
    ]
    for marker in ("manual", "gpu", "network"):
        body += [
            "",
            f"@pytest.mark.{marker}",
            f"def test_probe_{marker}():",
            f"    _hit({marker!r})",
            "",
        ]
    body += ["", "def test_probe_plain():", "    _hit('plain')", ""]
    (bdd_dir / "test_marker_probe.py").write_text("\n".join(body), encoding="utf-8")
    ctx["repo"] = repo
    ctx["probe_dir"] = probe_dir


# ---------------------------------------------------------------- When


@when(parsers.re(r"^用「(?P<cfg>[^」]+)」設定檔執行 check\.py(?P<extra>.*)$"))
def run_with_named_config(
    ctx: dict, request: pytest.FixtureRequest, cfg: str, extra: str
) -> None:
    repo = _repo(ctx, request)
    config: Path = ctx["configs"][cfg]
    ctx["result"] = bs.run_check(repo, ["--config", config.as_posix(), *extra.split()])


@when("用這份設定檔執行 check.py")
def run_with_this_config(ctx: dict, request: pytest.FixtureRequest) -> None:
    repo = _repo(ctx, request)
    config: Path = ctx["configs"]["這份"]
    ctx["result"] = bs.run_check(repo, ["--config", config.as_posix()])


@when(parsers.re(r"^不指定設定檔，執行 check\.py(?P<extra>.*)$"))
def run_with_default_config(
    ctx: dict, request: pytest.FixtureRequest, extra: str
) -> None:
    repo = _repo(ctx, request)
    ctx["default_config"] = True
    ctx["result"] = bs.run_check(repo, extra.split())


# ---------------------------------------------------------------- Then


@then("alpha、beta、gamma 都有執行，順序是 alpha、beta、gamma")
def all_ran_in_order(ctx: dict) -> None:
    assert _trace(ctx) == ["alpha", "beta", "gamma"], (
        f"實際執行紀錄：{_trace(ctx)}\n" + ctx["result"].describe()
    )


@then(parsers.parse("整體 exit code 是 {code:d}"))
def overall_exit_code(ctx: dict, code: int) -> None:
    result: bs.Result = ctx["result"]
    assert result.returncode == code, result.describe()


@then('標準輸出有一張摘要表，每列包含項目名稱、exit code、以及 "通過" 或 "失敗"')
def summary_table(ctx: dict) -> None:
    result: bs.Result = ctx["result"]
    for name, item in ctx["items"].items():
        row = bs.summary_row(result.stdout, name)
        assert row is not None, f"摘要表沒有 {name} 這一列\n" + result.describe()
        assert bs.has_number_token(row, item["code"]), (
            f"{name} 那列沒有 exit code {item['code']}：{row!r}"
        )


@then(parsers.parse('{name} 那列是 exit code {code:d} 與 "{verdict}"'))
def summary_row_is(ctx: dict, name: str, code: int, verdict: str) -> None:
    result: bs.Result = ctx["result"]
    row = bs.summary_row(result.stdout, name)
    assert row is not None, f"摘要表沒有 {name} 這一列\n" + result.describe()
    other = {"通過": "失敗", "失敗": "通過"}[verdict]
    assert verdict in row and other not in row, f"{name} 那列不是 {verdict!r}：{row!r}"
    assert bs.has_number_token(row, code), f"{name} 那列沒有 exit code {code}：{row!r}"


@then('標準輸出的最後一行是記錄檔路徑，位於 "outputs/check/" 底下')
def last_line_is_log_path(ctx: dict) -> None:
    result: bs.Result = ctx["result"]
    repo: Path = ctx["repo"]
    path = bs.log_path_from_stdout(repo, result.stdout)
    expected_dir = (repo / "outputs" / "check").resolve()
    assert path.resolve().parent == expected_dir, (
        f"最後一行 {bs.last_nonempty_line(result.stdout)!r} 不是 outputs/check/ 底下的路徑\n"
        + result.describe()
    )
    ctx["log_path"] = path


@then("這個記錄檔存在")
def log_exists(ctx: dict) -> None:
    path: Path = ctx["log_path"]
    assert path.is_file(), f"記錄檔不存在：{path}"


def _log_text(ctx: dict) -> str:
    return ctx["log_path"].read_text(encoding="utf-8", errors="replace")


@then("記錄檔包含 beta 印出的全部 120 行")
def log_has_all_beta_lines(ctx: dict) -> None:
    text = _log_text(ctx)
    lines = ctx["items"]["beta"]["lines"]
    assert len(lines) == 120
    missing = [line for line in lines if line not in text]
    assert not missing, f"記錄檔缺少 beta 的 {len(missing)} 行，例如：{missing[:3]}"


@then("記錄檔包含每一項執行的指令與 exit code")
def log_has_commands_and_codes(ctx: dict) -> None:
    text = _log_text(ctx)
    items: dict[str, dict] = ctx["items"]
    starts: list[tuple[int, str]] = []
    for name, item in items.items():
        assert item["script_name"] in text, (
            f"記錄檔沒有 {name} 執行的指令（{item['script_name']}）"
        )
        # 每一項的區段從「名稱或指令第一次出現的位置」開始，到下一項的區段為止。
        cands = [text.find(item["script_name"])]
        m = bs.word_pattern(name).search(text)
        if m:
            cands.append(m.start())
        starts.append((min(c for c in cands if c >= 0), name))
    starts.sort()
    for i, (start, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        segment = text[start:end]
        code = items[name]["code"]
        assert bs.has_number_token(segment, code), (
            f"記錄檔中 {name} 的區段沒有 exit code {code}：\n{segment[:1500]}"
        )


@then("只有 gamma 被執行")
def only_gamma_ran(ctx: dict) -> None:
    assert _trace(ctx) == ["gamma"], (
        f"實際執行紀錄：{_trace(ctx)}\n" + ctx["result"].describe()
    )


@then("輸出列出可用的項目名稱 alpha、beta、gamma")
def lists_available_names(ctx: dict) -> None:
    result: bs.Result = ctx["result"]
    for name in ("alpha", "beta", "gamma"):
        assert bs.word_pattern(name).search(result.output), (
            f"輸出沒有列出 {name}\n" + result.describe()
        )


@then("沒有任何項目被執行")
def nothing_ran(ctx: dict) -> None:
    result: bs.Result = ctx["result"]
    if "trace" in ctx and not ctx.get("default_config"):
        assert _trace(ctx) == [], f"有項目被執行：{_trace(ctx)}\n" + result.describe()
    else:
        # 預設設定的項目無法插入 trace；有執行的話會出現摘要表（通過／失敗）。
        assert "通過" not in result.stdout and "失敗" not in result.stdout, (
            "輸出出現摘要表，表示有項目被執行\n" + result.describe()
        )


@then('摘要表中這一項註明 "無測試"')
def empty_marked_no_tests(ctx: dict) -> None:
    result: bs.Result = ctx["result"]
    row = bs.summary_row(result.stdout, ctx["empty_item"])
    assert row is not None, "摘要表沒有這一項\n" + result.describe()
    assert "無測試" in row, f"這一列沒有註明「無測試」：{row!r}"


@then('印出的項目名稱依序是 "lint"、"boundaries"、"unit"、"bdd"')
def listed_names(ctx: dict) -> None:
    result: bs.Result = ctx["result"]
    # 公開介面：「--list：每行印一個項目名稱」，所以標準輸出只能有這四行。
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert lines == ["lint", "boundaries", "unit", "bdd"], result.describe()


@then("只有沒有標記的那個測試被執行")
def only_unmarked_ran(ctx: dict) -> None:
    probe_dir: Path = ctx["probe_dir"]
    ran = sorted(p.name for p in probe_dir.iterdir())
    assert ran == ["plain"], f"實際被執行的測試：{ran}\n" + ctx["result"].describe()
