"""ragdoc.cli：命令列入口。"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from importlib.metadata import version

PROG = "ragdoc"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROG, description="企業文件轉結構化中間格式的管線")
    parser.add_argument(
        "--version",
        action="version",
        version=f"{PROG} {version('ragdoc')}",
        help="印出版本號",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """命令列進入點。目前只支援 --version；其他子命令由後續任務加入。"""
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
