# splint

[![CI](https://github.com/splforge/splint/actions/workflows/ci.yml/badge.svg)](https://github.com/splforge/splint/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/splint-spl.svg)](https://pypi.org/project/splint-spl/)
[![Python](https://img.shields.io/pypi/pyversions/splint-spl.svg)](https://pypi.org/project/splint-spl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

![splint in action](docs/demo.gif)

A fast, **zero-dependency** linter for Splunk SPL searches.

`splint` catches the performance anti-patterns and style slips that creep into
SPL — broad index wildcards, leading wildcards, expensive `join`/`transaction`,
unbounded `sort` — before they hit production. It runs anywhere Python 3.11+
runs, has no runtime dependencies, and plugs straight into `pre-commit` and CI.

It's been run against the entire [`splunk/security_content`](https://github.com/splunk/security_content)
detection library (2,000+ real searches) to keep its rules signal-rich and its
false-positive rate low.

```console
$ splint examples/sample.spl
examples/sample.spl:1:1: SPL001 `index=*` uses a wildcard; specify explicit indexes to avoid scanning every index.
examples/sample.spl:1:41: SPL002 `user=*admin` has a leading wildcard, which disables efficient term lookups.
examples/sample.spl:2:2: SPL003 `join` is costly and caps subsearch results (default 50k); consider `stats`, `eventstats`, or a `lookup` instead.
examples/sample.spl:3:2: SPL004 `transaction` is memory-intensive and not distributable; prefer `stats` grouped by a correlation field when possible.
examples/sample.spl:4:2: SPL005 `sort` has no limit; add a count (e.g. `sort 100 -_time`) to cap memory and runtime.

Found 5 issues.
```

## Install

Requires Python 3.11+. Works on Linux, macOS and Windows — it's pure Python with
no compiled extensions or runtime dependencies.

```console
pip install splint-spl
```

Or, to keep it isolated as a standalone CLI:

```console
pipx install splint-spl
```

## Usage

```console
splint query.spl                 # lint one or more files
splint *.spl                     # globs work
cat query.spl | splint -         # read from stdin
splint query.spl --format json   # text | json | sarif
splint query.spl --select SPL001,SPL003
splint query.spl --ignore SPL101
```

Exit codes: `0` no issues, `1` issues found, `2` usage/IO error — ideal for CI.

## Rules

| Code   | Name              | Severity | What it flags |
|--------|-------------------|----------|---------------|
| SPL001 | index-wildcard    | warning  | Wildcards in the `index=` specifier (`index=*`, `index=win*`) |
| SPL002 | leading-wildcard  | info     | Field values starting with `*` in the base search (`user=*admin`) |
| SPL003 | join-usage        | warning  | `join` command (expensive, silently truncates) |
| SPL004 | transaction-usage | warning  | `transaction` command (memory-heavy, non-distributable) |
| SPL005 | unbounded-sort    | warning  | `sort` without a row count or `limit=` |
| SPL101 | pipe-spacing      | info     | Missing space around the `\|` pipe |

## Inline suppression

Use an SPL triple-backtick comment containing `noqa` on the offending line —
a bare `noqa` silences every rule on that line, or list specific codes:

~~~spl
index=* | stats count   ```noqa```           « suppress everything on this line »
index=* | stats count   ```noqa: SPL001```   « suppress only SPL001 »
~~~

## Configuration

`splint` reads `.spl-lint.toml` (whole file) or a `[tool.splint]` table in
`pyproject.toml`:

```toml
[tool.splint]
select = ["SPL001", "SPL002", "SPL003", "SPL004", "SPL005"]
ignore = ["SPL101"]
```

CLI `--select` / `--ignore` override the config file.

## pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/splforge/splint
    rev: v0.1.0
    hooks:
      - id: splint
```

## Development

```console
pip install -e ".[dev]"
ruff check .
pytest
```

## License

MIT © splforge
