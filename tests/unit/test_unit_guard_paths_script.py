from __future__ import annotations

import json
from pathlib import Path

import pytest
from script_loader import load_script

guard = load_script("scripts/hooks/guard_paths.py", "guard_paths_under_test")
ROOT = Path(guard.__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "raw",
    [
        "features/tooling/check.feature",
        "tests/bdd/test_check.py",
        "docs/tasks/T-000-dev-environment.md",
        "src/../features/tooling/new.feature",
        "./features/a.feature",
        "features\\a.feature",
        "FEATURES/a.feature",
        "tests/bdd",
    ],
)
def test_protected_relative_paths_are_blocked(raw: str) -> None:
    assert guard.protected_prefix(raw, ROOT) is not None


def test_windows_absolute_path_with_backslashes_is_blocked() -> None:
    raw = str(ROOT / "features" / "a.feature").replace("/", "\\")
    assert guard.protected_prefix(raw, ROOT) == "features"


@pytest.mark.parametrize(
    "raw",
    [
        "src/ragdoc/probe/detect.py",
        "tests/unit/probe/test_detect.py",
        "docs/lessons/L-0002-sample.md",
        "docs/reports/T-000-impl.md",
        "tests/bdd_extra/x.py",
        "../outside/features/x.feature",
    ],
)
def test_other_paths_are_allowed(raw: str) -> None:
    assert guard.protected_prefix(raw, ROOT) is None


def test_parse_file_path_reads_tool_input() -> None:
    payload = json.dumps({"tool_input": {"file_path": "a/b.py"}}).encode("utf-8")
    assert guard.parse_file_path(payload) == "a/b.py"


@pytest.mark.parametrize(
    "payload",
    [b"{", b"[]", b"{}", b'{"tool_input": {}}', b'{"tool_input": {"file_path": 3}}', b"\xff\xfe"],
)
def test_parse_file_path_rejects_unusable_input(payload: bytes) -> None:
    with pytest.raises(ValueError):
        guard.parse_file_path(payload)


def test_parse_file_path_accepts_utf8_bom() -> None:
    payload = b"\xef\xbb\xbf" + json.dumps({"tool_input": {"file_path": "a.py"}}).encode("utf-8")
    assert guard.parse_file_path(payload) == "a.py"
