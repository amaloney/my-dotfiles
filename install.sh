#!/usr/bin/env bash
# macOS/Linux Dotfiles Installation Script
# Run as: ./install.sh [-f|--force] [-n|--dry-run]

set -e

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force) FORCE=true; shift ;;
        -n|--dry-run) DRY_RUN=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

status() { echo -e "\033[36m:: $1\033[0m"; }
skip() { echo -e "   \033[33mSKIP: $1\033[0m"; }
done_msg() { echo -e "   \033[32mOK: $1\033[0m"; }

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
$DRY_RUN && echo -e "\033[33m(DRY RUN - no changes will be made)\033[0m"
echo ""

# Neovim
status "Neovim"
symlink "$DOTFILES/.config/nvim" "$HOME/.config/nvim"

# Yazi file manager
status "Yazi"
symlink "$DOTFILES/.config/yazi" "$HOME/.config/yazi"

# Eza (ls replacement)
status "Eza"
symlink "$DOTFILES/.config/eza" "$HOME/.config/eza"

# Tmux
status "Tmux"
symlink "$DOTFILES/.config/tmux" "$HOME/.config/tmux"

# Ghostty terminal
status "Ghostty"
symlink "$DOTFILES/.config/ghostty" "$HOME/.config/ghostty"

# Bash config
status "Bash"
symlink "$DOTFILES/.config/bash" "$HOME/.config/bash"

# Inputrc
status "Inputrc"
symlink "$DOTFILES/.config/.inputrc" "$HOME/.inputrc"

# Claude Code
status "Claude Code"
symlink "$DOTFILES/.claude" "$HOME/.claude"

# Conda
status "Conda"
symlink "$DOTFILES/.config/conda" "$HOME/.config/conda"

# Pixi
status "Pixi"
symlink "$DOTFILES/.config/pixi" "$HOME/.config/pixi"

# Colima (macOS only)
if [[ "$(uname)" == "Darwin" ]]; then
    status "Colima"
    symlink "$DOTFILES/.colima" "$HOME/.colima"
fi

# Git config (if exists)
if [[ -f "$DOTFILES/.gitconfig" ]]; then
    status "Git"
    symlink "$DOTFILES/.gitconfig" "$HOME/.gitconfig"
fi

echo ""
echo -e "\033[32mInstallation complete!\033[0m"
echo ""
echo -e "\033[36mNext steps:\033[0m"
if [[ "$(uname)" == "Darwin" ]]; then
    echo "  1. Install Neovim:  brew install neovim"
else
    echo "  1. Install Neovim:  sudo apt install neovim (or your package manager)"
fi
echo "  2. Install tools:   Open Neovim and run :Mason"
echo "  3. Install debugpy: pip install debugpy"
