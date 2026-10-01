"""Tests for the optional-dependency helpers."""

from __future__ import annotations

from ravenkit.deps import Requirement, missing, render_missing

# A module that cannot possibly be installed, used to simulate an absence.
ABSENT = "definitely_not_a_real_module_xyz"

IMAGE = Requirement(ABSENT, "Pillow")


def test_missing_ignores_importable_modules():
    assert missing("images", {"images": (Requirement("sys", "sys"),)}) == []


def test_missing_reports_unimportable_modules():
    assert missing("images", {"images": (IMAGE,)}) == [IMAGE]


def test_missing_keeps_declaration_order():
    other = Requirement("definitely_not_a_real_module_abc", "numpy")
    assert missing("images", {"images": (IMAGE, other)}) == [IMAGE, other]


def test_unknown_extra_reports_nothing():
    assert missing("nope", {}) == []


def test_missing_reads_the_module_registry_by_default():
    # The real registry is empty until the first optional dependency lands, so
    # every extra reports nothing missing.
    assert missing("images") == []


def test_render_missing_names_the_command_and_packages():
    text = render_missing("images", [IMAGE], "raven validate")
    assert "raven validate" in text
    assert "Pillow" in text


def test_render_missing_shows_both_install_forms():
    text = render_missing("images", [IMAGE], "raven validate")
    assert 'pip install -e ".[images]"' in text
    assert 'pip install "ravenkit[images]"' in text


def test_render_missing_lists_every_package():
    text = render_missing(
        "stats",
        [Requirement(ABSENT, "numpy"), Requirement(ABSENT, "scipy")],
        "raven stats",
    )
    assert "- numpy" in text
    assert "- scipy" in text
