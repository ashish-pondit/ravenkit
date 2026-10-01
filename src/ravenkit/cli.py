"""Command line interface for the ``ravenkit`` toolbox.

Run ``raven --help`` for details.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from . import __version__
from .dataset import (
    IMAGE_EXTENSIONS,
    DatasetSummary,
    DirNode,
    build_tree,
    find_duplicates,
    human_size,
    iter_files,
    normalize_extensions,
    parse_size,
    scan_dataset,
)

console = Console()
error_console = Console(stderr=True)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    help="Dataset-inspection CLIs: files, sizes, formats and folders.",
)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _version_callback(value: bool) -> None:
    if value:
        console.print(f"raven {__version__}")
        raise typer.Exit()


def _resolve_dir(path: Path) -> Path:
    """Expand and validate a user supplied folder argument."""
    resolved = Path(path).expanduser()
    if not resolved.exists():
        raise typer.BadParameter(f"path does not exist: {resolved}")
    if not resolved.is_dir():
        raise typer.BadParameter(f"not a directory: {resolved}")
    return resolved.resolve()


def _extensions_from(exts: str | None, images_only: bool) -> list[str] | None:
    """Turn ``--ext "jpg,png"`` / ``--images-only`` into an extension list."""
    if images_only:
        return sorted(IMAGE_EXTENSIONS)
    if not exts:
        return None
    return [part for part in (chunk.strip() for chunk in exts.split(",")) if part]


def _bar(fraction: float, width: int = 18) -> str:
    filled = max(0, min(width, round(fraction * width)))
    return "[cyan]" + "#" * filled + "[/cyan][dim]" + "-" * (width - filled) + "[/dim]"


def _share_bar(count: int, total: int) -> str:
    fraction = count / total if total else 0.0
    return f"{_bar(fraction)} {fraction * 100:5.1f}%"


def _fail(message: str, code: int = 1) -> None:
    error_console.print(f"[red]error:[/red] {message}")
    raise typer.Exit(code)


# --------------------------------------------------------------------------- #
# root callback
# --------------------------------------------------------------------------- #
@app.callback()
def root(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """Dataset-inspection CLIs for folders and datasets."""


# --------------------------------------------------------------------------- #
# dataset summary
# --------------------------------------------------------------------------- #
@app.command()
def summary(
    path: Path = typer.Argument(Path("."), help="Folder to inspect."),
    top: int = typer.Option(10, "--top", "-n", min=1, help="Rows per table."),
    ext: str | None = typer.Option(
        None, "--ext", "-e", help='Comma separated filter, e.g. "jpg,png".'
    ),
    images_only: bool = typer.Option(False, "--images-only", help="Only look at image files."),
) -> None:
    """Count files, images and total size in a folder tree."""
    root_path = _resolve_dir(path)
    with console.status(f"Scanning {root_path} ..."):
        data = scan_dataset(root_path, largest=top, extensions=_extensions_from(ext, images_only))
    _render_summary(data, top)


def _render_summary(data: DatasetSummary, top: int) -> None:
    console.print(f"\n[bold]Dataset[/bold]  {data.root}\n")

    overview = Table(box=None, show_header=False, padding=(0, 3, 0, 0))
    overview.add_column(style="dim", justify="right")
    overview.add_column(style="bold", justify="right")
    overview.add_row("Folders", f"{data.total_dirs:,}")
    overview.add_row("Files", f"{data.total_files:,}")
    overview.add_row("Total size", human_size(data.total_size))
    overview.add_row("Images", f"{data.image_files:,}")
    overview.add_row("Image size", human_size(data.image_size))
    overview.add_row("Avg. file size", human_size(data.average_size))
    console.print(overview)

    if not data.by_extension:
        console.print("\n[yellow]No files matched.[/yellow]")
        return

    table = Table(title="By extension", title_justify="left", header_style="bold")
    table.add_column("Ext")
    table.add_column("Files", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Share", no_wrap=True)

    ranked = sorted(data.by_extension.items(), key=lambda item: (-item[1], item[0]))
    for name, count in ranked[: max(top, 1)]:
        table.add_row(
            name,
            f"{count:,}",
            human_size(data.size_by_extension[name]),
            _share_bar(count, data.total_files),
        )
    console.print()
    console.print(table)

    if data.largest:
        biggest = Table(title="Largest files", title_justify="left", header_style="bold")
        biggest.add_column("Size", justify="right")
        biggest.add_column("Path")
        for info in data.largest:
            try:
                shown = info.path.relative_to(data.root)
            except ValueError:
                shown = info.path
            biggest.add_row(human_size(info.size), str(shown))
        console.print()
        console.print(biggest)
    console.print()


# --------------------------------------------------------------------------- #
# dataset tree
# --------------------------------------------------------------------------- #
@app.command()
def tree(
    path: Path = typer.Argument(Path("."), help="Folder to display."),
    depth: int = typer.Option(3, "--depth", "-d", min=1, help="How many levels to expand."),
    ext: str | None = typer.Option(None, "--ext", "-e", help="Comma separated filter."),
    images_only: bool = typer.Option(False, "--images-only", help="Only count image files."),
) -> None:
    """Show the folder structure with per-folder file counts and sizes."""
    root_path = _resolve_dir(path)
    node = build_tree(root_path, max_depth=depth, extensions=_extensions_from(ext, images_only))

    label = f"[bold]{node.name}[/bold] [dim]({node.files:,} files, {human_size(node.size)})[/dim]"
    rich_tree = Tree(label)
    _add_children(rich_tree, node)
    console.print()
    console.print(rich_tree)
    console.print()


def _add_children(parent: Tree, node: DirNode) -> None:
    for child in node.children:
        suffix = " [dim]...[/dim]" if child.truncated else ""
        label = (
            f"[cyan]{child.name}[/cyan] "
            f"[dim]({child.files:,} files, {human_size(child.size)})[/dim]{suffix}"
        )
        branch = parent.add(label)
        _add_children(branch, child)


# --------------------------------------------------------------------------- #
# dataset files
# --------------------------------------------------------------------------- #
@app.command()
def files(
    path: Path = typer.Argument(Path("."), help="Folder to search."),
    ext: str | None = typer.Option(None, "--ext", "-e", help="Comma separated filter."),
    images_only: bool = typer.Option(False, "--images-only", help="Only image files."),
    min_size: str | None = typer.Option(None, "--min-size", help='e.g. "500kb" or "2MB".'),
    limit: int = typer.Option(25, "--limit", "-l", min=1, help="Max rows to print."),
    sort: str = typer.Option("size", "--sort", help="Sort by 'size' or 'name'."),
) -> None:
    """List files matching filters, biggest first."""
    root_path = _resolve_dir(path)

    threshold = 0
    if min_size:
        try:
            threshold = parse_size(min_size)
        except ValueError as exc:
            _fail(str(exc))

    collected = []
    wanted = normalize_extensions(_extensions_from(ext, images_only))
    for item in iter_files(root_path):
        if wanted is not None and item.suffix.lower() not in wanted:
            continue
        try:
            size = item.stat().st_size
        except OSError:
            continue
        if size < threshold:
            continue
        collected.append((item, size))

    if sort not in {"size", "name"}:
        _fail("--sort must be 'size' or 'name'")

    if sort == "size":
        collected.sort(key=lambda pair: (-pair[1], str(pair[0])))
    else:
        collected.sort(key=lambda pair: str(pair[0]))

    total = sum(size for _, size in collected)
    console.print(
        f"\n[bold]{len(collected):,}[/bold] file(s), {human_size(total)} in {root_path}\n"
    )

    table = Table(box=None, header_style="bold", padding=(0, 2, 0, 0))
    table.add_column("Size", justify="right")
    table.add_column("Ext")
    table.add_column("Path")
    for item, size in collected[:limit]:
        try:
            shown = item.relative_to(root_path)
        except ValueError:
            shown = item
        table.add_row(human_size(size), item.suffix.lower() or "-", str(shown))
    console.print(table)

    if len(collected) > limit:
        console.print(f"\n[dim]... {len(collected) - limit:,} more (use --limit)[/dim]")
    console.print()


# --------------------------------------------------------------------------- #
# dataset duplicates
# --------------------------------------------------------------------------- #
@app.command()
def duplicates(
    path: Path = typer.Argument(Path("."), help="Folder to scan."),
    ext: str | None = typer.Option(None, "--ext", "-e", help="Comma separated filter."),
    images_only: bool = typer.Option(False, "--images-only", help="Only image files."),
    limit: int = typer.Option(20, "--limit", "-l", min=1, help="Max groups to print."),
) -> None:
    """Find files with identical content and report wasted space."""
    root_path = _resolve_dir(path)
    with console.status("Hashing files ..."):
        groups = find_duplicates(root_path, extensions=_extensions_from(ext, images_only))

    if not groups:
        console.print("\n[green]No duplicate files found.[/green]\n")
        return

    recoverable = 0
    for paths in groups.values():
        recoverable += paths[0].stat().st_size * (len(paths) - 1)

    console.print(
        f"\n[bold]{len(groups):,}[/bold] duplicate group(s), "
        f"recoverable: [bold]{human_size(recoverable)}[/bold]\n"
    )

    ranked = sorted(groups.values(), key=lambda paths: -paths[0].stat().st_size)
    for index, paths in enumerate(ranked[:limit], start=1):
        size = paths[0].stat().st_size
        console.print(f"[bold cyan]{index}.[/bold cyan] {human_size(size)} x {len(paths)}")
        for item in paths:
            try:
                shown = item.relative_to(root_path)
            except ValueError:
                shown = item
            console.print(f"   [dim]{shown}[/dim]")
        console.print()

    if len(ranked) > limit:
        console.print(f"[dim]... {len(ranked) - limit:,} more group(s)[/dim]\n")


def main() -> None:
    """Console script entry point."""
    app()


if __name__ == "__main__":
    main()
