#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

# Generate skill interconnectivity graph
# Usage: ./skill-graph.sh [output.png]
# Requires: graphviz (dot)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${SCRIPT_DIR}/../skills"
OUTPUT="${1:-${SCRIPT_DIR}/../skill-graph.png}"
DOT_FILE="${OUTPUT%.png}.dot"

command -v dot &>/dev/null || { echo "graphviz required: brew install graphviz" >&2; exit 1; }

{
echo 'digraph skills {'
echo '  rankdir=LR;'
echo '  node [shape=box, style=rounded, fontname="Helvetica"];'
echo '  edge [color="#666666"];'

# Process each skill file
find "$SKILLS_DIR" -name "*.md" -type f | while read -r file; do
    rel="${file#$SKILLS_DIR/}"
    name="${rel%.md}"
    node_id="${name//\//_}"
    label="${name##*/}"
    dir="$(dirname "$rel")"

    # Node with cluster prefix for grouping
    if [[ "$dir" != "." ]]; then
        echo "  \"$node_id\" [label=\"$label\"];"
    else
        echo "  \"$node_id\" [label=\"$name\", style=\"rounded,bold\"];"
    fi

    # Extract [[links]] and create edges (skill names: lowercase, hyphens, slashes only)
    { grep -oE '\[\[[a-z][a-z0-9/_-]*\]\]' "$file" 2>/dev/null || true; } | sed 's/\[\[\([^]]*\)\]\]/\1/g' | while read -r link; do
        [[ -n "$link" ]] || continue
        link_id="${link//\//_}"
        echo "  \"$node_id\" -> \"$link_id\";"
    done
done

echo '}'
} > "$DOT_FILE"

dot -Tpng "$DOT_FILE" -o "$OUTPUT"
echo "Generated: $OUTPUT"
echo "DOT source: $DOT_FILE"
