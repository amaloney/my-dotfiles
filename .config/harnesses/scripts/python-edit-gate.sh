#!/usr/bin/env bash
# Claude Code hook for .py edits: small edits happen in place and are checked in code; big ones go to a subagent.
# A subagent costs >10k tokens before it starts, so only changes big enough to need a fresh context are delegated.
#   --before (PreToolUse,  matcher Edit|Write|MultiEdit): block (exit 2) a new .py file or a change over the limit
#   --after  (PostToolUse, same matcher): run style-gates.sh on the file; findings -> exit 2 so Claude fixes them
# Exit 2 shows stderr to Claude. Anything this script can't evaluate is allowed (exit 0): a hook bug must not block work.
# Overrides: ALLOW_DIRECT_PYTHON_EDIT=1 skips the size check; PY_EDIT_MAX_LINES sets the limit (default 40).
set -o errexit -o nounset -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
readonly STYLE_GATES="$SCRIPT_DIR/style-gates.sh"
readonly MAX_LINES="${PY_EDIT_MAX_LINES:-40}"

usage() {
    cat << EOF
Usage: $(basename "$0") --before|--after < hook-input.json
EOF
}

line_count() {
    local text="$1"
    [[ -n "$text" ]] || { echo 0; return 0; }
    printf '%s\n' "$text" | wc -l
}

# Lines changed by Edit/MultiEdit: per edit, the larger of the old and new text
edit_lines() {
    local input="$1"
    local total=0 edit old_text new_text old_lines new_lines
    while IFS= read -r edit; do
        old_text=$(jq --raw-output '.old_string // ""' <<< "$edit")
        new_text=$(jq --raw-output '.new_string // ""' <<< "$edit")
        old_lines=$(line_count "$old_text")
        new_lines=$(line_count "$new_text")
        total=$(( total + (old_lines > new_lines ? old_lines : new_lines) ))
    done < <(jq --compact-output '.tool_input | if .edits then .edits[] else . end' <<< "$input")
    echo "$total"
}

# Lines changed by Write over an existing file: lines removed or added, whichever is larger
write_lines() {
    local file="$1"
    local content="$2"
    local removed added
    removed=$(diff "$file" - <<< "$content" | grep --count '^<' || true)
    added=$(diff "$file" - <<< "$content" | grep --count '^>' || true)
    echo $(( removed > added ? removed : added ))
}

delegate() {
    local reason="$1"
    cat >&2 << EOF
BLOCKED: $reason
Delegate it: Agent(subagent_type "code-hygiene" for a focused change, "bug" for the full pipeline).
Small edits (up to $MAX_LINES lines) are fine in place: they are checked automatically by style-gates.sh.
To lift the limit, the user starts the session with ALLOW_DIRECT_PYTHON_EDIT=1.
EOF
    exit 2
}

before_edit() {
    local input="$1"
    local file="$2"
    local tool changed

    [[ -z "$(jq --raw-output '.agent_id // empty' <<< "$input")" ]] || return 0
    [[ "${ALLOW_DIRECT_PYTHON_EDIT:-}" != 1 ]] || return 0

    tool=$(jq --raw-output '.tool_name // empty' <<< "$input")
    case "$tool" in
        Write)
            [[ -f "$file" ]] || delegate "new Python file $file"
            changed=$(write_lines "$file" "$(jq --raw-output '.tool_input.content // ""' <<< "$input")")
            ;;
        Edit|MultiEdit)
            changed=$(edit_lines "$input")
            ;;
        *)
            return 0
            ;;
    esac

    if (( changed > MAX_LINES )); then
        delegate "$tool changes $changed lines of $file (limit $MAX_LINES)"
    fi
}

after_edit() {
    local file="$1"
    local output status=0

    [[ -f "$file" && -x "$STYLE_GATES" ]] || return 0
    output=$("$STYLE_GATES" "$file" 2>&1) || status=$?
    if (( status == 1 )); then
        printf 'style-gates found problems in %s; fix them now:\n%s\n' "$file" "$output" >&2
        exit 2
    fi
}

main() {
    local mode="${1:-}"
    case "$mode" in
        --before|--after) ;;
        -h|--help) usage; return 0 ;;
        *) usage >&2; return 0 ;;
    esac

    local input file
    input=$(cat)
    file=$(jq --raw-output '.tool_input.file_path // empty' <<< "$input" 2>/dev/null) || return 0
    [[ "$file" == *.py ]] || return 0

    if [[ "$mode" == --before ]]; then
        before_edit "$input" "$file"
    else
        after_edit "$file"
    fi
}

main "$@"
