"""Smoke tests for the ``raven`` command line surface."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from ravenkit import __version__, cli, deps
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


def test_missing_path_is_an_invalid_value(tmp_path: Path) -> None:
    result = runner.invoke(app, ["summary", str(tmp_path / "nope")])
    assert result.exit_code == 2


def test_unknown_sort_is_a_runtime_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["files", str(tmp_path), "--sort", "bogus"])
    assert result.exit_code == 1


def test_bad_min_size_is_a_runtime_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["files", str(tmp_path), "--min-size", "5xb"])
    assert result.exit_code == 1


def test_require_is_silent_when_nothing_is_registered() -> None:
    # The real registry is empty until the first optional dependency lands.
    cli._require("images", "raven validate")


def test_require_fails_with_an_install_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    absent = deps.Requirement("definitely_not_a_real_module_xyz", "Pillow")
    monkeypatch.setitem(deps.EXTRA_MODULES, "images", (absent,))
    with pytest.raises(typer.Exit) as excinfo:
        cli._require("images", "raven validate")
    assert excinfo.value.exit_code == 1


def test_fail_keeps_brackets_out_of_richs_markup(capsys: pytest.CaptureFixture[str]) -> None:
    # `ravenkit[images]` must survive: rich would otherwise treat [images] as a
    # style tag and silently drop it, printing a wrong install command.
    with pytest.raises(typer.Exit):
        cli._fail('install with pip install "ravenkit[images]"')
    assert "ravenkit[images]" in capsys.readouterr().err
