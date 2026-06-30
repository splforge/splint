# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- `SPL002` (leading-wildcard) is now severity `info` and only applies to the
  base search, where leading wildcards actually defeat index/term retrieval.
  Validated against the `splunk/security_content` corpus (2114 detections),
  where leading wildcards are overwhelmingly intentional path/command-line
  matches.

### Fixed

- `SPL101` (pipe-spacing) no longer flags a leading pipe (`| tstats ...`),
  which is valid SPL; only the spacing *after* such a pipe is checked. This
  removed ~1070 false positives on the `security_content` corpus.

## [0.1.0] - 2026-06-25

### Added

- Initial release of **splint**, a zero-dependency linter for Splunk SPL.
- Tolerant SPL pipeline parser (handles quoted strings, `[...]` subsearches, and
  ` ``` comments ``` `).
- Performance rules: `SPL001` (index wildcard), `SPL002` (leading wildcard),
  `SPL003` (`join` usage), `SPL004` (`transaction` usage), `SPL005` (unbounded `sort`).
- Style rule: `SPL101` (space around pipe `|`).
- Reporters: `text`, `json`, `sarif`.
- CLI with `--select`/`--ignore`, `--format`, `--config`, exit codes.
- Inline suppression via `noqa` SPL comments (` ``` noqa: SPL003 ``` `).
- Configuration via `.spl-lint.toml` or the `[tool.splint]` table in `pyproject.toml`.
- GitHub Actions CI matrix (3.11 / 3.12 / 3.13) and tag-triggered PyPI release via OIDC.
- `pre-commit` hook definition.

[Unreleased]: https://github.com/kevinbelon/splint/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kevinbelon/splint/releases/tag/v0.1.0
