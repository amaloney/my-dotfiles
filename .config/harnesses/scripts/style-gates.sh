#!/usr/bin/env bash
# style-gates.sh — review-time style gates for Python files, one command.
#
# Runs every gate the python skill family documents as prose (the leaves teach
# the rules; this script is the enforcement mirror):
#   ruff | cryptic abbreviations | single-letter bindings | relative imports
#   | underscore module functions | ast structure check
#
# Findings print as `file:line: <gate>: <text>`. Exit 1 = violations found.
# Inline suppression: append `# naming:allow` to a line to exempt it from the
# grep gates (use sparingly; the greps are deliberately text-based).
#
# Usage: style-gates.sh <file-or-dir>...
set -o errexit -o nounset -o pipefail

# --- Gate patterns (single source; python/naming + python/structure mirror these) ---
CRYPTIC_PATTERN='\b(rec|req|resp|fh|exc|ret|hdr|buf)\b'
SINGLE_LETTER_PATTERNS=(
  '\bfor [a-z] in\b'
  '\bfor [a-z],'
  '\blambda [a-z][,:)]'
)
RELATIVE_IMPORT_PATTERN='^[[:space:]]*from \.'
UNDERSCORE_FUNC_PATTERN='^def _[a-zA-Z]'
SUPPRESSION_MARKER='# naming:allow'
AST_CHECKER="$HOME/.config/harnesses/skills/ast-check/scripts/ast_checker.py"

findings=0
note() {
  printf '%s\n' "$1"
  findings=$((findings + 1))
}

if [[ $# -eq 0 ]]; then
  printf 'usage: style-gates.sh <file-or-dir>...\n' >&2
  exit 2
fi

# Expand args into a list of .py files (directories are walked recursively).
shopt -s nullglob
files=()
for arg in "$@"; do
  if [[ -d "$arg" ]]; then
    while IFS= read -r py_file; do
      files+=("$py_file")
    done < <(find "$arg" -name '*.py' -type f)
  elif [[ -f "$arg" ]]; then
    files+=("$arg")
  else
    printf 'style-gates: no such file or directory: %s\n' "$arg" >&2
    exit 2
  fi
done
if [[ ${#files[@]} -eq 0 ]]; then
  printf 'style-gates: no .py files under the given paths\n'
  exit 0
fi

# --- ruff (warn-and-skip when absent: the script must not become the silent gap) ---
if command -v ruff &>/dev/null; then
  ruff_status=0
  ruff_output=$(ruff check "${files[@]}" 2>&1) || ruff_status=$?
  if [[ $ruff_status -ne 0 ]]; then
    printf '%s\n' "$ruff_output"
    findings=$((findings + 1))
  fi
else
  printf 'WARN: ruff not found on PATH — ruff gate skipped\n'
fi

# --- grep gates (skip lines carrying the suppression marker) ---
grep_gate() {
  local gate_name="$1" pattern="$2"
  local file matches
  for file in "${files[@]}"; do
    matches=$(grep -nE "$pattern" "$file" | grep -v -F "$SUPPRESSION_MARKER") || true
    if [[ -n "$matches" ]]; then
      while IFS= read -r match_line; do
        note "$file:$gate_name: $match_line"
      done <<< "$matches"
    fi
  done
}

grep_gate cryptic-abbreviation "$CRYPTIC_PATTERN"
for single_letter_pattern in "${SINGLE_LETTER_PATTERNS[@]}"; do
  grep_gate single-letter-binding "$single_letter_pattern"
done
grep_gate relative-import "$RELATIVE_IMPORT_PATTERN"
grep_gate underscore-module-function "$UNDERSCORE_FUNC_PATTERN"

# --- ast structure check (needs a >=3.10 interpreter; ast_checker uses PEP 604 unions at runtime) ---
ast_python=""
for candidate in python3 python3.13 python3.12 python3.11 python3.10; do
  if command -v "$candidate" &>/dev/null &&
    "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' &>/dev/null; then
    ast_python="$candidate"
    break
  fi
done
if [[ -n "$ast_python" && -f "$AST_CHECKER" ]]; then
  for arg in "$@"; do
    if [[ -d "$arg" || -f "$arg" ]]; then
      ast_status=0
      ast_output=$("$ast_python" "$AST_CHECKER" --check structure "$arg" 2>&1) || ast_status=$?
      if [[ $ast_status -ne 0 ]]; then
        printf '%s\n' "$ast_output"
        findings=$((findings + 1))
      fi
    fi
  done
elif [[ -z "$ast_python" ]]; then
  printf 'WARN: no python >= 3.10 found — ast structure gate skipped\n'
else
  printf 'WARN: ast_checker not found at %s — ast structure gate skipped\n' "$AST_CHECKER"
fi

# --- verdict ---
if [[ $findings -gt 0 ]]; then
  printf 'style-gates: %s finding(s) — fix or suppress with %s\n' "$findings" "$SUPPRESSION_MARKER"
  exit 1
fi
printf 'style-gates: clean (%s file(s))\n' "${#files[@]}"