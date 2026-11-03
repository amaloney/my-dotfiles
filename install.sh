#!/usr/bin/env bash
# macOS/Linux dotfiles installer: symlinks configs into place, optionally installs tools.
# --system (needs sudo) installs to /etc/xdg for all users, plus the Linux NAS/borgmatic backup files.
# Short flags (mkdir -p, rm -f, ln -s) on purpose: macOS BSD tools don't accept the long forms.
set -o errexit -o nounset -o pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DOTFILES
readonly HARNESSES="$DOTFILES/.config/harnesses"

# ANSI colors for terminal output
readonly RED=$'\033[31m'
readonly GREEN=$'\033[32m'
readonly YELLOW=$'\033[33m'
readonly MAGENTA=$'\033[35m'
readonly CYAN=$'\033[36m'
readonly NORMAL=$'\033[0m'

# Options (set by parse_args; FORCE may also be set by the overwrite prompt)
FORCE=false
DRY_RUN=false
SKIP_TOOLS=false
UPDATE=false
SYSTEM=false
CONFIG_BASE="$HOME/.config"

usage() {
    cat << EOF
Usage: $(basename "$0") [options]

  -f, --force      replace existing files and links without asking
  -n, --dry-run    show what would change, change nothing
  -u, --update     settings only, no tool installation
      --skip-tools skip tool installation
  -s, --system     install for all users to /etc/xdg (run with sudo)
  -h, --help       show this help
EOF
}

# ---------- output ----------

status() { echo "${CYAN}:: $1${NORMAL}"; }
skip() { echo "   ${YELLOW}SKIP: $1${NORMAL}"; }
done_msg() { echo "   ${GREEN}OK: $1${NORMAL}"; }
error_msg() { echo "   ${RED}ERROR: $1${NORMAL}" >&2; }
manual_msg() { echo "   ${YELLOW}MANUAL: $1${NORMAL}"; }
would() { echo "   Would $1"; }
heading() {
    echo ""
    echo "${MAGENTA}$1${NORMAL}"
    echo "${MAGENTA}${1//?/=}${NORMAL}"
}

# ---------- checks ----------

command_exists() { command -v "$1" &>/dev/null; }
is_macos() { [[ "$(uname)" == "Darwin" ]]; }

# ---------- file helpers ----------

# Remove an existing path before replacing it. Returns 1 (caller skips) unless --force or the prompt allowed it.
clear_existing() {
    local path="$1"
    if ! $FORCE; then
        skip "$path exists (use -f to overwrite)"
        return 1
    fi
    if $DRY_RUN; then
        would "remove: $path"
    else
        rm -rf "$path"
    fi
}

symlink() {
    local target="$1"
    local link="$2"

    if [[ -L "$link" && "$(readlink "$link")" == "$target" ]]; then
        skip "$link already linked correctly"
        return 0
    fi
    if [[ -L "$link" || -e "$link" ]]; then
        clear_existing "$link" || return 0
    fi

    if $DRY_RUN; then
        would "link: $link -> $target"
    else
        mkdir -p "$(dirname "$link")"
        ln -s "$target" "$link"
        done_msg "$link -> $target"
    fi
}

# Copy (not link) a file whose installed copy is meant to diverge locally, e.g. settings.json.
# A diverged copy is only replaced with --force (or a yes at the prompt), like symlink().
copy_file() {
    local source="$1"
    local dest="$2"

    # An old symlink from before this file was copied: always replace it
    if [[ -L "$dest" ]]; then
        if $DRY_RUN; then
            would "remove old link: $dest"
        else
            rm -f "$dest"
        fi
    fi

    if [[ -f "$dest" && ! -L "$dest" ]]; then
        if diff -q "$source" "$dest" &>/dev/null; then
            skip "$dest up to date"
            return 0
        fi
        if ! $FORCE; then
            skip "$dest differs from the repo copy (use -f to overwrite; reconcile manually)"
            return 0
        fi
    fi

    if $DRY_RUN; then
        would "copy: $source -> $dest"
    else
        mkdir -p "$(dirname "$dest")"
        cp "$source" "$dest"
        done_msg "$dest (copied)"
    fi
}

