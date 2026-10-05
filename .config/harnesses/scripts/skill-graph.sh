#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

# Generate skill interconnectivity graph
# Usage: ./skill-graph.sh [--check | --dependents <skill>] [output.png]
# Requires: graphviz (dot) for graph generation; --check/--dependents need only grep/find

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${SCRIPT_DIR}/../skills"
AGENTS_MD="${SCRIPT_DIR}/../AGENTS.md"

MODE="graph"
if [[ "${1:-}" == "--check" ]]; then
    MODE="check"
    shift
elif [[ "${1:-}" == "--dependents" ]]; then
    MODE="dependents"
    shift
    TARGET="${1:?usage: skill-graph.sh --dependents <skill>}"
fi
OUTPUT="${1:-${SCRIPT_DIR}/../skill-graph.png}"
DOT_FILE="${OUTPUT%.png}.dot"

skill_dirs() {
    find "$SKILLS_DIR" -name "SKILL.md" -type f | while read -r file; do
        rel="${file#$SKILLS_DIR/}"
        dirname "$rel"
    done | sort
}

skill_links() {
    { grep -oE '\[\[[a-z][a-z0-9/_-]*\]\]' "$1" 2>/dev/null || true; } | sed 's/\[\[\([^]]*\)\]\]/\1/g'
}

if [[ "$MODE" == "dependents" ]]; then
    # Reverse lookup: who points at TARGET, and via which edge type
    found=0
    while read -r file; do
        rel="${file#$SKILLS_DIR/}"
        src="$(dirname "$rel")"
        [[ "$src" == "$TARGET" ]] && continue
        while read -r link; do
            if [[ "$link" == "$TARGET" ]]; then
                echo "LINK  $src -> [[$TARGET]]"
                found=1
            fi
        done < <(skill_links "$file")
        while read -r tgt; do
            if [[ "$tgt" == "$TARGET" ]]; then
                echo "NEXT  $src -> next: $TARGET"
                found=1
            fi
        done < <(grep -oE 'next: `?(\[\[)?[a-z0-9/_-]+' "$file" | sed -E 's/next: `?(\[\[)?//' || true)
    done < <(find "$SKILLS_DIR" -name "SKILL.md" -type f)
    if grep -qwF "$TARGET" "$AGENTS_MD"; then
        echo "ROUTE AGENTS.md routing table mentions $TARGET"
        found=1
    fi
    [[ "$found" -eq 0 ]] && echo "no dependents: $TARGET"
    exit 0
fi

if [[ "$MODE" == "check" ]]; then
    fail=0
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT
    skill_dirs > "$tmp/dirs"
    : > "$tmp/links"

    while read -r file; do
        rel="${file#$SKILLS_DIR/}"
        src="$(dirname "$rel")"
        while read -r link; do
            [[ -n "$link" ]] || continue
            if ! grep -qxF "$link" "$tmp/dirs" && [[ ! -f "$SKILLS_DIR/$link.md" && ! -d "$SKILLS_DIR/$link" ]]; then
                echo "DANGLING: $src -> [[$link]]"
                fail=1
            fi
            [[ "$link" != "$src" ]] && echo "$link" >> "$tmp/links"
        done < <(skill_links "$file")
    done < <(find "$SKILLS_DIR" -name "SKILL.md" -type f)

    # Orphans: no inbound link, no AGENTS.md routing entry, no next: verdict
    while read -r dir; do
        grep -qxF "$dir" "$tmp/links" && continue
        grep -qwF "$dir" "$AGENTS_MD" && continue
        if ! find "$SKILLS_DIR" -name "SKILL.md" -type f -print0 | xargs -0 grep -qE "next: \`?(\[\[)?${dir}([]]|\`|[[:space:].,]|$)"; then
            echo "ORPHAN: $dir"
            fail=1
        fi
    done < "$tmp/dirs"

    # Rank map from the handoff-contract Termination table (single owner)
    awk -F'|' '/^\| *[0-9]/ {
        rank=$2; gsub(/[[:space:]]/,"",rank); skills=$4
        while (match(skills, /`[^`]+`/)) {
            print substr(skills,RSTART+1,RLENGTH-2), rank
            skills=substr(skills,RSTART+RLENGTH)
        }
    }' "$SCRIPT_DIR/../handoff-contract.md" > "$tmp/ranks"

    rank_of() {
        awk -v s="$1" '$1==s { print $2; found=1; exit }
            END { if (!found) exit 1 }' "$tmp/ranks" && return 0
        awk -v s="$1" '$1 ~ /\*$/ { p=$1; sub(/\*$/,"",p); if (index(s,p)==1) { print $2; found=1; exit } }
            END { if (!found) exit 1 }' "$tmp/ranks"
    }

    # Handoff gates: terminal coverage + rank acyclicity
    while read -r file; do
        rel="${file#$SKILLS_DIR/}"
        src="$(dirname "$rel")"
        edges="$(grep -oE 'next: `?(\[\[)?[a-z0-9/_-]+' "$file" | sed -E 's/next: `?(\[\[)?//' || true)"
        if [[ -z "$edges" ]]; then
            echo "NO-HANDOFF: $src declares no next: verdict"
            fail=1
            continue
        fi
        while read -r tgt; do
            [[ "$tgt" == "done" ]] && continue
            rs="$(rank_of "$src")" || { echo "UNRANKED: $src (missing from rank table)"; fail=1; continue; }
            rt="$(rank_of "$tgt")" || { echo "UNRANKED: $tgt (target of $src, missing from rank table)"; fail=1; continue; }
            if (( rt <= rs )); then
                echo "RANK-VIOLATION: $src (rank $rs) -> $tgt (rank $rt)"
                fail=1
            fi
        done <<< "$edges"
    done < <(find "$SKILLS_DIR" -name "SKILL.md" -type f)

    if [[ "$fail" -eq 0 ]]; then
        echo "skill graph: connected (no dangling links, no orphans, handoffs acyclic, all skills terminate)"
    fi
    exit "$fail"
fi

command -v dot &>/dev/null || { echo "graphviz required: brew install graphviz" >&2; exit 1; }

{
echo 'digraph skills {'
echo '  rankdir=LR;'
echo '  node [shape=box, style=rounded, fontname="Helvetica"];'
echo '  edge [color="#666666"];'

# Process each skill file (dir/SKILL.md convention)
find "$SKILLS_DIR" -name "SKILL.md" -type f | while read -r file; do
    rel="${file#$SKILLS_DIR/}"
    name="$(dirname "$rel")"
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
    skill_links "$file" | while read -r link; do
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
