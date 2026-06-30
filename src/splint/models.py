"""Core data structures shared across the linter."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    """Severity level for a diagnostic."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def sarif_level(self) -> str:
        """Map to a SARIF result level."""
        return {
            Severity.ERROR: "error",
            Severity.WARNING: "warning",
            Severity.INFO: "note",
        }[self]


@dataclass(frozen=True)
class Position:
    """A 1-indexed line/column location within a source file."""

    line: int
    column: int


@dataclass(frozen=True)
class Diagnostic:
    """A single linting finding."""

    code: str
    message: str
    severity: Severity
    position: Position
    rule_name: str = ""

    def sort_key(self) -> tuple[int, int, str]:
        return (self.position.line, self.position.column, self.code)
