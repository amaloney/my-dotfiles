#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

# Cleanup of Anaconda/Miniconda/Miniforge installations on Linux and macOS.
# Removes installation directories, leftover files, environment variables, and shell config.
# Configuration loaded from benothing.yaml (single source of truth)

readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CONFIG_FILE="$SCRIPT_DIR/benothing.yaml"

# Options
DRY_RUN=false
FORCE=false
SKIP_UNINSTALLER=false
NAME_FILTER=""

# Colors (disabled if not a terminal)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    CYAN='\033[0;36m'
    GRAY='\033[0;90m'
    RESET='\033[0m'
else
    RED='' GREEN='' YELLOW='' CYAN='' GRAY='' RESET=''
fi

# Parse YAML list into bash array (requires yq v4+)
# Usage: readarray -t ARRAY < <(yaml_list "key.subkey")
yaml_list() {
    local key="$1"
    if command -v yq &>/dev/null && [[ -f "$CONFIG_FILE" ]]; then
        yq -r ".$key[]? // empty" "$CONFIG_FILE" 2>/dev/null
    fi
}

# Load configuration from YAML or use defaults
load_config() {
    local os_type
    os_type="$(uname -s)"

    # Load from YAML if yq is available
    if command -v yq &>/dev/null && [[ -f "$CONFIG_FILE" ]]; then
        # Common (all platforms)
        readarray -t USER_PROFILE_ITEMS < <(yaml_list "common.user_profile_items")
        readarray -t USER_PROFILE_PATTERNS < <(yaml_list "common.user_profile_patterns")
        readarray -t ENV_VARS_TO_REMOVE < <(yaml_list "common.env_vars")

        # Build install dirs from common + unix
        local -a install_common
        readarray -t install_common < <(yaml_list "common.install_dirs")
        INSTALL_DIRS=()
        for dir in "${install_common[@]}"; do
            INSTALL_DIRS+=("$HOME/$dir")
        done
        local -a unix_install
        readarray -t unix_install < <(yaml_list "unix.install_dirs")
        INSTALL_DIRS+=("${unix_install[@]}")

        # System config dirs (unix)
        readarray -t SYSTEM_CONFIG_DIRS < <(yaml_list "unix.system_config_dirs")

        # User config dirs
        local -a user_config_names
        readarray -t user_config_names < <(yaml_list "common.user_config_dirs")
        USER_CONFIG_DIRS=()
        for name in "${user_config_names[@]}"; do
            USER_CONFIG_DIRS+=("${XDG_CONFIG_HOME:-$HOME/.config}/$name")
        done

        # Shell configs (to clean, not delete)
        local -a shell_config_names
        readarray -t shell_config_names < <(yaml_list "common.shell_configs_to_clean")
        SHELL_CONFIGS=()
        for name in "${shell_config_names[@]}"; do
            SHELL_CONFIGS+=("$HOME/$name")
        done

        # Unix (Linux + macOS)
        readarray -t LOCAL_BIN_PATTERNS < <(yaml_list "unix.local_bin_patterns")

        # Platform-specific
        case "$os_type" in
            Linux)
                readarray -t XDG_ITEMS < <(yaml_list "linux.xdg_items")
                ;;
            Darwin)
                readarray -t MACOS_LIBRARY < <(yaml_list "macos.library")
                readarray -t MACOS_APP_SUPPORT < <(yaml_list "macos.app_support")
                readarray -t MACOS_CACHES < <(yaml_list "macos.caches")
                ;;
        esac

        printf "${GREEN}Loaded configuration from %s${RESET}\n" "$CONFIG_FILE"
    else
        # Fallback to hardcoded defaults
        USER_PROFILE_ITEMS=(
            .anaconda .astropy .conda .condarc .continuum .copilot
            .ipynb_checkpoints .ipython .jupyter .matplotlib
            .python_history .virtual_documents
        )
        USER_PROFILE_PATTERNS=(".spyder*" ".anaconda*")  # WILDCARD: review with --dry-run
        INSTALL_DIRS=(
            "$HOME/anaconda3" "$HOME/miniconda3" "$HOME/miniforge3"
            "$HOME/mambaforge" "$HOME/anaconda" "$HOME/miniconda"
            "/opt/anaconda3" "/opt/miniconda3" "/opt/miniforge3"
            "/opt/mambaforge" "/opt/conda" "$HOME/.conda"
        )
        SYSTEM_CONFIG_DIRS=("/etc/conda" "/var/lib/conda")
        USER_CONFIG_DIRS=("${XDG_CONFIG_HOME:-$HOME/.config}/conda")
        # From: conda/core/initialize.py (make_initialize_plan)
        SHELL_CONFIGS=(
            "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"
            "$HOME/.zshrc" "$HOME/.zprofile"
            "$HOME/.config/fish/config.fish"
            "$HOME/.xonshrc" "$HOME/.tcshrc"
        )
        ENV_VARS_TO_REMOVE=(
            CONDA_DEFAULT_ENV CONDA_PREFIX CONDA_SHLVL CONDA_EXE
            CONDA_PYTHON_EXE CONDA_PROMPT_MODIFIER _CE_CONDA _CE_M
            CONDARC CONDA_ROOT_PREFIX CONDA_ENVS_DIRS CONDA_PKGS_DIRS
            CONDA_CHANNELS CONDA_SUBDIR CONDA_BLD_PATH CONDA_CHANGEPS1
            CONDA_ENV_PROMPT CONDA_AUTO_ACTIVATE_BASE CONDA_AUTO_STACK
            CONDA_AUTO_UPDATE_CONDA CONDA_ALWAYS_YES CONDA_DRY_RUN
            CONDA_QUIET CONDA_VERBOSITY CONDA_JSON CONDA_SSL_VERIFY
            CONDA_TOKEN CONDA_AUTH_USERNAME CONDA_AUTH_PASSWORD
            CONDA_SOLVER CONDA_EXPERIMENTAL_SOLVER CONDA_DEFAULT_THREADS
            CONDA_EXECUTE_THREADS CONDA_REPODATA_THREADS CONDA_VERIFY_THREADS
            CONDA_OFFLINE CONDA_CHANNEL_PRIORITY CONDA_CHANNEL_ALIAS
            CONDA_SAFETY_CHECKS CONDA_EXTRA_SAFETY_CHECKS CONDA_NO_PLUGINS
            CONDA_REGISTER_ENVS CONDA_SHORTCUTS
        )
        LOCAL_BIN_PATTERNS=("anaconda*" "conda*")  # WILDCARD: review with --dry-run
        XDG_ITEMS=(jupyter conda)
        MACOS_LIBRARY=(Jupyter)
        MACOS_APP_SUPPORT=(Anaconda conda ContinuumIO jupyter)
        MACOS_CACHES=(Anaconda conda pip)

        if [[ -f "$CONFIG_FILE" ]]; then
            printf "${YELLOW}Note: yq not found, using hardcoded defaults${RESET}\n"
            printf "${YELLOW}Install yq to use %s${RESET}\n" "$CONFIG_FILE"
        fi
    fi
}

