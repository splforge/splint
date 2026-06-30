"""Output formatters: text, JSON and SARIF."""

from __future__ import annotations

import json
from collections.abc import Iterable

from splint import __version__
from splint.models import Diagnostic
from splint.rules import rules_by_code

FileDiagnostics = tuple[str, list[Diagnostic]]


def format_text(results: Iterable[FileDiagnostics], *, color: bool = False) -> str:
    """Human-readable, grep-friendly ``path:line:col: CODE message`` output."""
    lines: list[str] = []
    total = 0
    for path, diags in results:
        for d in diags:
            total += 1
            code = _colorize(d.code, _SEVERITY_COLOR.get(d.severity.value, ""), color)
            lines.append(
                f"{path}:{d.position.line}:{d.position.column}: {code} {d.message}"
            )
    if total == 0:
        lines.append("All clear: no issues found.")
    else:
        noun = "issue" if total == 1 else "issues"
        lines.append("")
        lines.append(f"Found {total} {noun}.")
    return "\n".join(lines)


def format_json(results: Iterable[FileDiagnostics]) -> str:
    payload = []
    for path, diags in results:
        for d in diags:
            payload.append(
                {
                    "path": path,
                    "line": d.position.line,
                    "column": d.position.column,
                    "code": d.code,
                    "rule": d.rule_name,
                    "severity": d.severity.value,
                    "message": d.message,
                }
            )
    return json.dumps({"version": __version__, "diagnostics": payload}, indent=2)


def format_sarif(results: Iterable[FileDiagnostics]) -> str:
    by_code = rules_by_code()
    used_codes: dict[str, None] = {}
    sarif_results = []

    for path, diags in results:
        for d in diags:
            used_codes.setdefault(d.code, None)
            sarif_results.append(
                {
                    "ruleId": d.code,
                    "level": d.severity.sarif_level,
                    "message": {"text": d.message},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": path},
                                "region": {
                                    "startLine": d.position.line,
                                    "startColumn": d.position.column,
                                },
                            }
                        }
                    ],
                }
            )

    sarif_rules = []
    for code in used_codes:
        rule = by_code.get(code)
        sarif_rules.append(
            {
                "id": code,
                "name": rule.name if rule else code,
                "shortDescription": {
                    "text": rule.description if rule else code
                },
                "defaultConfiguration": {
                    "level": rule.severity.sarif_level if rule else "warning"
                },
            }
        )

    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "splint",
                        "version": __version__,
                        "informationUri": "https://github.com/kevinbelon/splint",
                        "rules": sarif_rules,
                    }
                },
                "results": sarif_results,
            }
        ],
    }
    return json.dumps(sarif, indent=2)


_SEVERITY_COLOR = {
    "error": "31",  # red
    "warning": "33",  # yellow
    "info": "36",  # cyan
}


def _colorize(text: str, code: str, enabled: bool) -> str:
    if not enabled or not code:
        return text
    return f"\033[{code}m{text}\033[0m"


REPORTERS = {
    "text": format_text,
    "json": format_json,
    "sarif": format_sarif,
}
