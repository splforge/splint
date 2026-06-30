from splint.cli import EXIT_ERROR, EXIT_ISSUES, EXIT_OK, main


def test_cli_clean_file_exits_zero(tmp_path, capsys):
    f = tmp_path / "ok.spl"
    f.write_text("index=main | stats count", encoding="utf-8")
    assert main([str(f)]) == EXIT_OK


def test_cli_dirty_file_exits_one(tmp_path, capsys):
    f = tmp_path / "bad.spl"
    f.write_text("index=* | join x [ search y ]", encoding="utf-8")
    assert main([str(f)]) == EXIT_ISSUES
    out = capsys.readouterr().out
    assert "SPL001" in out


def test_cli_json_format(tmp_path, capsys):
    f = tmp_path / "bad.spl"
    f.write_text("index=* | stats count", encoding="utf-8")
    main([str(f), "--format", "json"])
    out = capsys.readouterr().out
    assert '"code": "SPL001"' in out


def test_cli_missing_path_is_error(capsys):
    assert main([]) == EXIT_ERROR


def test_cli_select_flag(tmp_path, capsys):
    f = tmp_path / "bad.spl"
    f.write_text("index=*|stats count", encoding="utf-8")
    main([str(f), "--select", "SPL101"])
    out = capsys.readouterr().out
    assert "SPL101" in out
    assert "SPL001" not in out
