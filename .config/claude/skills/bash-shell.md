---
name: bash-shell
description: Gotchas, patterns, and best practices for POSIX/bash shell scripts (.sh)
invocation: auto
---

# Bash/POSIX Shell

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

## Variables & Expansion

| Syntax                              | Effect                     |
| ----------------------------------- | -------------------------- |
| `${var:-default}`                   | Use default if unset/empty |
| `${var:=default}`                   | Set and use default        |
| `${var?error}`                      | Exit with error if unset   |
| `local`, `export`, `readonly`       | Scope modifiers            |
| `${#str}`, `${str:0:5}`             | Length, substring          |
| `${str/old/new}`, `${str//old/new}` | Replace first/all          |
| `${str#prefix}`, `${str%suffix}`    | Remove prefix/suffix       |

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

| Pattern                     | Fix                                         |
| --------------------------- | ------------------------------------------- |
| `cd` can fail               | `cd "$dir" \|\| exit 1`                     |
| Glob no match stays literal | `shopt -s nullglob`                         |
| Check command exists        | `command -v git &>/dev/null \|\| exit 1`    |
| Temp file cleanup           | `temp=$(mktemp); trap 'rm -f "$temp"' EXIT` |

## POSIX vs Bash

| Feature                | POSIX | Bash |
| ---------------------- | ----- | ---- |
| `[[ ]]`, arrays, `<<<` | No    | Yes  |
| `=~` regex             | No    | Yes  |

## jq (JSON)

```bash
jq '.key'                            # Extract key
jq -r '.name'                        # Raw output (no quotes)
jq '.items[]'                        # Iterate array
jq '.items[] | select(.active)'      # Filter
jq -s '.'                            # Slurp lines → array
jq --arg v "$var" '.key = $v'        # Inject shell var
echo '{}' | jq '.new = "val"'        # Add field
```

## xargs/parallel

```bash
find . -name "*.log" | xargs rm -f             # Batch delete
find . -name "*.sh" -print0 | xargs -0 chmod +x  # Null-delimited (spaces safe)
cat urls.txt | xargs -P4 -I{} curl -sO {}      # Parallel downloads
seq 10 | xargs -P4 -I{} bash -c 'process {}'   # Parallel jobs
```

## Process/Signals

```bash
trap 'rm -f "$tmpfile"; exit' EXIT INT TERM    # Cleanup on exit/ctrl-c
cmd & pid=$!; wait $pid                        # Background + wait
kill -0 $pid 2>/dev/null && echo "running"     # Check if alive
timeout 30 long_cmd                            # Kill after 30s
nohup cmd > out.log 2>&1 &                     # Detach from terminal
```

## curl

```bash
curl -sSfL "$url"                              # Silent, fail on error, follow redirects
curl -X POST -H "Content-Type: application/json" -d '{"k":"v"}' "$url"
curl -o file.zip -w "%{http_code}" "$url"      # Save + print status
curl --retry 3 --retry-delay 2 "$url"          # Retry logic
```

## awk/sed

```bash
awk '{print $2}'                               # 2nd column
awk -F: '{print $1}'                           # Custom delimiter
awk '/pattern/ {print}'                        # Filter lines
sed 's/old/new/g'                              # Replace all
sed -i.bak 's/old/new/g' file                  # In-place with backup
sed -n '10,20p' file                           # Print lines 10-20
```

## CI/CD Shell

```bash
set -o errexit -o nounset -o pipefail          # Always in CI scripts
[[ -n "${CI:-}" ]] && echo "::group::Step"     # GitHub Actions grouping
echo "::error file=f.sh,line=10::msg"          # GHA annotations
echo "VAR=value" >> "$GITHUB_ENV"              # Set env for next steps
```

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
