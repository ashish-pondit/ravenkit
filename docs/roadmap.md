# Roadmap

Planned capabilities, then the phases for the current renaming/documentation
work.

## Planned tools

These are ideas, not commitments — scope and flags are undecided until each one
gets its own design pass.

| Tool | Idea |
| --- | --- |
| `raven report` | Emit the summary as JSON or CSV so the numbers can feed a pipeline or a notebook, instead of only being rendered for humans. |
| `raven validate` | Flag dataset problems: unreadable files, zero-byte images, truncated data, wrong extensions for the detected format. |
| `raven compare` | Diff two folders — files added, removed, changed in size — useful for checking a dataset version against the previous one. |
| `raven manifest` | Write a checksum list (path + size + hash) to pin a dataset version or verify a copy after transfer. |
| `raven stats` | Richer distribution views: per-extension size histograms, size quantiles, dimension stats for images. |

`RAW_EXTENSIONS` in `dataset.py` already lists camera raw formats in
anticipation of `validate` and `stats`; nothing consumes it yet.

### Explicitly out of scope

- **Destructive deduplication** (`duplicates --delete`). Reporting is safe;
  deleting is not. If this ever lands it needs a dry-run default, an explicit
  confirmation flag, and a separate design conversation.

## Current phase plan

The work below renames the project from its original name to `ravenkit` and
moves detail out of `AGENTS.md` into this folder.

| Phase | Work | Status |
| --- | --- | --- |
| 1 | Rename the package to `ravenkit`, the CLI to `raven`, flatten the command surface, add the MIT `LICENSE` and a CLI smoke test. | ✅ done |
| 2 | Write `docs/` (`commands`, `architecture`, `development`, `roadmap`) by extracting detail from the old `README.md` and `AGENTS.md`. | ✅ done |
| 3 | Slim `AGENTS.md` to an index and `README.md` to a pitch, both pointing here. | 🔄 in progress |
| 4 | End-to-end verification on a fresh install and update the project notes. | ⏳ planned |
