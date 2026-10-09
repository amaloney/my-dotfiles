#!/usr/bin/env bash
# Bootstrap or refresh a repo's .harness/code_index.
# Tri-state: missing -> install; stale (>7 days) -> rebuild; current -> exit.
# Debounced: skips if a build ran in the last 10 minutes.
# Usage: harness-refresh.sh [path]   (default: cwd; any path inside the repo resolves to its top level)
set -o errexit -o nounset -o pipefail

# Not a git repo -> nothing to do. Hooks fire from whatever cwd the shell is in, so a subdirectory must map to the
# repo root — otherwise every subdir gets its own stray .harness/
ROOT=$(git -C "${1:-.}" rev-parse --show-toplevel 2>/dev/null) || exit 0
IDX="$ROOT/.harness/code_index"
SCRIPTS="$HOME/.config/harnesses/skills/code-index/scripts"
STAMP="$IDX/.last_build"
DEBOUNCE=600

now=$(date +%s)
if [[ -f "$STAMP" ]] && (( now - $(cat "$STAMP") < DEBOUNCE )); then
    exit 0
fi

if [[ ! -d "$IDX" ]]; then
    echo "harness: bootstrapping .harness/code_index in $ROOT"
    "$SCRIPTS/install.sh" "$ROOT" >/dev/null
elif [[ ! -f "$IDX/code_graph.db" ]]; then
    echo "harness: index never built, building"
elif find "$IDX" -name "code_graph.db" -mtime +7 2>/dev/null | grep -q .; then
    echo "harness: index stale, rebuilding"
else
    exit 0
fi

# Prefer a pixi env's interpreter (called directly: no solve/install at startup),
# then fall back to system python3.
PYTHON=""
for candidate in "$ROOT/.pixi/envs/dev/bin/python" "$ROOT/.pixi/envs/default/bin/python" python3; do
    if "$candidate" -c "import chromadb" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [[ -n "$PYTHON" ]]; then
    (cd "$IDX" && "$PYTHON" build_index_temporal.py >/dev/null 2>&1) || echo "harness: index build failed"
    date +%s > "$STAMP"
else
    echo "harness: chromadb not installed — index skipped (add it to a pixi env: pixi add --feature dev chromadb)"
fi
