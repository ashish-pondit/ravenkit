"""Tests for the pure dataset helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from ravenkit.dataset import (
    build_tree,
    find_duplicates,
    human_size,
    iter_files,
    normalize_extensions,
    parse_size,
    scan_dataset,
)


@pytest.fixture()
def sample_dataset(tmp_path: Path) -> Path:
    (tmp_path / "cat").mkdir()
    (tmp_path / "cat" / "nested").mkdir()
    (tmp_path / "dog").mkdir()
    (tmp_path / "cat" / "a.jpg").write_bytes(b"a" * 100)
    (tmp_path / "cat" / "nested" / "b.png").write_bytes(b"b" * 200)
    (tmp_path / "dog" / "c.txt").write_bytes(b"c" * 50)
    # duplicate of a.jpg
    (tmp_path / "dog" / "copy.jpg").write_bytes(b"a" * 100)
    return tmp_path


def test_normalize_extensions():
    assert normalize_extensions(None) is None
    assert normalize_extensions([]) is None
    assert normalize_extensions(["JPG", ".png"]) == frozenset({".jpg", ".png"})


def test_iter_files_filters_by_extension(sample_dataset: Path):
    assert len(list(iter_files(sample_dataset))) == 4
    images = list(iter_files(sample_dataset, extensions=["jpg", "png"]))
    assert {path.name for path in images} == {"a.jpg", "b.png", "copy.jpg"}


def test_scan_dataset_counts_and_sizes(sample_dataset: Path):
    data = scan_dataset(sample_dataset)

    assert data.total_files == 4
    assert data.total_dirs == 3
    assert data.total_size == 450
    assert data.image_files == 3
    assert data.image_size == 400
    assert data.non_image_files == 1
    assert data.by_extension[".jpg"] == 2
    assert data.largest[0].size == 200
    assert data.average_size == pytest.approx(112.5)


def test_scan_dataset_rejects_missing_path(tmp_path: Path):
    with pytest.raises(NotADirectoryError):
        scan_dataset(tmp_path / "nope")


def test_scan_dataset_respects_largest(sample_dataset: Path):
    data = scan_dataset(sample_dataset, largest=2)
    assert len(data.largest) == 2
    assert [info.size for info in data.largest] == [200, 100]


def test_build_tree_totals(sample_dataset: Path):
    root = build_tree(sample_dataset, max_depth=1)

    assert root.files == 4
    assert root.size == 450
    children = {child.name: child for child in root.children}
    assert children["cat"].files == 2
    assert children["cat"].size == 300
    assert children["dog"].files == 2
    # "nested" sits at max_depth so it is counted but not expanded.
    assert children["cat"].children[0].truncated is True


def test_build_tree_filters_extensions(sample_dataset: Path):
    root = build_tree(sample_dataset, extensions=["jpg"])
    assert root.files == 2
    assert root.size == 200


def test_find_duplicates(sample_dataset: Path):
    groups = find_duplicates(sample_dataset)

    assert len(groups) == 1
    paths = next(iter(groups.values()))
    assert [path.name for path in paths] == ["a.jpg", "copy.jpg"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [("2048", 2048), ("1kb", 1024), ("1.5 MB", 1572864), ("2g", 2 * 1024**3)],
)
def test_parse_size(text: str, expected: int):
    assert parse_size(text) == expected


def test_parse_size_rejects_garbage():
    with pytest.raises(ValueError):
        parse_size("banana")


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, "0 B"), (512, "512 B"), (1024, "1.0 KB"), (1536, "1.5 KB"), (1024**2, "1.0 MB")],
)
def test_human_size(value: int, expected: str):
    assert human_size(value) == expected
