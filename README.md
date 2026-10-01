<p align="center">
  <img src="images/Ravenkit%20Utility%20Tools%20Logo.png" alt="ravenkit logo — a raven carrying utility tags" width="260">
</p>

# ravenkit

Dataset-inspection CLIs for the terminal: count files, measure sizes, break down
formats and find duplicates in a folder tree. Works on any directory; built with
image datasets in mind.

```bash
raven summary ~/data/mydataset
```

## Install

Not yet published to PyPI — install from a checkout:

```bash
pip install -e ".[dev]"
```

## Commands

| Command | What it does |
| --- | --- |
| `raven summary [PATH]` | Folders, files, total size, per-extension breakdown, largest files. |
| `raven tree [PATH]` | Folder structure with per-folder file counts and sizes. |
| `raven files [PATH]` | Files matching your filters, biggest first. |
| `raven duplicates [PATH]` | Byte-identical files and the space they waste. |

```bash
raven summary ./data --top 15
raven tree ./data --depth 2
raven files ./data --images-only --min-size 2MB
raven duplicates ./data --images-only
```

Common filters: `--ext "jpg,png"`, `--images-only`, `--min-size 500kb`.
Run `raven <command> --help` for the full option list.

## Documentation

- [Command reference](docs/commands.md) — every flag, every convention, exit codes
- [Architecture](docs/architecture.md) — how the code is layered
- [Development](docs/development.md) — setup, tests, adding a command
- [Roadmap](docs/roadmap.md) — what's planned

## License

MIT — see [LICENSE](LICENSE).
