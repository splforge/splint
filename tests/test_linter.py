from splint.config import Config
from splint.linter import lint_text


def test_noqa_bare_suppresses_line():
    text = "index=* | stats count ```noqa```"
    assert lint_text(text) == []


def test_noqa_specific_code():
    text = "index=*|stats count ```noqa: SPL001```"
    found = [d.code for d in lint_text(text)]
    assert "SPL001" not in found
    assert "SPL101" in found  # not suppressed


def test_select_limits_rules():
    cfg = Config(select=["SPL003"])
    found = [d.code for d in lint_text("index=* | join x [ search y ]", cfg)]
    assert found == ["SPL003"]


def test_ignore_disables_rule():
    cfg = Config(ignore=["SPL001"])
    found = [d.code for d in lint_text("index=* | stats count", cfg)]
    assert "SPL001" not in found


def test_diagnostics_sorted_by_position():
    text = "index=*|transaction sid"
    diags = lint_text(text)
    keys = [d.sort_key() for d in diags]
    assert keys == sorted(keys)
