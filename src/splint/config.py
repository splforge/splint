"""Configuration loading for splint.

Resolution order (first match wins):

1. An explicit path passed on the CLI (``--config``).
2. ``.spl-lint.toml`` in the current directory (the whole file is the config).
3. The ``[tool.splint]`` table in ``pyproject.toml``.
4. Built-in defaults (all rules enabled).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from splint.rules import rules_by_code


@dataclass
class Config:
    """Effective linter configuration."""

    select: list[str] = field(default_factory=list)
    ignore: list[str] = field(default_factory=list)

    def enabled_codes(self) -> set[str]:
        """Resolve which rule codes are active after select/ignore."""
        all_codes = set(rules_by_code())
        selected = set(self.select) & all_codes if self.select else set(all_codes)
        return selected - set(self.ignore)


def _coerce(raw: dict) -> Config:
    select = [str(c).strip().upper() for c in raw.get("select", []) or []]
    ignore = [str(c).strip().upper() for c in raw.get("ignore", []) or []]
    return Config(select=select, ignore=ignore)


def load_config(explicit: str | Path | None = None, start: Path | None = None) -> Config:
    """Load configuration, searching the filesystem when no explicit path given."""
    if explicit is not None:
        data = tomllib.loads(Path(explicit).read_text(encoding="utf-8"))
        # An explicit .spl-lint.toml may or may not nest under [tool.splint].
        table = data.get("tool", {}).get("splint", data)
        return _coerce(table)

    base = start or Path.cwd()

    spl_toml = base / ".spl-lint.toml"
    if spl_toml.is_file():
        data = tomllib.loads(spl_toml.read_text(encoding="utf-8"))
        table = data.get("tool", {}).get("splint", data)
        return _coerce(table)

    pyproject = base / "pyproject.toml"
    if pyproject.is_file():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        table = data.get("tool", {}).get("splint")
        if table is not None:
            return _coerce(table)

    return Config()
