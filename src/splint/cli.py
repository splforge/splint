"""Command-line interface for splint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from splint import __version__
from splint.config import Config, load_config
from splint.linter import lint_text
from splint.reporters import REPORTERS

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_ERROR = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="splint",
        description="A fast, zero-dependency linter for Splunk SPL searches.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="SPL files to lint. Use '-' to read from stdin.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=sorted(REPORTERS),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--select",
        default=None,
        help="Comma-separated rule codes to enable (overrides config).",
    )
    parser.add_argument(
        "--ignore",
        default=None,
        help="Comma-separated rule codes to disable.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to a config file (.spl-lint.toml or pyproject.toml).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in text output.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"splint {__version__}",
    )
    return parser


def _split_codes(value: str | None) -> list[str]:
    if not value:
        return []
    return [c.strip().upper() for c in value.split(",") if c.strip()]


def _resolve_config(args: argparse.Namespace) -> Config:
    config = load_config(explicit=args.config)
    if args.select is not None:
        config.select = _split_codes(args.select)
    if args.ignore is not None:
        config.ignore = list({*config.ignore, *_split_codes(args.ignore)})
    return config


def _read_source(path: str) -> tuple[str, str]:
    """Return (display_name, text) for a path or stdin."""
    if path == "-":
        return "<stdin>", sys.stdin.read()
    return path, Path(path).read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.paths:
        parser.print_help(sys.stderr)
        return EXIT_ERROR

    try:
        config = _resolve_config(args)
    except (OSError, ValueError) as exc:
        print(f"splint: config error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    results = []
    had_read_error = False
    for path in args.paths:
        try:
            name, text = _read_source(path)
        except OSError as exc:
            print(f"splint: cannot read {path}: {exc}", file=sys.stderr)
            had_read_error = True
            continue
        diagnostics = lint_text(text, config)
        results.append((name, diagnostics))

    reporter = REPORTERS[args.format]
    if args.format == "text":
        output = reporter(results, color=sys.stdout.isatty() and not args.no_color)
    else:
        output = reporter(results)
    print(output)

    if had_read_error:
        return EXIT_ERROR
    total = sum(len(diags) for _, diags in results)
    return EXIT_ISSUES if total else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
