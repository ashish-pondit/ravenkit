"""Pure dataset inspection logic.

This module never prints anything and never imports the CLI, which keeps it
easy to test and reuse from other scripts.

>>> from pathlib import Path
>>> data = scan_dataset(Path("."))
>>> data.total_files >= 0
True
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

IMAGE_EXTENSIONS = frozenset(
    {
        ".avif",
        ".bmp",
        ".gif",
        ".heic",
        ".jpeg",
        ".jpg",
        ".png",
        ".svg",
        ".tif",
        ".tiff",
        ".webp",
    }
)

RAW_EXTENSIONS = frozenset({".arw", ".cr2", ".dng", ".nef", ".orf", ".raf", ".rw2"})

Extensions = Iterable[str] | None


def normalize_extensions(extensions: Extensions) -> frozenset | None:
    """Normalize ``["jpg", ".PNG"]`` into ``{".jpg", ".png"}``.

    Returns ``None`` when no filter was requested (meaning "everything").
    """
    if not extensions:
        return None
    normalized = set()
    for ext in extensions:
        ext = ext.strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = "." + ext
        normalized.add(ext)
    return frozenset(normalized) or None


def human_size(num_bytes: float) -> str:
    """Format a byte count for humans, e.g. ``1536`` -> ``"1.5 KB"``."""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{value:.0f} B"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"  # pragma: no cover - unreachable guard


_SIZE_UNITS = {
    "b": 1,
    "k": 1024,
    "kb": 1024,
    "m": 1024**2,
    "mb": 1024**2,
    "g": 1024**3,
    "gb": 1024**3,
    "t": 1024**4,
    "tb": 1024**4,
}


def parse_size(text: str) -> int:
    """Parse ``"10kb"`` / ``"1.5 MB"`` / ``"2048"`` into a byte count."""
    cleaned = text.strip().lower().replace(" ", "")
    if not cleaned:
        raise ValueError("empty size")
    digits = ""
    for char in cleaned:
        if char.isdigit() or char == ".":
            digits += char
        else:
            break
    suffix = cleaned[len(digits) :]
    if not digits:
        raise ValueError(f"invalid size: {text!r}")
    if not suffix:
        return int(float(digits))
    if suffix not in _SIZE_UNITS:
        raise ValueError(f"unknown size unit: {suffix!r}")
    return int(float(digits) * _SIZE_UNITS[suffix])


def ext_label(path: Path) -> str:
    """Return the lowercase extension of *path*, or ``"<none>"``."""
    return path.suffix.lower() or "<none>"


def iter_files(
    root: Path,
    *,
    extensions: Extensions = None,
    follow_symlinks: bool = False,
) -> Iterable[Path]:
    """Yield every regular file below *root* in a stable (sorted) order."""
    wanted = normalize_extensions(extensions)
    for path in sorted(root.rglob("*")):
        if path.is_symlink() and not follow_symlinks:
            continue
        if not path.is_file():
            continue
        if wanted is not None and ext_label(path) not in wanted:
            continue
        yield path


@dataclass(frozen=True)
class FileInfo:
    """A single file with its cached size."""

    path: Path
    size: int

    @property
    def ext(self) -> str:
        return ext_label(self.path)


@dataclass
class DatasetSummary:
    """Aggregated facts about a folder tree."""

    root: Path
    total_files: int = 0
    total_dirs: int = 0
    total_size: int = 0
    image_files: int = 0
    image_size: int = 0
    by_extension: Counter = field(default_factory=Counter)
    size_by_extension: Counter = field(default_factory=Counter)
    largest: list[FileInfo] = field(default_factory=list)

    @property
    def non_image_files(self) -> int:
        return self.total_files - self.image_files

    @property
    def average_size(self) -> float:
        return self.total_size / self.total_files if self.total_files else 0.0


def scan_dataset(
    root: Path,
    *,
    largest: int = 10,
    extensions: Extensions = None,
    follow_symlinks: bool = False,
) -> DatasetSummary:
    """Walk *root* once and collect counts, sizes and the biggest files."""
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")

    summary = DatasetSummary(root=root)
    biggest: list[FileInfo] = []

    for path in root.rglob("*"):
        if path.is_symlink() and not follow_symlinks:
            continue
        if path.is_dir():
            summary.total_dirs += 1

    for path in iter_files(root, extensions=extensions, follow_symlinks=follow_symlinks):
        try:
            size = path.stat().st_size
        except OSError:
            continue
        ext = ext_label(path)
        summary.total_files += 1
        summary.total_size += size
        summary.by_extension[ext] += 1
        summary.size_by_extension[ext] += size
        if ext in IMAGE_EXTENSIONS:
            summary.image_files += 1
            summary.image_size += size
        biggest.append(FileInfo(path=path, size=size))

    biggest.sort(key=lambda info: (-info.size, str(info.path)))
    summary.largest = biggest[:largest] if largest > 0 else []
    return summary


@dataclass
class DirNode:
    """A folder in the tree view, with recursive totals."""

    path: Path
    files: int = 0
    size: int = 0
    truncated: bool = False
    children: list[DirNode] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.path.name or str(self.path)


def _sorted_entries(path: Path) -> list[Path]:
    try:
        entries = list(path.iterdir())
    except OSError:
        return []
    return sorted(entries, key=lambda entry: (entry.is_file(), entry.name.lower()))


def _count_subtree(path: Path, wanted: frozenset | None, follow_symlinks: bool) -> DirNode:
    """Count everything below *path* without materializing child nodes."""
    node = DirNode(path=path, truncated=True)
    for child in _sorted_entries(path):
        if child.is_symlink() and not follow_symlinks:
            continue
        if child.is_dir():
            nested = _count_subtree(child, wanted, follow_symlinks)
            node.files += nested.files
            node.size += nested.size
        elif child.is_file():
            if wanted is not None and ext_label(child) not in wanted:
                continue
            try:
                node.size += child.stat().st_size
            except OSError:
                continue
            node.files += 1
    return node


def build_tree(
    root: Path,
    *,
    max_depth: int = 3,
    extensions: Extensions = None,
    follow_symlinks: bool = False,
) -> DirNode:
    """Build a folder tree, stopping at *max_depth* but still counting deeper files."""
    wanted = normalize_extensions(extensions)
    root = Path(root)

    def build(path: Path, depth: int) -> DirNode:
        node = DirNode(path=path)
        for entry in _sorted_entries(path):
            if entry.is_symlink() and not follow_symlinks:
                continue
            if entry.is_dir():
                if depth < max_depth:
                    child = build(entry, depth + 1)
                else:
                    child = _count_subtree(entry, wanted, follow_symlinks)
                node.children.append(child)
                node.files += child.files
                node.size += child.size
            elif entry.is_file():
                if wanted is not None and ext_label(entry) not in wanted:
                    continue
                try:
                    node.size += entry.stat().st_size
                except OSError:
                    continue
                node.files += 1
        return node

    return build(root, 0)


def _hash_file(path: Path, chunk_size: int = 1 << 20) -> str | None:
    digest = hashlib.blake2b(digest_size=16)
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(chunk_size):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def find_duplicates(
    root: Path,
    *,
    extensions: Extensions = None,
    follow_symlinks: bool = False,
) -> dict[str, list[Path]]:
    """Return ``{content_hash: [paths]}`` for files that share identical content.

    Files are grouped by size first so only candidates are ever hashed.
    """
    by_size: dict[int, list[Path]] = defaultdict(list)
    for path in iter_files(root, extensions=extensions, follow_symlinks=follow_symlinks):
        try:
            by_size[path.stat().st_size].append(path)
        except OSError:
            continue

    groups: dict[str, list[Path]] = defaultdict(list)
    for size, paths in by_size.items():
        if size == 0 or len(paths) < 2:
            continue
        for path in paths:
            digest = _hash_file(path)
            if digest is not None:
                groups[digest].append(path)

    return {digest: sorted(paths) for digest, paths in groups.items() if len(paths) > 1}
