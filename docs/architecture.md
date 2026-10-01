# Architecture

The codebase is split by **responsibility**, not by feature. Keeping the split
strict is what makes the tool easy to test and extend.

```
src/ravenkit/
├── cli.py       # presentation: parse args, call logic, render, exit
└── dataset.py   # pure logic: no printing, no CLI knowledge
```

## The layering rule

`cli.py` may import `dataset.py`. **`dataset.py` must never import `cli.py`.**

`dataset.py` is pure: functions take plain inputs (a `Path`, an extension list)
and return plain data (dataclasses, dicts, iterators). It never writes to the
screen and never exits the process. This means every algorithm can be tested by
calling a function and asserting on its return value — no output capture, no
mocking.

`cli.py` is thin. Each command does three things:

1. validate arguments (`_resolve_dir`, `_extensions_from`)
2. call one logic function
3. render the result with `rich`

Anything that is *computable* belongs in `dataset.py`; anything that is
*displayable* belongs in `cli.py`.

## Output rules

- **Never** use `print()`. Always the module-level `console` from `cli.py`.
- Errors go to `error_console` (stderr), not stdout, via the `_fail` helper, so
  piped output stays clean.
- Rich handles all colour and table layout, so nothing else formats for humans.

## Logic module: `dataset.py`

### Constants

| Name | Purpose |
| --- | --- |
| `IMAGE_EXTENSIONS` | The set behind `--images-only`. Drives the image counts in `summary`. |
| `RAW_EXTENSIONS` | Camera raw formats (`.arw .cr2 .dng .nef .orf .raf .rw2`). Declared for future use; no command consumes it yet. |

### Shared helpers

| Function | Contract |
| --- | --- |
| `human_size(num_bytes)` | `1536` → `"1.5 KB"`. Used for every size shown to a user. |
| `parse_size(text)` | `"1.5 MB"` → `1572864`. Raises `ValueError` on bad input; the CLI turns that into exit code 1. |
| `normalize_extensions(exts)` | `["JPG", ".png"]` → `frozenset({".jpg", ".png"})`. Returns `None` when there is no filter, which means "everything". `None` vs. empty set is meaningful — always check for `None`. |
| `ext_label(path)` | Lowercase extension, or `"<none>"` for files without one. |
| `iter_files(root, ...)` | Yields files in sorted order, skipping symlinks by default. The single place that walks a directory tree. |

### Data structures

| Type | Shape |
| --- | --- |
| `FileInfo` | Frozen dataclass: `path` + cached `size`, plus an `.ext` property. |
| `DatasetSummary` | Mutable aggregate: totals, per-extension counters, largest files. Derived properties `non_image_files` and `average_size` are computed, never stored. |
| `DirNode` | One folder in the tree view: recursive `files`/`size`, `children`, and `truncated`. |

### Algorithms

- **`scan_dataset`** — one walk collecting counts, sizes and the biggest files.
  Folder counting uses a separate `rglob` pass so directory totals are correct
  even when an extension filter is active.
- **`build_tree`** — recurses to `max_depth`. Beyond that it switches to
  `_count_subtree`, which sums the remaining depth without materialising nodes,
  and marks the node `truncated`. This is why deep trees stay cheap to render.
- **`find_duplicates`** — buckets files by size, then hashes only buckets with
  more than one member (BLAKE2b, 128-bit, streamed in 1 MiB chunks). Size is a
  free pre-filter: files of different sizes can never be identical.

## Why it is shaped this way

- The CLI is swapped or wrapped (tests, future library use) without touching
  the algorithms.
- The algorithms are testable with no I/O capture.
- Rendering bugs and counting bugs cannot hide behind each other.
