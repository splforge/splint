from splint.linter import lint_text


def codes(text):
    return [d.code for d in lint_text(text)]


def test_spl001_index_wildcard():
    assert "SPL001" in codes("index=* | stats count")


def test_spl001_index_wildcard_suffix():
    assert "SPL001" in codes("index=win* | stats count")


def test_spl001_clean_index_passes():
    assert "SPL001" not in codes("index=main | stats count")


def test_spl002_leading_wildcard():
    found = codes("index=main user=*admin | stats count")
    assert "SPL002" in found
    assert "SPL001" not in found  # index field excluded from SPL002


def test_spl002_only_flags_base_search():
    # A leading wildcard downstream (e.g. inside a where/eval) is not flagged.
    assert "SPL002" not in codes("index=main | where like(path, \"*tmp\") name=*x")


def test_spl003_join():
    assert "SPL003" in codes("index=main | join host [ search index=dns ]")


def test_spl004_transaction():
    assert "SPL004" in codes("index=main | transaction session_id")


def test_spl005_unbounded_sort():
    assert "SPL005" in codes("index=main | sort -_time")


def test_spl005_bounded_sort_passes():
    assert "SPL005" not in codes("index=main | sort 100 -_time")
    assert "SPL005" not in codes("index=main | sort limit=50 -_time")


def test_spl101_pipe_spacing():
    assert "SPL101" in codes("index=main|stats count")
    assert "SPL101" not in codes("index=main | stats count")


def test_spl101_leading_pipe_is_ok():
    # A search starting with `| tstats ...` is valid SPL, not a spacing issue.
    assert "SPL101" not in codes("| tstats count from datamodel=Foo")
    assert "SPL101" not in codes("  | tstats count")


def test_spl101_leading_pipe_still_needs_space_after():
    assert "SPL101" in codes("|tstats count")
