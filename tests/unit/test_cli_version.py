from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from ragdoc.cli import main

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_version_flag_prints_program_name_and_pyproject_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--version"])
    assert raised.value.code == 0
    expected = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    assert re.fullmatch(rf"ragdoc {re.escape(expected)}", capsys.readouterr().out.strip())
