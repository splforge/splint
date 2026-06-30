import json

from splint.linter import lint_text
from splint.reporters import format_json, format_sarif, format_text


def _results():
    return [("query.spl", lint_text("index=* | join x [ search y ]"))]


def test_text_reporter_lists_and_summarizes():
    out = format_text(_results())
    assert "query.spl:1:" in out
    assert "Found" in out


def test_text_reporter_all_clear():
    out = format_text([("ok.spl", lint_text("index=main | stats count"))])
    assert "All clear" in out


def test_json_reporter_is_valid_json():
    data = json.loads(format_json(_results()))
    assert data["diagnostics"]
    assert {"path", "line", "column", "code", "severity", "message"} <= set(
        data["diagnostics"][0]
    )


def test_sarif_reporter_structure():
    data = json.loads(format_sarif(_results()))
    assert data["version"] == "2.1.0"
    run = data["runs"][0]
    assert run["tool"]["driver"]["name"] == "splint"
    assert run["results"]
    assert run["tool"]["driver"]["rules"]
