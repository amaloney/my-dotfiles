#!/usr/bin/env bash
# Bootstrap or refresh a repo's .harness/code_index.
# Tri-state: missing -> install; stale (>7 days) -> rebuild; current -> exit.
# Debounced: skips if a build ran in the last 10 minutes.
# Usage: harness-refresh.sh [repo_root]   (default: cwd)
set -o errexit -o nounset -o pipefail

ROOT="${1:-.}"
IDX="$ROOT/.harness/code_index"
SCRIPTS="$HOME/.config/harnesses/skills/code-index/scripts"
STAMP="$IDX/.last_build"
DEBOUNCE=600

# Not a git repo -> nothing to do
git -C "$ROOT" rev-parse --is-inside-work-tree &>/dev/null || exit 0

now=$(date +%s)
if [[ -f "$STAMP" ]] && (( now - $(cat "$STAMP") < DEBOUNCE )); then
    exit 0
fi

if [[ ! -d "$IDX" ]]; then
    echo "harness: bootstrapping .harness/code_index in $ROOT"
    "$SCRIPTS/install.sh" "$ROOT" >/dev/null
elif find "$IDX" -name "code_graph.db" -mtime +7 2>/dev/null | grep -q .; then
    echo "harness: index stale, rebuilding"
else
    exit 0
fi

if python3 -c "import chromadb" 2>/dev/null; then
    (cd "$IDX" && python3 build_index_temporal.py >/dev/null 2>&1) || echo "harness: index build failed"
    date +%s > "$STAMP"
else
    echo "harness: chromadb not installed — index skipped (pip install chromadb)"
fi
