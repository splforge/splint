"""A tolerant, grammar-free parser for Splunk SPL pipelines.

The goal is not to fully understand SPL semantics, but to robustly split a
search into its top-level commands while correctly ignoring pipes that appear
inside quoted strings, ``[ ... ]`` subsearches, and ``` ``` `` comments.

This is deliberately permissive: malformed input never raises, it just yields a
best-effort decomposition. That keeps the linter usable on the messy, real-world
searches people actually paste in.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from splint.models import Position


@dataclass(frozen=True)
class Comment:
    """A ``` ``` `` triple-backtick comment span."""

    text: str
    offset: int
    position: Position


@dataclass(frozen=True)
class Pipe:
    """A top-level pipe ``|`` separating two commands."""

    offset: int
    position: Position
    space_before: bool
    space_after: bool


@dataclass
class Command:
    """A single top-level SPL command (the text between two top-level pipes)."""

    raw: str
    offset: int
    position: Position
    index: int

    @property
    def name(self) -> str:
        """The command verb, lowercased. Empty string if the command is blank.

        A leading ``search`` is implicit on the first command in SPL; the verb is
        whatever the first bare token is.
        """
        stripped = self.raw.strip()
        if not stripped:
            return ""
        token = stripped.split(maxsplit=1)[0]
        return token.lower()

    @property
    def args(self) -> str:
        """Everything after the command verb."""
        stripped = self.raw.strip()
        parts = stripped.split(maxsplit=1)
        return parts[1] if len(parts) > 1 else ""


@dataclass
class ParsedSearch:
    """The decomposed result of parsing an SPL search."""

    text: str
    commands: list[Command] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    pipes: list[Pipe] = field(default_factory=list)

    def line_text(self, line: int) -> str:
        lines = self.text.splitlines()
        if 1 <= line <= len(lines):
            return lines[line - 1]
        return ""


def offset_to_position(text: str, offset: int) -> Position:
    """Convert a 0-based character offset into a 1-based line/column Position."""
    line = text.count("\n", 0, offset) + 1
    last_newline = text.rfind("\n", 0, offset)
    column = offset - last_newline  # works even when last_newline == -1
    return Position(line=line, column=column)


# Backwards-compatible private alias.
_offset_to_position = offset_to_position


def parse(text: str) -> ParsedSearch:
    """Parse an SPL search string into a :class:`ParsedSearch`.

    Never raises on malformed input.
    """
    result = ParsedSearch(text=text)

    n = len(text)
    i = 0
    bracket_depth = 0
    command_start = 0

    def flush_command(end: int) -> None:
        raw = text[command_start:end]
        if raw.strip() == "" and not result.commands:
            # leading whitespace before the first command; skip emitting empty
            return
        result.commands.append(
            Command(
                raw=raw,
                offset=command_start,
                position=_offset_to_position(text, command_start),
                index=len(result.commands),
            )
        )

    while i < n:
        ch = text[i]

        # Triple-backtick comment.
        if text.startswith("```", i):
            end = text.find("```", i + 3)
            if end == -1:
                end = n
                content = text[i + 3 : end]
                consumed_to = n
            else:
                content = text[i + 3 : end]
                consumed_to = end + 3
            result.comments.append(
                Comment(
                    text=content,
                    offset=i,
                    position=_offset_to_position(text, i),
                )
            )
            i = consumed_to
            continue

        # Quoted strings: skip until the matching unescaped quote.
        if ch in ('"', "'"):
            quote = ch
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue

        # Subsearch / bracket nesting.
        if ch == "[":
            bracket_depth += 1
            i += 1
            continue
        if ch == "]":
            if bracket_depth > 0:
                bracket_depth -= 1
            i += 1
            continue

        # Top-level pipe → command separator.
        if ch == "|" and bracket_depth == 0:
            flush_command(i)
            space_before = i > 0 and text[i - 1].isspace()
            space_after = i + 1 < n and text[i + 1].isspace()
            result.pipes.append(
                Pipe(
                    offset=i,
                    position=_offset_to_position(text, i),
                    space_before=space_before,
                    space_after=space_after,
                )
            )
            command_start = i + 1
            i += 1
            continue

        i += 1

    flush_command(n)
    return result
