---
name: bash-shell
description: Gotchas, patterns, and best practices for POSIX/bash shell scripts (.sh)
invocation: auto
---

# Bash/POSIX Shell

Handoff: `next: done`.

**Strict mode**: `set -o errexit -o nounset -o pipefail` **Shebang**: `#!/usr/bin/env bash` | **Flags**: Prefer
spelled-out (`curl --silent --fail`)

## Quoting (#1 Bug Source)

```bash
rm "$file"                       # Always quote vars
cd "$dir" || exit 1              # cd can fail
for f in "${files[@]}"; do       # Arrays: preserve boundaries
if [[ $var == "value" ]]; then   # Bash: [[ ]] handles empty/spaces
if [ "$var" = "value" ]; then    # POSIX: requires quotes
```

## Loops

```bash
for f in *; do [[ -e "$f" ]] || continue; done           # Files (NOT: for f in $(ls))
while IFS= read -r line; do echo "$line"; done < "$file" # Lines from file
# GOTCHA: Pipes create subshells - vars don't persist (use < redirect instead)
```

## Commands & Functions

```bash
output=$(command); exit_code=$?    # Capture output, check immediately
myfunc() { local r="val"; echo "$r"; return 0; }  # Return via stdout
command > file 2>&1                # Both to file (order matters!)
cat << 'EOF'                       # Here-doc, 'EOF' = no expansion
```

## Common Gotchas

| Pattern                     | Fix                                         |
| --------------------------- | ------------------------------------------- |
| `cd` can fail               | `cd "$dir" \|\| exit 1`                     |
| Glob no match stays literal | `shopt -s nullglob`                         |
| Check command exists        | `command -v git &>/dev/null \|\| exit 1`    |
| Temp file cleanup           | `temp=$(mktemp); trap 'rm -f "$temp"' EXIT` |

## Tool Search

`rg` > grep (`-P` PCRE, `-U` multiline) · `fd` > find · `jq` for JSON

## Scratch Files

- Scratch outputs (scripts, fetched pages) → `.scratch/<task>/`; `<task>` = short task name
- Adhoc code: write to file, then run. Never `python -c` inline
- Fetched web results → `.scratch/research/`: save as PDF (visual fidelity for human review) + markdown (agent consumption)
- Ensure `.scratch/.gitignore` exists with `**/*`

## CI/CD Shell

```bash
set -o errexit -o nounset -o pipefail          # Always in CI scripts
[[ -n "${CI:-}" ]] && echo "::group::Step"     # GitHub Actions grouping
echo "::error file=f.sh,line=10::msg"          # GHA annotations
echo "VAR=value" >> "$GITHUB_ENV"              # Set env for next steps
```

## References

| Reference                    | Contents                                 |
| ---------------------------- | ---------------------------------------- |
| references/variables.md      | Variables & expansion, arrays, POSIX vs Bash |
| references/jq.md             | jq JSON patterns                         |
| references/processes.md      | xargs/parallel, process/signals          |
| references/text-and-http.md  | curl, awk/sed                            |
| references/template.md       | Script boilerplate template              |
