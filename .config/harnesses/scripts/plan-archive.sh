#!/usr/bin/env bash
# File Claude plan-mode plans by date: .harness/plans/.claude/<name>.md -> .harness/plans/<YYYY-MM-DD>/<name>.md
# Claude writes plans to the staging dir (settings.json "plansDirectory"); SessionEnd/SessionStart hooks call this.
# A plan already filed under some date (resumed or re-entered plan) replaces that copy, so one plan stays one file.
set -o errexit -o nounset -o pipefail
shopt -s nullglob

# Hooks must never block a session: whatever happens, exit 0 (an exit inside the EXIT trap sets the final status)
trap 'exit 0' EXIT

readonly STAGING_REL=".harness/plans/.claude"
readonly PLANS_REL=".harness/plans"

usage() {
    cat << EOF
Usage: $(basename "$0") [--min-age <age>] [--dry-run] [project-dir]

File staged Claude plans into $PLANS_REL/<YYYY-MM-DD>/<name>.md.

  project-dir      default: \$CLAUDE_PROJECT_DIR, then the hook's JSON "cwd" on stdin, then \$PWD
  --min-age <age>  only file plans unchanged for <age> (e.g. 12h, 30m, 90s, 3600)
  --dry-run        print what would move, change nothing
  -h, --help       show this help
EOF
}

log() { echo "plans: $*" >&2; }

# "12h" / "30m" / "90s" / "3600" -> seconds on stdout; non-zero for anything else
to_seconds() {
    local value="$1"
    [[ "$value" =~ ^([0-9]+)([hms]?)$ ]] || return 1
    local number="${BASH_REMATCH[1]}"
    case "${BASH_REMATCH[2]}" in
        h) echo $(( number * 3600 )) ;;
        m) echo $(( number * 60 )) ;;
        *) echo "$number" ;;
    esac
}

# The hook's JSON input on stdin carries "cwd"; nothing when run by hand from a terminal
hook_cwd() {
    [[ -t 0 ]] && return 0
    jq --raw-output '.cwd // empty' 2>/dev/null || true
}

# Creation date (stat %W; 0 when the filesystem doesn't record it), else modification date
plan_date() {
    local file="$1"
    local born
    born=$(stat --format=%W "$file" 2>/dev/null || echo 0)
    if [[ "$born" =~ ^[0-9]+$ ]] && (( born > 0 )); then
        date --date="@$born" +%F
    else
        date --reference="$file" +%F
    fi
}

# Where a plan belongs: its existing dated copy if there is one, else a folder named after its creation date
plan_destination() {
    local plans_dir="$1"
    local plan="$2"
    local name
    name=$(basename "$plan")

    local existing=("$plans_dir"/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/"$name")
    if (( ${#existing[@]} > 0 )); then
        echo "${existing[0]}"
        return 0
    fi
    # Separate assignment so a failed date lookup fails here instead of yielding "$plans_dir//$name"
    local day
    day=$(plan_date "$plan") || return 1
    [[ -n "$day" ]] || return 1
    echo "$plans_dir/$day/$name"
}

is_recent() {
    local file="$1"
    local min_age_seconds="$2"
    local modified now
    modified=$(stat --format=%Y "$file")
    now=$(date +%s)
    (( now - modified < min_age_seconds ))
}

file_plan() {
    local plans_dir="$1"
    local plan="$2"
    local dry_run="$3"
    local dest
    dest=$(plan_destination "$plans_dir" "$plan") || return 1

    if [[ "$dry_run" == true ]]; then
        echo "would file: $plan -> $dest"
        return 0
    fi
    # Explicit returns: the caller's `||` turns off errexit inside this function
    mkdir --parents "$(dirname "$dest")" || return 1
    mv --force "$plan" "$dest" || return 1
    log "filed $(basename "$plan") -> ${dest#"$plans_dir"/}"
}

main() {
    local min_age_seconds=0
    local dry_run=false
    local project_dir=""

    while (( $# > 0 )); do
        case "$1" in
            -h|--help) usage; return 0 ;;
            --dry-run) dry_run=true; shift ;;
            --min-age)
                [[ $# -ge 2 ]] || { log "--min-age needs a value"; usage >&2; return 1; }
                min_age_seconds=$(to_seconds "$2") || { log "bad --min-age: $2"; return 1; }
                shift 2
                ;;
            -*) log "unknown option: $1"; usage >&2; return 1 ;;
            *) project_dir="$1"; shift ;;
        esac
    done

    if [[ -z "$project_dir" ]]; then
        project_dir="${CLAUDE_PROJECT_DIR:-}"
    fi
    if [[ -z "$project_dir" ]]; then
        project_dir=$(hook_cwd)
    fi
    project_dir="${project_dir:-$PWD}"

    local plans_dir="$project_dir/$PLANS_REL"
    local plan
    for plan in "$project_dir/$STAGING_REL"/*.md; do
        if (( min_age_seconds > 0 )) && is_recent "$plan" "$min_age_seconds"; then
            continue
        fi
        file_plan "$plans_dir" "$plan" "$dry_run" || log "could not file $plan"
    done
}

main "$@"
