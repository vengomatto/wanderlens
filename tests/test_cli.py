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
    assert {"ingest", "profile", "recommend", "eval", "serve", "guide"} <= commands


def test_guide_flags_parse():
    parser = build_parser()
    args = parser.parse_args(["guide", "--count", "3", "--refresh", "--no-llm"])
    assert args.count == 3
    assert args.refresh is True
    assert args.no_llm is True


def test_recommend_no_media_flag_parses():
    parser = build_parser()
    args = parser.parse_args(["recommend", "--no-media"])
    assert args.no_media is True


def test_recommend_media_defaults_on():
    parser = build_parser()
    args = parser.parse_args(["recommend"])
    assert args.no_media is False


def test_recommend_alpha_default_and_override():
    parser = build_parser()
    assert parser.parse_args(["recommend"]).alpha is None
    assert parser.parse_args(["recommend", "--alpha", "0.7"]).alpha == 0.7


def test_eval_synthetic_flag_parses():
    parser = build_parser()
    args = parser.parse_args(["eval", "--synthetic", "--k", "5"])
    assert args.synthetic is True
    assert args.k == 5


def test_feedback_flags_parse():
    parser = build_parser()
    args = parser.parse_args(["feedback", "--destination", "wv:Kotor", "--action", "like"])
    assert args.destination == "wv:Kotor"
    assert args.action == "like"


def test_recommend_refresh_media_flag_parses():
    parser = build_parser()
    assert parser.parse_args(["recommend", "--refresh-media"]).refresh_media is True


def test_ingest_estimate_flag_parses():
    parser = build_parser()
    args = parser.parse_args(["ingest", "--tag", "--estimate"])
    assert args.estimate is True


def test_ingest_vlm_flag_parses():
    parser = build_parser()
    args = parser.parse_args(["ingest", "--tag", "--vlm"])
    assert args.vlm is True


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
        ["serve", "--help"],
        ["guide", "--help"],
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
