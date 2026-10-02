# Template

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
