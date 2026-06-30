"""The linting engine: parse, run rules, apply suppressions."""

from __future__ import annotations

import re

from splint.config import Config
from splint.models import Diagnostic
from splint.parser import parse
from splint.rules import ALL_RULES

# `noqa` or `noqa: SPL001, SPL003`
_NOQA_RE = re.compile(r"noqa(?:\s*:\s*(?P<codes>[A-Z0-9, ]+))?", re.IGNORECASE)


def _suppressions(parsed) -> dict[int, set[str] | None]:
    """Map line number -> suppressed codes (None means suppress everything)."""
    out: dict[int, set[str] | None] = {}
    for comment in parsed.comments:
        m = _NOQA_RE.search(comment.text)
        if not m:
            continue
        line = comment.position.line
        codes = m.group("codes")
        if codes is None:
            out[line] = None  # bare noqa: suppress all on this line
        else:
            parsed_codes = {c.strip().upper() for c in codes.split(",") if c.strip()}
            existing = out.get(line)
            if existing is None and line in out:
                continue  # already suppressing all
            out[line] = (existing or set()) | parsed_codes
    return out


def _is_suppressed(diag: Diagnostic, suppressions: dict[int, set[str] | None]) -> bool:
    if diag.position.line not in suppressions:
        return False
    codes = suppressions[diag.position.line]
    return codes is None or diag.code in codes


def lint_text(text: str, config: Config | None = None) -> list[Diagnostic]:
    """Lint a raw SPL string and return sorted, filtered diagnostics."""
    config = config or Config()
    enabled = config.enabled_codes()
    parsed = parse(text)
    suppressions = _suppressions(parsed)

    diagnostics: list[Diagnostic] = []
    for rule in ALL_RULES:
        if rule.code not in enabled:
            continue
        for diag in rule.check(parsed):
            if _is_suppressed(diag, suppressions):
                continue
            diagnostics.append(diag)

    diagnostics.sort(key=lambda d: d.sort_key())
    return diagnostics
