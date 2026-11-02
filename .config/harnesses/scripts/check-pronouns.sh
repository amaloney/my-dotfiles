#!/usr/bin/env bash
# MessageDisplay hook: flag first-person pronouns in Claude's reply text (read from stdin).
# Exit 1 with up to 3 highlighted lines on stderr when any are found; exit 0 otherwise.
set -o errexit -o nounset -o pipefail

readonly BANNED='\b(I|I'\''ll|I'\''ve|I'\''m|I'\''d|Let me|me to|my |mine)\b'

main() {
    local input
    input=$(cat)

    if grep --quiet --ignore-case --extended-regexp "$BANNED" <<< "$input"; then
        echo "⚠️  First-person pronoun violation detected" >&2
        grep --ignore-case --extended-regexp --color=always "$BANNED" <<< "$input" | head -3 >&2 || true
        exit 1
    fi
}

main "$@"