# Install a root-owned copy (never a symlink): root must not execute or read config from a user-writable
# repo, or any user-level compromise becomes root. Linux only (GNU install/stat).
install_root_file() {
    local source="$1"
    local dest="$2"
    local mode="$3"

    if [[ -f "$dest" ]] && diff --brief "$source" "$dest" &>/dev/null \
        && [[ "$(stat --format=%a "$dest")" == "$mode" ]]; then
        skip "$dest up to date"
    elif $DRY_RUN; then
        would "install: $source -> $dest (root:root $mode)"
    else
        install -D --owner=root --group=root --mode="$mode" "$source" "$dest"
        done_msg "$dest (root:root $mode)"
    fi
}

# Remove top-level symlinks in each dir that point into $DOTFILES at a path that no longer exists.
# Never touches real files or links pointing outside the repo.
prune_stale_links() {
    local dir entry target
    for dir in "$@"; do
        [[ -d "$dir" ]] || continue
        for entry in "$dir"/*; do
            [[ -L "$entry" ]] || continue
            target="$(readlink "$entry")"
            [[ "$target" == "$DOTFILES/"* && ! -e "$target" ]] || continue
            if $DRY_RUN; then
                would "prune: $entry -> $target (source deleted)"
            else
                rm -f "$entry"
                done_msg "pruned $entry (source deleted)"
            fi
        done
    done
}

# ---------- setup ----------

parse_args() {
    while (( $# > 0 )); do
        case "$1" in
            -f|--force) FORCE=true ;;
            -n|--dry-run) DRY_RUN=true ;;
            -s|--system) SYSTEM=true ;;
            --skip-tools) SKIP_TOOLS=true ;;
            -u|--update) UPDATE=true ;;
            -h|--help) usage; exit 0 ;;
            *) error_msg "unknown option: $1"; usage >&2; exit 1 ;;
        esac
        shift
    done

    if $SYSTEM && (( EUID != 0 )); then
        error_msg "--system requires root privileges. Run with sudo."
        exit 1
    fi
    if $SYSTEM; then
        CONFIG_BASE="/etc/xdg"
    fi
}

print_banner() {
    heading "Dotfiles Installer for macOS/Linux"
    echo "Source: $DOTFILES"
    echo "Config: $DOTFILES/.config"
    echo "Method: Symlinks"
    if $DRY_RUN; then echo "${YELLOW}(DRY RUN - no changes will be made)${NORMAL}"; fi
    if $UPDATE; then echo "${YELLOW}(UPDATE MODE - settings only, no tool installation)${NORMAL}"; fi
    if $SYSTEM; then echo "${YELLOW}(SYSTEM-WIDE - installing to /etc/xdg for all users)${NORMAL}"; fi
    echo ""
}

# Ask once whether to replace existing files (skipped with -f or --dry-run; "no" when there's no terminal)
prompt_overwrite() {
    if $FORCE || $DRY_RUN; then
        return 0
    fi
    local response=""
    echo "${YELLOW}Existing config files will be skipped by default.${NORMAL}"
    read -r -p "Replace existing files with symlinks? [y/N] " response || response=""
    case "$response" in
        [yY][eE][sS]|[yY]) FORCE=true ;;
        *) ;;
    esac
    echo ""
}

# ---------- configs ----------

install_app_configs() {
    status "Neovim"
    symlink "$DOTFILES/.config/nvim" "$CONFIG_BASE/nvim"

    status "Yazi"
    symlink "$DOTFILES/.config/yazi" "$CONFIG_BASE/yazi"

    status "Eza"
    symlink "$DOTFILES/.config/eza" "$CONFIG_BASE/eza"

    status "Starship Config"
    symlink "$DOTFILES/.config/starship/starship.toml" "$CONFIG_BASE/starship.toml"

    status "Pixi Config"
    symlink "$DOTFILES/.config/pixi" "$CONFIG_BASE/pixi"

    status "Ruff Config"
    symlink "$DOTFILES/.config/ruff" "$CONFIG_BASE/ruff"
}

# User only, not system-wide
install_user_configs() {
    status "Condarc"
    symlink "$DOTFILES/.config/conda/.condarc" "$HOME/.condarc"

    # Keeps every repo's .harness/ out of git status
    status "Git global ignore"
    symlink "$DOTFILES/.config/git/ignore" "$HOME/.config/git/ignore"

    status "Bash Profile"
    symlink "$DOTFILES/.config/bash/.bash_profile" "$HOME/.bash_profile"

    status "Bashrc"
    symlink "$DOTFILES/.config/bash/.bashrc" "$HOME/.bashrc"

    status "Bash Aliases"
    symlink "$DOTFILES/.config/bash/.bash-aliases" "$HOME/.bash-aliases"

    status "Bash Functions"
    symlink "$DOTFILES/.config/bash/.bashrc-functions" "$HOME/.bashrc-functions"

    status "Inputrc"
    symlink "$DOTFILES/.config/input/.inputrc" "$HOME/.inputrc"
}

# Kilo no longer falls back to opencode config: remove our old link so Kilo stops warning about ~/.config/opencode
remove_legacy_opencode_link() {
    local link="$HOME/.config/opencode/AGENTS.md"
    [[ -L "$link" && "$(readlink "$link")" == "$DOTFILES/"* ]] || return 0
    if $DRY_RUN; then
        would "remove: legacy ~/.config/opencode/AGENTS.md link"
    else
        rm -f "$link"
        rmdir "$HOME/.config/opencode" 2>/dev/null || true
        done_msg "removed legacy opencode config link"
    fi
}

# Claude Code + Kilo harness config (user only). OpenCode prefs live in harnesses/opencode/ but are intentionally
# NOT linked to ~/.config/opencode: Kilo warns on that dir.
install_harness_configs() {
    status "Harnesses - canonical shared dir"
    symlink "$HARNESSES" "$HOME/.config/harnesses"

    status "Harness AGENTS.md - Claude Code"
    symlink "$HARNESSES/AGENTS.md" "$HOME/.claude/CLAUDE.md"

    status "Harness AGENTS.md - Kilo"
    symlink "$HARNESSES/AGENTS.md" "$HOME/.config/kilo/AGENTS.md"

    remove_legacy_opencode_link

    status "Claude Code - README.md"
    symlink "$HARNESSES/claude/README.md" "$HOME/.claude/README.md"

    status "Claude Code - keybindings.json"
    symlink "$HARNESSES/claude/keybindings.json" "$HOME/.claude/keybindings.json"

    # Copied, not linked: local divergences (model, provider) live in the installed copy
    status "Claude Code - settings.json"
    copy_file "$HARNESSES/claude/settings.json" "$HOME/.claude/settings.json"

    status "Kilo - kilo.jsonc"
    copy_file "$HARNESSES/kilo/kilo.jsonc" "$HOME/.config/kilo/kilo.jsonc"

    status "Kilo - tui.json"
    copy_file "$HARNESSES/kilo/tui.json" "$HOME/.config/kilo/tui.json"

    status "Claude Code - skills (shared)"
    symlink "$HARNESSES/skills" "$HOME/.claude/skills"

    status "Claude Code - scripts (shared)"
    symlink "$HARNESSES/scripts" "$HOME/.claude/scripts"

    status "Agents (shared) - Kilo"
    symlink "$HARNESSES/agents" "$HOME/.config/kilo/agents"

    status "Agents (shared) - Claude Code"
    symlink "$HARNESSES/agents" "$HOME/.claude/agents"

    status "Kilo - plugins (shared)"
    symlink "$HARNESSES/plugins" "$HOME/.config/kilo/plugins"

    status "Git pre-commit hook (skill graph gate)"
    symlink "$HARNESSES/scripts/pre-commit" "$DOTFILES/.git/hooks/pre-commit"

    # Kilo loads skills from ~/.config/kilo/skills/: link each shared skill in
    status "Kilo - skills (shared)"
    local skill_dir name
    for skill_dir in "$HARNESSES/skills"/*/; do
        name="$(basename "$skill_dir")"
        # synced/ is Claude's skill-sync output (gitignored), not a harness skill
        [[ "$name" != "synced" ]] || continue
        symlink "${skill_dir%/}" "$HOME/.config/kilo/skills/$name"
    done

    status "Pruning stale links"
    prune_stale_links "$HOME/.claude" "$HOME/.config/kilo" "$HOME/.config/kilo/skills"
}

