"""Smoke tests for the ``raven`` command line surface."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ravenkit import __version__
from ravenkit.cli import app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"raven {__version__}" in result.stdout


def test_help_lists_every_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("summary", "tree", "files", "duplicates"):
        assert command in result.stdout


def test_summary_on_folder(tmp_path: Path) -> None:
    (tmp_path / "cat").mkdir()
    (tmp_path / "cat" / "a.jpg").write_bytes(b"a" * 100)
    result = runner.invoke(app, ["summary", str(tmp_path)])
    assert result.exit_code == 0
    assert "Dataset" in result.stdout
