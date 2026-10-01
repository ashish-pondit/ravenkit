# Commands

`raven` inspects a folder tree: how many files, how big, which formats, which
folders, and what is duplicated. It works on any directory but is built with
dataset work in mind (image collections especially).

```
raven [--version] COMMAND [ARGS]...
```

## Conventions

These apply to every command.

- **Path argument** is optional and defaults to the current directory. `~` is
  expanded. A path that does not exist, or that is not a directory, is rejected
  as an invalid value: the command prints an error and exits with code 2.
- **`--ext "jpg,png"`** filters by extension. The value is comma separated, case
  insensitive, and a leading dot is optional (`jpg` and `.JPG` both work).
- **`--images-only`** is shorthand for `--ext` with the built-in image set:
  `.avif .bmp .gif .heic .jpeg .jpg .png .svg .tif .tiff .webp`.
  If both `--images-only` and `--ext` are given, `--images-only` wins.
- **Sizes** (`--min-size`) accept `2048`, `500kb`, `1.5MB`. Units are
  `b`, `k`/`kb`, `m`/`mb`, `g`/`gb`, `t`/`tb`, all powers of 1024. An unknown
  unit is an error (exit code 1).
- Sizes are always printed in human-readable form (`4.4 KB`, `1.2 GB`).

## `raven summary [PATH]`

Counts folders, files and total size in a folder tree, then breaks the files
down by extension and lists the largest ones.

| Option | Default | Meaning |
| --- | --- | --- |
| `PATH` | `.` | Folder to inspect. |
| `--top`, `-n` | `10` | Rows per table (minimum 1). |
| `--ext`, `-e` | – | Comma separated extension filter. |
| `--images-only` | off | Only look at image files. |

Output is three parts: an overview (folders, files, total size, image count and
size, average file size), a **By extension** table ranked by file count, and a
**Largest files** table. If nothing matched, it prints `No files matched.`

```bash
raven summary ~/data/mydataset
raven summary ./data --top 15
raven summary ./data --images-only
raven summary ./data --ext "jpg,png,webp"
```

## `raven tree [PATH]`

Prints the folder structure as a tree, with the file count and total size of
every folder.

| Option | Default | Meaning |
| --- | --- | --- |
| `PATH` | `.` | Folder to display. |
| `--depth`, `-d` | `3` | How many levels to expand (minimum 1). |
| `--ext`, `-e` | – | Comma separated extension filter. |
| `--images-only` | off | Only count image files. |

Folders deeper than `--depth` are still **counted** into their parent's totals
and are marked with a trailing `...` to show they were not expanded.

```bash
raven tree ./data
raven tree ./data --depth 2
raven tree ./data --images-only
```

## `raven files [PATH]`

Lists the files that match the filters, largest first.

| Option | Default | Meaning |
| --- | --- | --- |
| `PATH` | `.` | Folder to search. |
| `--ext`, `-e` | – | Comma separated extension filter. |
| `--images-only` | off | Only image files. |
| `--min-size` | – | Skip files smaller than this, e.g. `500kb` or `2MB`. |
| `--limit`, `-l` | `25` | Maximum rows to print (minimum 1). |
| `--sort` | `size` | `size` (biggest first) or `name` (path order). |

The header reports how many files matched and their combined size. When more
files match than `--limit`, a `... N more (use --limit)` footer is printed.

```bash
raven files ./data --images-only --min-size 2MB --limit 50
raven files ./data --ext jpg --sort name
```

## `raven duplicates [PATH]`

Finds files with byte-identical content and reports how much space could be
recovered by removing the redundant copies.

| Option | Default | Meaning |
| --- | --- | --- |
| `PATH` | `.` | Folder to scan. |
| `--ext`, `-e` | – | Comma separated extension filter. |
| `--images-only` | off | Only image files. |
| `--limit`, `-l` | `20` | Maximum duplicate groups to print (minimum 1). |

Files are grouped by size first, so only same-size candidates are ever hashed
(BLAKE2b, 128-bit). Groups are ranked by file size. When nothing is duplicated
it prints `No duplicate files found.`

```bash
raven duplicates ./data
raven duplicates ./data --images-only
```

> This command only **reports**. It never deletes anything.

## Global options

| Option | Meaning |
| --- | --- |
| `--version`, `-V` | Print `raven <version>` and exit. |
| `--help` | Show help for `raven` or any subcommand. |

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `1` | Runtime error: unknown `--sort` value, unparsable `--min-size`. |
| `2` | Invalid input: bad `PATH`, unknown option, invalid option value. |
