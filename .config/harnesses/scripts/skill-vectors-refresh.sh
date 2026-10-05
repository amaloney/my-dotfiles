#!/usr/bin/env bash
# Rebuild the skill vector index when skills change.
# Skips fast unless a SKILL.md is newer than the last build; also debounced.
# Non-fatal: hook callers must never break on rebuild failure.
set -o nounset

SKILLS="$HOME/.config/harnesses/skills"
VECTORS="$HOME/.config/harnesses/vectors"
STAMP="$VECTORS/.last_build"
DEBOUNCE=600

now=$(date +%s)
if [[ -f "$STAMP" ]] && (( now - $(cat "$STAMP") < DEBOUNCE )); then
    exit 0
fi

# Rebuild only if a skill file changed since the last build
if [[ -f "$STAMP" ]] && ! find "$SKILLS" -name "SKILL.md" -newer "$STAMP" 2>/dev/null | grep -q .; then
    exit 0
fi

if ! python3 -c "import chromadb, sentence_transformers" 2>/dev/null; then
    echo "harness: chromadb/sentence_transformers missing — skill vectors skipped" >&2
    exit 0
fi

mkdir -p "$VECTORS"
if python3 "$HOME/.config/harnesses/scripts/build_skill_vectors.py" --rebuild >/dev/null 2>&1; then
    date +%s > "$STAMP"
    echo "harness: skill vectors rebuilt"
else
    echo "harness: skill vector rebuild failed" >&2
fi
exit 0