usage() {
    cat << EOF
Usage: $SCRIPT_NAME [options]

Cleanup Anaconda/Miniconda/Miniforge installations on Linux and macOS.

Options:
    -n, --dry-run          Preview what would be deleted (no changes made)
    -f, --force            Skip confirmation prompts
    -s, --skip-uninstaller Skip removing installation directories
    --name NAME            Only remove installations matching NAME
    -h, --help             Show this help message

Examples:
    $SCRIPT_NAME --dry-run          # Preview changes
    $SCRIPT_NAME --force            # Run without prompts
    $SCRIPT_NAME --name miniconda3  # Only remove miniconda3
EOF
}

log_action() {
    local action="$1" path="$2" extra="${3:-}"
    case "$action" in
        DryRun) printf "  ${YELLOW}[DryRun]${RESET} %s %s\n" "$path" "$extra" ;;
        DELETE) printf "  ${RED}[DELETE]${RESET} %s %s\n" "$path" "$extra" ;;
        SKIP)   printf "  ${GRAY}[SKIP]${RESET}   %s\n" "$path" ;;
        CLEAN)  printf "  ${CYAN}[CLEAN]${RESET}  %s\n" "$path" ;;
    esac
}

section_header() {
    printf "\n${GREEN}=== %s ===${RESET}\n" "$1"
}