# ---------- tools ----------

install_tool() {
    local name="$1"
    local command="$2"
    local brew_pkg="$3"
    local apt_pkg="$4"

    status "$name"
    if command_exists "$command"; then
        skip "$name already installed"
        return 0
    fi

    if is_macos; then
        if $DRY_RUN; then would "install: brew install $brew_pkg"; return 0; fi
        if ! command_exists brew; then manual_msg "Homebrew not found. Install from https://brew.sh"; return 0; fi
        echo "   Installing $name..."
        brew install "$brew_pkg"
    else
        if $DRY_RUN; then would "install: sudo apt install $apt_pkg"; return 0; fi
        if ! command_exists apt; then manual_msg "apt not found. Install $name with your package manager"; return 0; fi
        echo "   Installing $name..."
        sudo apt install -y "$apt_pkg"
    fi
    done_msg "$name installed"
}

install_yazi() {
    local brew_pkgs=(yazi ffmpeg sevenzip jq poppler fd ripgrep fzf zoxide imagemagick)

    status "Yazi"
    if command_exists yazi; then
        skip "Yazi already installed"
        return 0
    fi

    if is_macos; then
        if $DRY_RUN; then would "install: brew install ${brew_pkgs[*]}"; return 0; fi
        if ! command_exists brew; then manual_msg "Homebrew not found. Install from https://brew.sh"; return 0; fi
        echo "   Installing Yazi..."
        brew install "${brew_pkgs[@]}"
    else
        if $DRY_RUN; then would "install: cargo install --locked yazi-fm yazi-cli"; return 0; fi
        if ! command_exists cargo; then
            manual_msg "Cargo not found. See https://yazi-rs.github.io/docs/installation"
            return 0
        fi
        echo "   Installing Yazi..."
        cargo install --locked yazi-fm yazi-cli
    fi
    done_msg "Yazi installed"
}

