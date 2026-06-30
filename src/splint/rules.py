"""The linting rules shipped with splint.

Each rule is a small object exposing ``code``, ``name``, ``severity`` and a
``check(parsed) -> list[Diagnostic]`` method. Rules never mutate state, so the
registry can be shared freely.
"""

from __future__ import annotations

import re
from typing import Protocol

from splint.models import Diagnostic, Severity
from splint.parser import Command, ParsedSearch, offset_to_position


class Rule(Protocol):
    code: str
    name: str
    severity: Severity
    description: str

    def check(self, parsed: ParsedSearch) -> list[Diagnostic]: ...


def _diag(
    parsed: ParsedSearch,
    command: Command,
    rule: Rule,
    message: str,
    *,
    match_offset: int | None = None,
) -> Diagnostic:
    """Build a Diagnostic, preferring a precise offset when available."""
    if match_offset is not None:
        position = offset_to_position(parsed.text, match_offset)
    else:
        position = command.position
    return Diagnostic(
        code=rule.code,
        message=message,
        severity=rule.severity,
        position=position,
        rule_name=rule.name,
    )


# --- Performance rules -------------------------------------------------------

# Matches `index=*`, `index = *`, `index="*"`, `index=foo*`, etc. Captures the
# value so we can distinguish a bare wildcard from a wildcard suffix.
_INDEX_RE = re.compile(r"\bindex\s*=\s*\"?(?P<val>[^\s\"|]*\*[^\s\"|]*)\"?", re.IGNORECASE)


class IndexWildcard:
    code = "SPL001"
    name = "index-wildcard"
    severity = Severity.WARNING
    description = "Avoid wildcards in the index specifier; they force broad scans."

    def check(self, parsed: ParsedSearch) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for cmd in parsed.commands:
            # Only relevant where `index=` filtering happens (first command or
            # an explicit `search`).
            if cmd.index != 0 and cmd.name != "search":
                continue
            for m in _INDEX_RE.finditer(cmd.raw):
                val = m.group("val")
                offset = cmd.offset + m.start()
                msg = (
                    f"`index={val}` uses a wildcard; specify explicit indexes to "
                    "avoid scanning every index."
                )
                out.append(_diag(parsed, cmd, self, msg, match_offset=offset))
        return out


# A field value beginning with `*`, e.g. `user=*admin`. Excludes pure `index=*`
# (covered by SPL001) by simply not special-casing index here — a leading
# wildcard anywhere is bad, but we skip the index field to avoid double-flagging.
_LEADING_WC_RE = re.compile(r"(?P<field>\b\w+)\s*=\s*\"?(?P<val>\*[^\s\"|]*)\"?")


class LeadingWildcard:
    code = "SPL002"
    name = "leading-wildcard"
    severity = Severity.INFO
    description = "Leading wildcards prevent index/term optimisation."

    def check(self, parsed: ParsedSearch) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for cmd in parsed.commands:
            # Leading wildcards hurt most during index/term retrieval, i.e. in
            # the base search. Downstream (`tstats` WHERE, `where`/`eval` on
            # already-retrieved rows) the impact is marginal, so we don't flag it.
            if cmd.index != 0 and cmd.name != "search":
                continue
            for m in _LEADING_WC_RE.finditer(cmd.raw):
                if m.group("field").lower() == "index":
                    continue  # SPL001 owns the index field
                offset = cmd.offset + m.start("val")
                field = m.group("field")
                msg = (
                    f"`{field}={m.group('val')}` has a leading wildcard, which "
                    "disables efficient term lookups."
                )
                out.append(_diag(parsed, cmd, self, msg, match_offset=offset))
        return out


class JoinUsage:
    code = "SPL003"
    name = "join-usage"
    severity = Severity.WARNING
    description = "`join` is expensive and silently truncates; prefer stats/lookup."

    def check(self, parsed: ParsedSearch) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for cmd in parsed.commands:
            if cmd.name == "join":
                msg = (
                    "`join` is costly and caps subsearch results (default 50k); "
                    "consider `stats`, `eventstats`, or a `lookup` instead."
                )
                out.append(_diag(parsed, cmd, self, msg))
        return out


class TransactionUsage:
    code = "SPL004"
    name = "transaction-usage"
    severity = Severity.WARNING
    description = "`transaction` is memory-heavy; prefer `stats` by a correlation id."

    def check(self, parsed: ParsedSearch) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for cmd in parsed.commands:
            if cmd.name == "transaction":
                msg = (
                    "`transaction` is memory-intensive and not distributable; "
                    "prefer `stats` grouped by a correlation field when possible."
                )
                out.append(_diag(parsed, cmd, self, msg))
        return out


_SORT_LIMIT_RE = re.compile(r"\blimit\s*=\s*(\d+)", re.IGNORECASE)
_SORT_LEADING_INT_RE = re.compile(r"^\s*(\d+)\b")


class UnboundedSort:
    code = "SPL005"
    name = "unbounded-sort"
    severity = Severity.WARNING
    description = "`sort` without a limit sorts the entire result set."

    def check(self, parsed: ParsedSearch) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for cmd in parsed.commands:
            if cmd.name != "sort":
                continue
            args = cmd.args
            limit_match = _SORT_LIMIT_RE.search(args)
            leading_int = _SORT_LEADING_INT_RE.match(args)
            # `sort 0 ...` and `limit=0` explicitly mean "no limit" but are
            # intentional, so we treat any provided count as bounded.
            if limit_match or leading_int:
                continue
            msg = (
                "`sort` has no limit; add a count (e.g. `sort 100 -_time`) to "
                "cap memory and runtime."
            )
            out.append(_diag(parsed, cmd, self, msg))
        return out


# --- Style rules -------------------------------------------------------------


class PipeSpacing:
    code = "SPL101"
    name = "pipe-spacing"
    severity = Severity.INFO
    description = "Use a single space around the pipe `|` for readability."

    def check(self, parsed: ParsedSearch) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for pipe in parsed.pipes:
            # A pipe with only whitespace before it is a leading pipe (the search
            # starts with `| tstats ...`), which is valid SPL — only the spacing
            # *after* it is meaningful.
            leading = parsed.text[: pipe.offset].strip() == ""
            sides = []
            if not leading and not pipe.space_before:
                sides.append("before")
            if not pipe.space_after:
                sides.append("after")
            if not sides:
                continue
            msg = f"Missing space {' and '.join(sides)} pipe `|`."
            out.append(
                Diagnostic(
                    code=self.code,
                    message=msg,
                    severity=self.severity,
                    position=pipe.position,
                    rule_name=self.name,
                )
            )
        return out


ALL_RULES: list[Rule] = [
    IndexWildcard(),
    LeadingWildcard(),
    JoinUsage(),
    TransactionUsage(),
    UnboundedSort(),
    PipeSpacing(),
]


def rules_by_code() -> dict[str, Rule]:
    return {rule.code: rule for rule in ALL_RULES}