remove_path_safely() {
    local path="$1"

    if [[ ! -e "$path" ]]; then
        log_action SKIP "not found: $path"
        return 1
    fi

    if [[ -d "$path" ]]; then
        local count
        count=$(find "$path" -type f 2>/dev/null | wc -l | tr -d ' ')
        if $DRY_RUN; then
            log_action DryRun "dir  $path" "($count files)"
        else
            log_action DELETE "dir  $path" "($count files)"
            rm -rf "$path"
        fi
    else
        if $DRY_RUN; then
            log_action DryRun "file $path"
        else
            log_action DELETE "file $path"
            rm -f "$path"
        fi
    fi
    return 0
}

matches_name_filter() {
    local path="$1"
    if [[ -z "$NAME_FILTER" ]]; then
        return 0
    fi
    local basename
    basename="$(basename "$path")"
    [[ "${basename,,}" == *"${NAME_FILTER,,}"* ]]
}

confirm_cleanup() {
    if $FORCE || $DRY_RUN; then
        return 0
    fi

    printf "${RED}This will permanently remove Anaconda/Miniconda and all related files.${RESET}\n"
    printf "${YELLOW}Run with --dry-run first to see what would be deleted.${RESET}\n"
    printf "Type 'yes' to continue: "
    read -r confirm
    if [[ "$confirm" != "yes" ]]; then
        printf "${YELLOW}Aborted.${RESET}\n"
        exit 0
    fi
}

remove_install_dirs() {
    section_header "Removing Installation Directories"

    if $SKIP_UNINSTALLER; then
        log_action SKIP "Installation removal skipped (--skip-uninstaller)"
        return
    fi

    for dir in "${INSTALL_DIRS[@]}"; do
        if [[ -d "$dir" ]] && matches_name_filter "$dir"; then
            remove_path_safely "$dir"
        elif [[ ! -d "$dir" ]]; then
            log_action SKIP "not found: $dir"
        fi
    done
}

remove_user_profile_items() {
    section_header "Cleaning User Profile ($HOME)"

    for item in "${USER_PROFILE_ITEMS[@]}"; do
        remove_path_safely "$HOME/$item" || true
    done

    for pattern in "${USER_PROFILE_PATTERNS[@]}"; do
        for match in $HOME/$pattern; do
            [[ -e "$match" ]] && remove_path_safely "$match" || true
        done
    done
}

remove_platform_specific() {
    local os_type
    os_type="$(uname -s)"

    # Unix common: ~/.local/bin patterns
    section_header "Cleaning ~/.local/bin"
    local local_bin="$HOME/.local/bin"
    if [[ -d "$local_bin" ]]; then
        for pattern in "${LOCAL_BIN_PATTERNS[@]}"; do
            for match in "$local_bin"/$pattern; do
                [[ -e "$match" ]] && remove_path_safely "$match" || true
            done
        done
    else
        log_action SKIP "not found: $local_bin"
    fi

    case "$os_type" in
        Darwin)
            section_header "Cleaning ~/Library"
            for item in "${MACOS_LIBRARY[@]}"; do
                remove_path_safely "$HOME/Library/$item" || true
            done

            section_header "Cleaning macOS Application Support"
            local app_support="$HOME/Library/Application Support"
            for item in "${MACOS_APP_SUPPORT[@]}"; do
                remove_path_safely "$app_support/$item" || true
            done

            section_header "Cleaning macOS Caches"
            local caches="$HOME/Library/Caches"
            for item in "${MACOS_CACHES[@]}"; do
                remove_path_safely "$caches/$item" || true
            done

            section_header "Cleaning macOS Preferences"
            for plist in "$HOME/Library/Preferences/com.continuum"*.plist \
                         "$HOME/Library/Preferences/com.anaconda"*.plist; do
                [[ -e "$plist" ]] && remove_path_safely "$plist" || true
            done
            ;;
        Linux)
            section_header "Cleaning XDG Directories"
            local xdg_data="${XDG_DATA_HOME:-$HOME/.local/share}"
            local xdg_config="${XDG_CONFIG_HOME:-$HOME/.config}"
            local xdg_cache="${XDG_CACHE_HOME:-$HOME/.cache}"

            for item in "${XDG_ITEMS[@]}"; do
                remove_path_safely "$xdg_data/$item" || true
                remove_path_safely "$xdg_config/$item" || true
                remove_path_safely "$xdg_cache/$item" || true
            done

            section_header "Cleaning Desktop Entries"
            remove_path_safely "$xdg_data/applications/anaconda"* || true
            ;;
    esac
}

