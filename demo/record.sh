#!/usr/bin/env bash
#
# splint demo — designed to be recorded with asciinema and turned into a GIF.
#
#   asciinema rec splint.cast -c "./demo/record.sh"
#   agg splint.cast docs/demo.gif --theme monokai --font-size 22
#
# Run it standalone first (just `./demo/record.sh`) to check the timing.
# Requires `splint` on PATH (`pip install -e .`). Falls back to `python -m splint`.

set -euo pipefail

# --- config ------------------------------------------------------------------
TYPE_SPEED=${TYPE_SPEED:-0.035}   # seconds per character
PAUSE=${PAUSE:-1.4}               # pause after each command's output
PROMPT="\033[1;32m$\033[0m "      # green "$ "

SPLINT="splint"
command -v splint >/dev/null 2>&1 || SPLINT="python -m splint"

# --- helpers -----------------------------------------------------------------
type_out() {
  # Print a string with a typewriter effect.
  local text="$1"
  for ((i = 0; i < ${#text}; i++)); do
    printf '%s' "${text:$i:1}"
    sleep "$TYPE_SPEED"
  done
  printf '\n'
}

run() {
  # Show the prompt, "type" the command, run it, then pause.
  printf '%b' "$PROMPT"
  type_out "$1"
  eval "$1" || true
  sleep "$PAUSE"
  printf '\n'
}

say() {
  # A commented "narration" line in dim text.
  printf '\033[2m# %s\033[0m\n' "$1"
  sleep "$PAUSE"
}

clear 2>/dev/null || printf '\033[2J\033[H'
sleep 0.6

# --- script ------------------------------------------------------------------
say "splint — a zero-dependency linter for Splunk SPL"
run "$SPLINT --version"

say "Here's a search with every bad habit in the book:"
run "cat demo/messy_search.spl"

say "Let splint find them:"
run "$SPLINT demo/messy_search.spl"

say "Machine-readable too — JSON and SARIF for CI:"
run "$SPLINT demo/messy_search.spl --format json | head -n 14"

say "A clean, well-bounded search passes (exit code 0):"
run "cat demo/clean_search.spl"
run "$SPLINT demo/clean_search.spl"

say "Drop it into pre-commit or CI and keep SPL fast by default."
sleep 1.5
