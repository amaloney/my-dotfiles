#!/bin/bash
# Hook: check for banned first-person pronouns in Claude responses
# Returns non-zero if violations found

# Patterns to check (word boundaries)
BANNED='\b(I|I'\''ll|I'\''ve|I'\''m|I'\''d|Let me|me to|my |mine)\b'

# Read from stdin (response text)
input=$(cat)

if echo "$input" | grep -qiE "$BANNED"; then
    echo "⚠️  First-person pronoun violation detected" >&2
    echo "$input" | grep -iE --color=always "$BANNED" | head -3 >&2
    exit 1
fi

exit 0
