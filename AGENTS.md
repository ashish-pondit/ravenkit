# AGENTS.md

## Project
`pyutils` — small, dependency-light Python CLI tools for everyday dataset/file chores.
Entry point: `pyutils` → `pyutils.cli:main` (see `pyproject.toml`).

## Layout
- `src/pyutils/cli.py` — Typer app. Thin: parse args, render, exit.
- `src/pyutils/dataset.py` — pure scan logic (`scan_dataset`, `build_tree`, `find_duplicates`).
- `tests/` — pytest tests for the logic layer.

## Rules
- Keep logic out of the CLI: add pure functions to a module, not to `cli.py`.
- Never use `print()`; use the shared `rich` `console` from `cli.py`.
- Target Python 3.10+; use modern syntax (`list[str]`, `str | None`) since `from __future__ import annotations` is on.
- Every new helper needs a test in `tests/`.
- Keep dependencies minimal; prefer the stdlib.

## Commands
```bash
pip install -e ".[dev]"                  # install (editable, with dev extras)
pyutils dataset summary <path>           # run
python -m pyutils dataset tree <path>    # run without installing the script
pytest                                   # test
ruff check . && ruff format .            # lint + format
```

## CLI conventions
- Folder arguments expand `~` and must exist, otherwise exit code 1 with a clear message.
- Accept `--ext "jpg,png"` (comma separated) and `--images-only` for filtering.
- Human-readable sizes via `dataset.human_size`; parse input sizes via `dataset.parse_size`.
