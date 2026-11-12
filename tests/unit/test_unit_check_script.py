from __future__ import annotations

import sys
from pathlib import Path

import pytest
from script_loader import REPO_ROOT, load_script

check = load_script("scripts/check.py", "check_under_test")


def write_config(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def test_default_config_lists_the_four_checks_in_order() -> None:
    steps = check.load_steps(REPO_ROOT / "scripts" / "check_steps.toml")
    assert [step.name for step in steps] == ["lint", "boundaries", "unit", "bdd"]


def test_load_steps_reads_name_and_command(tmp_path: Path) -> None:
    config = write_config(tmp_path / "c.toml", '[[step]]\nname = "alpha"\ncommand = ["python", "-c", "print(1)"]\n')
    steps = check.load_steps(config)
    assert [(s.name, s.command) for s in steps] == [("alpha", ["python", "-c", "print(1)"])]


@pytest.mark.parametrize(
    "body",
    [
        "",
        '[[step]]\nname = "a"\n',
        '[[step]]\ncommand = ["x"]\n',
        '[[step]]\nname = "a"\ncommand = []\n',
        '[[step]]\nname = "a"\ncommand = ["x"]\n[[step]]\nname = "a"\ncommand = ["y"]\n',
        "not toml [",
    ],
)
def test_load_steps_rejects_bad_config(tmp_path: Path, body: str) -> None:
    with pytest.raises(check.ConfigError):
        check.load_steps(write_config(tmp_path / "bad.toml", body))


def test_python_is_resolved_to_the_current_interpreter() -> None:
    assert check.resolve_command(["python", "-V"]) == [sys.executable, "-V"]


def test_is_pytest_recognizes_module_and_executable_forms() -> None:
    assert check.is_pytest(["python", "-m", "pytest", "tests"])
    assert check.is_pytest(["pytest.exe", "tests"])
    assert not check.is_pytest(["python", "-m", "ruff", "check"])


def test_pytest_exit_code_5_counts_as_passed_without_tests() -> None:
    step = check.Step(name="empty", command=["python", "-c", "import sys; sys.exit(5)", "pytest"])
    outcome = check.run_step(step)
    assert (outcome.exit_code, outcome.passed, outcome.note) == (5, True, "無測試")


def test_other_exit_codes_fail() -> None:
    step = check.Step(name="boom", command=["python", "-c", "import sys; sys.exit(3)"])
    outcome = check.run_step(step)
    assert (outcome.exit_code, outcome.passed) == (3, False)


def test_missing_executable_is_reported_as_failure() -> None:
    outcome = check.run_step(check.Step(name="ghost", command=["no-such-tool-xyz"]))
    assert outcome.passed is False
    assert outcome.exit_code == check.NOT_FOUND_CODE


def test_child_output_is_decoded_as_utf8() -> None:
    code = "import sys; sys.stdout.buffer.write('中文輸出\\n'.encode('utf-8'))"
    outcome = check.run_step(check.Step(name="utf8", command=["python", "-c", code]))
    assert "中文輸出" in outcome.output
