import subprocess
import sys

import pytest

from wanderlens.cli.main import build_parser, main


def test_no_command_prints_help_and_returns_zero(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "usage" in out


def test_parser_has_all_commands():
    parser = build_parser()
    actions = [a for a in parser._actions if getattr(a, "choices", None)]
    commands = set(actions[0].choices)
    assert {"ingest", "profile", "recommend", "eval"} <= commands


def test_module_entrypoint_help():
    result = subprocess.run(
        [sys.executable, "-m", "wanderlens", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout


@pytest.mark.parametrize(
    "argv",
    [
        ["ingest", "--help"],
        ["profile", "--help"],
        ["profile", "show", "--help"],
        ["recommend", "--help"],
        ["eval", "--help"],
    ],
)
def test_subcommand_help(argv):
    result = subprocess.run(
        [sys.executable, "-m", "wanderlens", *argv],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout
