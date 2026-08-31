#!/usr/bin/env bash
# macOS/Linux Dotfiles Installation Script
# Run as: bash install.sh [-f|--force] [-n|--dry-run] [--skip-tools] [-u|--update] [-s|--system]
# Use --system (requires sudo) to install to /etc/xdg for all users

set -e

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE=false
DRY_RUN=false
SKIP_TOOLS=false
UPDATE=false
SYSTEM=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force) FORCE=true; shift ;;
        -n|--dry-run) DRY_RUN=true; shift ;;
        -s|--system) SYSTEM=true; shift ;;
        --skip-tools) SKIP_TOOLS=true; shift ;;
        -u|--update) UPDATE=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if $SYSTEM && [[ $EUID -ne 0 ]]; then
    echo "Error: --system requires root privileges. Run with sudo."
    exit 1
fi

status() { echo -e "\033[36m:: $1\033[0m"; }
skip() { echo -e "   \033[33mSKIP: $1\033[0m"; }
done_msg() { echo -e "   \033[32mOK: $1\033[0m"; }
error_msg() { echo -e "   \033[31mERROR: $1\033[0m"; }
manual_msg() { echo -e "   \033[33mMANUAL: $1\033[0m"; }

command_exists() { command -v "$1" &>/dev/null; }

is_macos() { [[ "$(uname)" == "Darwin" ]]; }

install_tool() {
    local name="$1"
    local command="$2"
    local brew_pkg="$3"
    local apt_pkg="$4"

    status "$name"

    if command_exists "$command"; then
        skip "$name already installed"
        return
    fi

    if $DRY_RUN; then
        if is_macos; then
            echo "   Would install: brew install $brew_pkg"
        else
            echo "   Would install: sudo apt install $apt_pkg"
        fi
        return
    fi

    echo "   Installing $name..."
    if is_macos; then
        if command_exists brew; then
            brew install "$brew_pkg"
            done_msg "$name installed"
        else
            manual_msg "Homebrew not found. Install from https://brew.sh"
        fi
    else
        if command_exists apt; then
            sudo apt install -y "$apt_pkg"
            done_msg "$name installed"
        else
            manual_msg "apt not found. Install $name with your package manager"
        fi
    fi
}

symlink() {
    local target="$1"
    local link="$2"

    mkdir -p "$(dirname "$link")"

    if [[ -L "$link" ]]; then
        local current_target
        current_target="$(readlink "$link")"
        if [[ "$current_target" == "$target" ]]; then
            skip "$link already linked correctly"
            return
        fi
    fi

    if [[ -e "$link" ]]; then
        if $FORCE; then
            if $DRY_RUN; then
                echo "   Would remove: $link"
            else
                rm -rf "$link"
            fi
        else
            skip "$link exists (use -f to overwrite)"
            return
        fi
    fi

    if $DRY_RUN; then
        echo "   Would link: $link -> $target"
    else
        ln -s "$target" "$link"
        done_msg "$link -> $target"
    fi
}

echo ""
echo -e "\033[35mDotfiles Installer for macOS/Linux\033[0m"
echo -e "\033[35m===================================\033[0m"
echo "Source: $DOTFILES"
echo "Config: $DOTFILES/.config"
echo "Method: Symlinks"
$DRY_RUN && echo -e "\033[33m(DRY RUN - no changes will be made)\033[0m"
$UPDATE && echo -e "\033[33m(UPDATE MODE - settings only, no tool installation)\033[0m"
$SYSTEM && echo -e "\033[33m(SYSTEM-WIDE - installing to /etc/xdg for all users)\033[0m"
echo ""

if $SYSTEM; then
    CONFIG_BASE="/etc/xdg"
else
    CONFIG_BASE="$HOME/.config"
fi

# Neovim
status "Neovim"
symlink "$DOTFILES/.config/nvim" "$CONFIG_BASE/nvim"

# Yazi file manager
status "Yazi"
symlink "$DOTFILES/.config/yazi" "$CONFIG_BASE/yazi"

# Eza (ls replacement)
status "Eza"
symlink "$DOTFILES/.config/eza" "$CONFIG_BASE/eza"

# Starship config
status "Starship Config"
symlink "$DOTFILES/.config/starship.toml" "$CONFIG_BASE/starship.toml"

# Pixi config
status "Pixi Config"
symlink "$DOTFILES/.config/pixi" "$CONFIG_BASE/pixi"

# Conda config (user only, not system-wide)
if ! $SYSTEM; then
    status "Condarc"
    symlink "$DOTFILES/.config/conda/.condarc" "$HOME/.condarc"
fi

# Bash config (user only, not system-wide)
if ! $SYSTEM; then
    status "Bash Profile"
    symlink "$DOTFILES/.config/bash/.bash_profile" "$HOME/.bash_profile"

    status "Bashrc"
    symlink "$DOTFILES/.config/bash/.bashrc" "$HOME/.bashrc"

    status "Bash Aliases"
    symlink "$DOTFILES/.config/bash/.bash-aliases" "$HOME/.bash-aliases"

    status "Bash Functions"
    symlink "$DOTFILES/.config/bash/.bashrc-functions" "$HOME/.bashrc-functions"

    status "Inputrc"
    symlink "$DOTFILES/.config/.inputrc" "$HOME/.config/.inputrc"
fi

# Install tools (unless skipped or update-only mode)
if ! $SKIP_TOOLS && ! $UPDATE; then
    echo ""
    echo -e "\033[35mInstalling Tools\033[0m"
    echo -e "\033[35m================\033[0m"
    echo ""

    install_tool "Neovim" "nvim" "neovim" "neovim"
    install_tool "Git" "git" "git" "git"
    install_tool "Python" "python3" "python" "python3"

    # Yazi with dependencies
    status "Yazi"
    if command_exists yazi; then
        skip "Yazi already installed"
    elif $DRY_RUN; then
        if is_macos; then
            echo "   Would install: brew install yazi ffmpeg sevenzip jq poppler fd ripgrep fzf zoxide imagemagick"
        else
            echo "   Would install: cargo install --locked yazi-fm yazi-cli"
        fi
    else
        echo "   Installing Yazi..."
        if is_macos; then
            if command_exists brew; then
                brew install yazi ffmpeg sevenzip jq poppler fd ripgrep fzf zoxide imagemagick
                done_msg "Yazi installed"
            else
                manual_msg "Homebrew not found. Install from https://brew.sh"
            fi
        else
            if command_exists cargo; then
                cargo install --locked yazi-fm yazi-cli
                done_msg "Yazi installed"
            else
                manual_msg "Cargo not found. See https://yazi-rs.github.io/docs/installation"
            fi
        fi
    fi

    install_tool "Eza" "eza" "eza" "eza"
    install_tool "Starship" "starship" "starship" "starship"

    # Nerd Font - download and install SauceCodePro Nerd Font
    status "Nerd Font (SauceCodePro)"
    if is_macos; then
        FONT_DIR="$HOME/Library/Fonts"
    else
        FONT_DIR="$HOME/.local/share/fonts"
    fi

    # Check if font files already exist
    if ls "$FONT_DIR"/SauceCodePro*.ttf &>/dev/null 2>&1; then
        skip "SauceCodePro Nerd Font already installed"
    elif $DRY_RUN; then
        echo "   Would download and install SauceCodePro Nerd Font"
    else
        FONT_URL="https://github.com/ryanoasis/nerd-fonts/releases/latest/download/SourceCodePro.zip"
        DOWNLOADS_DIR="$HOME/Downloads"
        FONT_ZIP="$DOWNLOADS_DIR/SourceCodePro.zip"
        TEMP_DIR="/tmp/SourceCodePro"

        # Skip download if cached zip exists
        if [[ -f "$FONT_ZIP" ]]; then
            echo "   Using cached download from $FONT_ZIP"
        else
            echo "   Downloading SauceCodePro Nerd Font..."
            if command_exists curl; then
                curl -fsSL "$FONT_URL" -o "$FONT_ZIP"
            elif command_exists wget; then
                wget -q "$FONT_URL" -O "$FONT_ZIP"
            else
                error_msg "Neither curl nor wget found"
                manual_msg "Download from https://www.nerdfonts.com/font-downloads"
            fi
        fi

        if [[ -f "$FONT_ZIP" ]]; then
            rm -rf "$TEMP_DIR"
            mkdir -p "$TEMP_DIR"
            unzip -q "$FONT_ZIP" -d "$TEMP_DIR"

            mkdir -p "$FONT_DIR"
            INSTALLED=0
            for ttf in "$TEMP_DIR"/*.ttf; do
                [[ -f "$ttf" ]] || continue
                DEST="$FONT_DIR/$(basename "$ttf")"
                if [[ ! -f "$DEST" ]]; then
                    cp "$ttf" "$DEST"
                    ((INSTALLED++))
                fi
            done

            # Update font cache on Linux
            if ! is_macos && command_exists fc-cache; then
                fc-cache -f "$FONT_DIR"
            fi

            rm -rf "$TEMP_DIR"

            if [[ $INSTALLED -gt 0 ]]; then
                done_msg "Installed $INSTALLED font files"
            else
                done_msg "Font files already in place"
            fi
        fi
    fi

    # debugpy (Python package)
    status "debugpy"
    if ! command_exists pip3 && ! command_exists pip; then
        skip "pip not found (install Python first, then re-run)"
    else
        PIP_CMD="pip3"
        command_exists pip3 || PIP_CMD="pip"
        if $PIP_CMD show debugpy &>/dev/null; then
            skip "debugpy already installed"
        elif $DRY_RUN; then
            echo "   Would install: $PIP_CMD install debugpy"
        else
            echo "   Installing debugpy..."
            $PIP_CMD install debugpy
            done_msg "debugpy installed"
        fi
    fi
fi

echo ""
echo -e "\033[32mInstallation complete!\033[0m"
if $SYSTEM; then
    echo -e "\033[32mConfig installed to $CONFIG_BASE (available to all users)\033[0m"
fi
echo ""
echo -e "\033[36mNext steps:\033[0m"
echo "  1. Restart terminal to apply font changes"
echo "  2. Open Neovim and run :Mason to install LSP servers"
if ! $SYSTEM; then
    echo ""
    echo -e "\033[36mFor all users (admin/root):\033[0m"
    echo "  Run: sudo bash install.sh --system"
fi
