# AGENTS.md

## Project
`ravenkit` — a growing kit of dataset-inspection CLIs: count files, sizes, formats
and folders in a directory tree. Works on any folder; built for dataset work
(images especially).
Distribution `ravenkit` · import `ravenkit` · CLI `raven` (→ `ravenkit.cli:main`).

> This file is an index, not a manual. Detail lives in `docs/`.

## Layout
- `src/ravenkit/cli.py` — Typer app; parse, render, exit.
- `src/ravenkit/dataset.py` — pure scan logic.
- `tests/` — pytest for the logic layer.
- `docs/` — detailed guidance (see below).

## Rules
- Keep logic out of the CLI: add pure functions to a module, not to `cli.py`.
- Never use `print()`; use the shared `rich` `console` in `cli.py`.
- Target Python 3.10+; modern syntax (`list[str]`, `str | None`).
- Every new helper needs a test in `tests/`.
- Keep dependencies minimal; prefer the stdlib.

## Commands
```bash
pip install -e ".[dev]"
raven summary <path>
python -m ravenkit summary <path>
pytest
ruff check . && ruff format .
```

## Where to look next
- `docs/commands.md` — CLI reference and conventions
- `docs/architecture.md` — layering rules and shared helpers
- `docs/development.md` — setup, testing, adding a command
- `docs/roadmap.md` — planned tools and the phase plan
