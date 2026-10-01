# pyutils

Small, dependency-light CLI helpers for everyday dataset and folder chores.

```bash
pyutils dataset summary ~/data/mydataset
```

## Install

```bash
pip install -e ".[dev]"
```

## Commands

### `pyutils dataset summary [PATH]`

Counts folders, files, images, total size, per-extension breakdown and the largest files.

```bash
pyutils dataset summary ./data --top 15
pyutils dataset summary ./data --images-only
pyutils dataset summary ./data --ext "jpg,png,webp"
```

### `pyutils dataset tree [PATH]`

Prints the folder structure with recursive file counts and sizes per folder.

```bash
pyutils dataset tree ./data --depth 2
pyutils dataset tree ./data --images-only
```

### `pyutils dataset files [PATH]`

Lists files matching filters, biggest first.

```bash
pyutils dataset files ./data --images-only --min-size 2MB --limit 50
pyutils dataset files ./data --ext jpg --sort name
```

### `pyutils dataset duplicates [PATH]`

Finds files with identical content (size pre-filter, then BLAKE2b hash) and reports
how much space could be recovered.

```bash
pyutils dataset duplicates ./data --images-only
```

## Development

```bash
pytest            # run tests
ruff check .      # lint
ruff format .     # format
```

## Layout

| Path | Purpose |
| --- | --- |
| `src/pyutils/cli.py` | Typer app, argument parsing, pretty output |
| `src/pyutils/dataset.py` | Pure scanning logic (no printing, fully testable) |
| `tests/` | pytest suite for the logic layer |

## Adding a new tool

1. Put the logic in a new module next to `dataset.py` — plain functions, no `print`.
2. Add a `typer.Typer()` sub-app in `cli.py` and register it with `app.add_typer(...)`.
3. Cover the logic with tests in `tests/`.
