from splint.parser import parse


def test_splits_top_level_commands():
    parsed = parse("index=main | stats count | sort -count")
    assert [c.name for c in parsed.commands] == ["index=main", "stats", "sort"]


def test_pipe_inside_quotes_is_not_a_separator():
    parsed = parse('search msg="a|b" | stats count')
    assert len(parsed.commands) == 2
    assert parsed.commands[0].name == "search"


def test_pipe_inside_subsearch_is_not_a_separator():
    parsed = parse("index=main [ search error | head 1 ] | stats count")
    # Only the two top-level commands; the inner pipe is inside [...]
    assert len(parsed.commands) == 2


def test_triple_backtick_comment_is_captured():
    parsed = parse("index=main ```a comment``` | stats count")
    assert len(parsed.comments) == 1
    assert "a comment" in parsed.comments[0].text


def test_offset_to_position_multiline():
    parsed = parse("index=main\n| join type=inner host [ search x ]")
    join_cmd = parsed.commands[1]
    assert join_cmd.position.line == 2
