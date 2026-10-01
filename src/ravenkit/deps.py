"""Optional-dependency checks.

Pure helpers: they return data and never print. The CLI turns the result into a
message and an exit code (see ``cli._require``).

Optional dependencies are declared in ``pyproject.toml`` under
``[project.optional-dependencies]``. This module knows which *importable* module
each extra needs, so a command can fail with a useful install hint instead of an
``ImportError``.

>>> missing("images", {})
[]
"""

from __future__ import annotations

import importlib.util
from collections.abc import Mapping
from typing import NamedTuple


class Requirement(NamedTuple):
    """One optional dependency, named both ways round.

    ``module`` is what Python must be able to import; ``package`` is what the
    user must feed to pip. They differ often enough (``PIL`` vs ``Pillow``) that
    guessing one from the other would be wrong.
    """

    module: str
    package: str


#: extra name -> the requirements that extra pulls in.
#: Empty until the first optional dependency actually lands; see
#: ``docs/development.md`` for how to register one.
EXTRA_MODULES: Mapping[str, tuple[Requirement, ...]] = {}


def missing(
    extra: str,
    registry: Mapping[str, tuple[Requirement, ...]] | None = None,
) -> list[Requirement]:
    """Return the requirements of *extra* that can not currently be imported.

    *registry* defaults to :data:`EXTRA_MODULES` and exists so tests (and future
    callers) can supply their own table instead of monkeypatching this module.
    An unknown extra has nothing to check, so it reports nothing missing.
    """
    table = EXTRA_MODULES if registry is None else registry
    return [req for req in table.get(extra, ()) if importlib.util.find_spec(req.module) is None]


def render_missing(extra: str, requirements: list[Requirement], command: str) -> str:
    """Build the user-facing message for a set of missing requirements."""
    packages = "\n".join(f"  - {req.package}" for req in requirements)
    return (
        f"'{command}' needs optional dependencies that aren't installed:\n"
        f"{packages}\n"
        "install them with:\n"
        f'  pip install -e ".[{extra}]"        # from a source checkout\n'
        f'  pip install "ravenkit[{extra}]"    # normal install'
    )