remove_config_dirs() {
    section_header "Cleaning Config Directories (from conda/base/constants.py:SEARCH_PATH)"

    # User config dirs
    for dir in "${USER_CONFIG_DIRS[@]}"; do
        remove_path_safely "$dir" || true
    done

    # System config dirs (may require sudo, just report)
    for dir in "${SYSTEM_CONFIG_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            if $DRY_RUN; then
                log_action DryRun "$dir" "(system, may need sudo)"
            else
                if [[ -w "$dir" ]] || [[ -w "$(dirname "$dir")" ]]; then
                    remove_path_safely "$dir"
                else
                    printf "  ${YELLOW}[MANUAL]${RESET} %s (run: sudo rm -rf %s)\n" "$dir" "$dir"
                fi
            fi
        else
            log_action SKIP "not found: $dir"
        fi
    done
}

clean_shell_configs() {
    section_header "Cleaning Shell Configuration Files"

    for config in "${SHELL_CONFIGS[@]}"; do
        [[ -f "$config" ]] || continue

        if grep -qE '(conda|anaconda|miniconda|miniforge|mamba)' "$config" 2>/dev/null; then
            if $DRY_RUN; then
                log_action DryRun "$config" "(contains conda init)"
            else
                log_action CLEAN "$config"
                local temp_file
                temp_file="$(mktemp)"
                trap 'rm -f "$temp_file"' RETURN

                # Remove conda initialize block and any conda-related lines
                sed -E \
                    -e '/# >>> conda initialize >>>/,/# <<< conda initialize <<</d' \
                    -e '/# >>> mamba initialize >>>/,/# <<< mamba initialize <<</d' \
                    -e '/^[[:space:]]*#.*conda/d' \
                    -e '/conda activate/d' \
                    -e '/conda init/d' \
                    "$config" > "$temp_file"

                mv "$temp_file" "$config"
            fi
        else
            log_action SKIP "$config (no conda references)"
        fi
    done
}

remove_conda_from_path() {
    section_header "Checking PATH"

    local found_conda=false
    IFS=':' read -ra path_parts <<< "${PATH:-}"

    for part in "${path_parts[@]}"; do
        if [[ "$part" == *conda* ]] || [[ "$part" == *anaconda* ]] || \
           [[ "$part" == *miniconda* ]] || [[ "$part" == *miniforge* ]]; then
            found_conda=true
            if $DRY_RUN; then
                log_action DryRun "PATH: $part"
            else
                log_action DELETE "PATH: $part"
            fi
        fi
    done

    if ! $found_conda; then
        log_action SKIP "No conda entries in PATH"
    else
        printf "\n${YELLOW}Note: PATH changes require restarting your shell or sourcing your config.${RESET}\n"
    fi
}

print_completion() {
    printf "\n${GREEN}=== Done ===${RESET}\n"
    if $DRY_RUN; then
        printf "${YELLOW}Run without --dry-run to perform actual cleanup.${RESET}\n"
    else
        printf "${GREEN}Cleanup complete. Restart your terminal for changes to take effect.${RESET}\n"
    fi
}

main() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -n|--dry-run) DRY_RUN=true ;;
            -f|--force) FORCE=true ;;
            -s|--skip-uninstaller) SKIP_UNINSTALLER=true ;;
            --name) NAME_FILTER="$2"; shift ;;
            -h|--help) usage; exit 0 ;;
            *) printf "Unknown option: %s\n" "$1" >&2; usage >&2; exit 1 ;;
        esac
        shift
    done

    load_config
    confirm_cleanup
    remove_install_dirs
    remove_user_profile_items
    remove_platform_specific
    remove_config_dirs
    clean_shell_configs
    remove_conda_from_path
    print_completion
}

main "$@"
