---
name: bash-shell
description: Gotchas, patterns, and best practices for POSIX/bash shell scripts (.sh)
invocation: auto
---

# Bash/POSIX Shell

**Strict mode**: `set -o errexit -o nounset -o pipefail`
**Shebang**: `#!/usr/bin/env bash` | **Flags**: Prefer spelled-out (`curl --silent --fail`)

## Quoting (#1 Bug Source)

```bash
rm "$file"                       # Always quote vars
cd "$dir" || exit 1              # cd can fail
for f in "${files[@]}"; do       # Arrays: preserve boundaries
if [[ $var == "value" ]]; then   # Bash: [[ ]] handles empty/spaces
if [ "$var" = "value" ]; then    # POSIX: requires quotes
```

## Variables & Expansion

| Syntax | Effect |
|--------|--------|
| `${var:-default}` | Use default if unset/empty |
| `${var:=default}` | Set and use default |
| `${var?error}` | Exit with error if unset |
| `local`, `export`, `readonly` | Scope modifiers |
| `${#str}`, `${str:0:5}` | Length, substring |
| `${str/old/new}`, `${str//old/new}` | Replace first/all |
| `${str#prefix}`, `${str%suffix}` | Remove prefix/suffix |

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

## Arrays (Bash)

```bash
arr=("one" "two"); echo "${arr[0]}" "${arr[@]}" "${#arr[@]}"  # First, all, length
declare -A map; map[key]="value"   # Associative (bash 4+)
```

## Common Gotchas

| Pattern | Fix |
|---------|-----|
| `cd` can fail | `cd "$dir" \|\| exit 1` |
| Glob no match stays literal | `shopt -s nullglob` |
| Check command exists | `command -v git &>/dev/null \|\| exit 1` |
| Temp file cleanup | `temp=$(mktemp); trap 'rm -f "$temp"' EXIT` |

## POSIX vs Bash

| Feature | POSIX | Bash |
|---------|-------|------|
| `[[ ]]`, arrays, `<<<` | No | Yes |
| `=~` regex | No | Yes |

## Template

```bash
#!/bin/bash
set -o errexit -o nounset -o pipefail
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() { cat << EOF
Usage: $(basename "$0") [options] <arg>
EOF
}

main() {
    case "${1:-}" in -h|--help) usage; exit 0 ;; esac
    [[ $# -ge 1 ]] || { usage >&2; exit 1; }
}
main "$@"
```
