# Development

## Setup

```bash
python -m venv .venv
```

Activate it, then install the package in editable mode with the dev extras:

```bash
# Windows (PowerShell)
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

# macOS / Linux
./.venv/bin/python -m pip install -e ".[dev]"
```

Editable install means `raven` on the PATH and `import ravenkit` both point at
`src/ravenkit/`, so edits take effect with no reinstall.

## Everyday commands

```bash
pytest                    # run the test suite
ruff check .              # lint
ruff format .             # format (add --check to verify without writing)
```

`ruff format` and `ruff check` are separate: lint fixes style *errors*, format
fixes layout. Run both before committing.

## Layout

| Path | Purpose |
| --- | --- |
| `src/ravenkit/cli.py` | Typer app, argument parsing, rendering |
| `src/ravenkit/dataset.py` | Pure scanning logic (no printing, fully testable) |
| `src/ravenkit/__main__.py` | Enables `python -m ravenkit` |
| `tests/test_dataset.py` | Tests for the logic layer |
| `tests/test_cli.py` | Smoke tests for the command surface |
| `docs/` | This documentation |

## Adding a new command

1. **Write the logic first.** Add pure functions to a module in
   `src/ravenkit/`. No `print()`, no `typer`, no `sys.exit`. Return plain data.
   Add it to `dataset.py` if it is dataset-related, otherwise create a new
   sibling module (`compare.py`, `manifest.py`, …).
2. **Test the logic.** Add tests in `tests/` alongside `test_dataset.py`. Cover
   the empty case, the filtered case, and at least one real value assertion.
3. **Wire up the CLI.** In `cli.py`, add a function decorated with
   `@app.command()`:
   - take a `path: Path = typer.Argument(Path("."))` and pass it through
     `_resolve_dir()`
   - take filters through `_extensions_from(ext, images_only)`
   - report problems with `_fail("message")` (exit code 1, on stderr). Invalid
     argument *values* become `typer.BadParameter` and exit code 2 — that is
     what `_resolve_dir` does for a missing folder.
   - render with `console` and the `rich` tables/trees already in use
4. **Document it.** Add a section to `docs/commands.md` and, if it changes the
   plan, a line in `docs/roadmap.md`.
5. **Verify.** `ruff format . && ruff check . && pytest`, then run the command
   by hand once.

## Conventions checklist

- Target Python 3.10+; use modern syntax (`list[str]`, `str | None`).
- `from __future__ import annotations` at the top of every module.
- Keep dependencies minimal — prefer the standard library.
- Every new helper gets a test.
- No `print()`, ever: use `console`.
- Keep the CLI thin; keep logic pure.