# Download to a temp file first, so a failed download never leaves a partial zip in the cache
download() {
    local url="$1"
    local dest="$2"
    local partial="$dest.partial"

    # Explicit returns: callers use `if ! download`, which turns off errexit inside this function
    if command_exists curl; then
        curl --fail --silent --show-error --location "$url" --output "$partial" || { rm -f "$partial"; return 1; }
    elif command_exists wget; then
        wget --quiet "$url" --output-document="$partial" || { rm -f "$partial"; return 1; }
    else
        error_msg "Neither curl nor wget found"
        return 1
    fi
    mv "$partial" "$dest"
}

install_nerd_font() {
    local font_url="https://github.com/ryanoasis/nerd-fonts/releases/latest/download/SourceCodePro.zip"
    local font_zip="$HOME/Downloads/SourceCodePro.zip"
    local font_dir="$HOME/.local/share/fonts"
    if is_macos; then
        font_dir="$HOME/Library/Fonts"
    fi

    status "Nerd Font (SauceCodePro)"
    if compgen -G "$font_dir/SauceCodePro*.ttf" >/dev/null; then
        skip "SauceCodePro Nerd Font already installed"
        return 0
    fi
    if $DRY_RUN; then
        would "download and install SauceCodePro Nerd Font"
        return 0
    fi

    if [[ -f "$font_zip" ]]; then
        echo "   Using cached download from $font_zip"
    else
        echo "   Downloading SauceCodePro Nerd Font..."
        mkdir -p "$(dirname "$font_zip")"
        if ! download "$font_url" "$font_zip"; then
            manual_msg "Download from https://www.nerdfonts.com/font-downloads"
            return 0
        fi
    fi

    local unpack_dir
    unpack_dir="$(mktemp -d)"
    # RETURN trap: clean up however this function exits
    trap 'rm -rf "$unpack_dir"; trap - RETURN' RETURN
    unzip -q "$font_zip" -d "$unpack_dir"

    mkdir -p "$font_dir"
    local installed=0 ttf dest
    for ttf in "$unpack_dir"/*.ttf; do
        [[ -f "$ttf" ]] || continue
        dest="$font_dir/$(basename "$ttf")"
        if [[ ! -f "$dest" ]]; then
            cp "$ttf" "$dest"
            installed=$(( installed + 1 ))
        fi
    done

    if ! is_macos && command_exists fc-cache; then
        fc-cache -f "$font_dir"
    fi

    if (( installed > 0 )); then
        done_msg "Installed $installed font files"
    else
        done_msg "Font files already in place"
    fi
}

install_debugpy() {
    status "debugpy"
    local pip_cmd
    if command_exists pip3; then
        pip_cmd="pip3"
    elif command_exists pip; then
        pip_cmd="pip"
    else
        skip "pip not found (install Python first, then re-run)"
        return 0
    fi

    if "$pip_cmd" show debugpy &>/dev/null; then
        skip "debugpy already installed"
    elif $DRY_RUN; then
        would "install: $pip_cmd install debugpy"
    else
        echo "   Installing debugpy..."
        "$pip_cmd" install debugpy
        done_msg "debugpy installed"
    fi
}

install_tools() {
    heading "Installing Tools"
    echo ""
    install_tool "Neovim" "nvim" "neovim" "neovim"
    install_tool "Git" "git" "git" "git"
    install_tool "Python" "python3" "python" "python3"
    install_yazi
    install_tool "Eza" "eza" "eza" "eza"
    install_tool "Starship" "starship" "starship" "starship"
    install_nerd_font
    install_debugpy
}

# ---------- NAS backups (Linux, --system) ----------

# NAS mounts + borgmatic backups. Packages and one-time steps: etc/README.md
install_nas_backup() {
    status "NAS mounts + backups (borgmatic)"
    install_root_file "$DOTFILES/etc/NetworkManager/dispatcher.d/50-nas-mounts" \
        /etc/NetworkManager/dispatcher.d/50-nas-mounts 755
    install_root_file "$DOTFILES/etc/borgmatic/config.yaml" /etc/borgmatic/config.yaml 600
    install_root_file "$DOTFILES/etc/systemd/system/borgmatic-nas.service" \
        /etc/systemd/system/borgmatic-nas.service 644
    install_root_file "$DOTFILES/etc/systemd/system/borgmatic-nas.timer" \
        /etc/systemd/system/borgmatic-nas.timer 644
    local helper
    for helper in due.sh run.sh notify.sh; do
        install_root_file "$DOTFILES/usr/local/lib/borgmatic-nas/$helper" "/usr/local/lib/borgmatic-nas/$helper" 755
    done

    # pre-down.d entries run before the link drops; relative target stays valid if /etc is moved/mounted
    local pre_down_link=/etc/NetworkManager/dispatcher.d/pre-down.d/50-nas-mounts
    if [[ "$(readlink "$pre_down_link" 2>/dev/null || true)" == "../50-nas-mounts" ]]; then
        skip "$pre_down_link already linked"
    elif $DRY_RUN; then
        would "link: $pre_down_link -> ../50-nas-mounts"
    else
        mkdir --parents "$(dirname "$pre_down_link")"
        ln --symbolic --force --no-dereference ../50-nas-mounts "$pre_down_link"
        done_msg "$pre_down_link -> ../50-nas-mounts"
    fi

    if $DRY_RUN; then
        would "run: systemctl daemon-reload"
        would "run: systemctl enable NetworkManager-dispatcher.service borgmatic-nas.service borgmatic-nas.timer"
    else
        systemctl daemon-reload
        systemctl enable --now NetworkManager-dispatcher.service
        systemctl enable borgmatic-nas.service borgmatic-nas.timer
        done_msg "units enabled"
    fi

    # The timer starts only once setup is finished, so it never runs against a missing passphrase
    if [[ ! -f /etc/borgmatic/passphrase ]]; then
        manual_msg "finish the one-time setup in etc/README.md (NAS squash, passphrase, repository)"
    elif $DRY_RUN; then
        would "run: systemctl start borgmatic-nas.timer"
    else
        systemctl start borgmatic-nas.timer
    fi
}

# ---------- summary ----------

print_summary() {
    echo ""
    echo "${GREEN}Installation complete!${NORMAL}"
    if $SYSTEM; then
        echo "${GREEN}Config installed to $CONFIG_BASE (available to all users)${NORMAL}"
    fi
    echo ""
    echo "${CYAN}Next steps:${NORMAL}"
    echo "  1. Restart terminal to apply font changes"
    echo "  2. Open Neovim and run :Mason to install LSP servers"
    if ! $SYSTEM; then
        echo ""
        echo "${CYAN}For all users (admin/root):${NORMAL}"
        echo "  Run: sudo bash install.sh --system"
    fi
}

main() {
    parse_args "$@"
    print_banner
    prompt_overwrite
    readonly FORCE DRY_RUN SKIP_TOOLS UPDATE SYSTEM CONFIG_BASE

    install_app_configs
    if ! $SYSTEM; then
        install_user_configs
        install_harness_configs
    fi
    if ! $SKIP_TOOLS && ! $UPDATE; then
        install_tools
    fi
    if $SYSTEM && ! is_macos && command_exists systemctl; then
        install_nas_backup
    fi
    print_summary
}

main "$@"
