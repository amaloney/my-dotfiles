# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ~/.bashrc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
source $HOME/useful-conda-functions

# check the window size after each command and, if necessary, update the values of LINES and COLUMNS.
shopt -s checkwinsize

# history
export HISTCONTROL=ignoreboth:erasedups
export HISTFILE=~/.bash_history
export HISTFILESIZE=-1
export HISTSIZE=-1
shopt -s histappend
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# pager and editor environment variables
export EDITOR=nvim
export PAGER=nvimpager
export VISUAL=nvim
export TERM=xterm-ghostty

# bash alias(es)
[[ -f ~/.bash_aliases ]] &&
    source ~/.bash_aliases

# prevent duplicates in the path
append_path() {
    case ":$PATH:" in
        *:"$1":*)
            ;;
        *)
            PATH="${PATH:+$PATH:}$1"
    esac
}
prepend_path() {
    case ":$PATH:" in
        *:"$1":*)
            ;;
        *)
            PATH="$1:${PATH:+$PATH:}"
    esac
}

# PATH updates
PIXI=$HOME/.pixi
append_path $PIXI/bin
if hash pixi 2>/dev/null; then
    eval "$(pixi completion --shell bash)"
fi
CARGO_HOME=$HOME/.cargo
append_path $CARGO_HOME/bin
TEX_HOME=/usr/local/texlive/2025/bin/x86_64-linux
append_path $TEX_HOME
LOCAL_HOME=$HOME/.local
append_path $LOCAL_HOME/bin

# yazi - yank
function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
	command yazi "$@" --cwd-file="$tmp"
	IFS= read -r -d '' cwd < "$tmp"
	[ -n "$cwd" ] && [ "$cwd" != "$PWD" ] && builtin cd -- "$cwd"
	rm -f -- "$tmp"
}

# ━━ macOS ━━
if [[ $OSTYPE == darwin* ]]; then
    # turn off brew analytics
    export HOMEBREW_NO_ANALYTICS=1

    # bash completions
    [[ -r /opt/homebrew/etc/profile.d/bash_completion.sh ]] &&
        source /opt/homebrew/etc/profile.d/bash_completion.sh

    # choose the shell from brew
    export SHELL=/opt/homebrew/bin/bash

    # Make ls more sane
    export LSCOLORS=GxFxCxDxBxegedabagaced

    # flags
    export CPPFLAGS="-I/opt/homebrew/include"
    export LDDFLAGS="-I/opt/homebrew/lib"

    # PATH
    HOMEBREW=/opt/homebrew
    prepend_path $HOMEBREW/bin

    export SHELL=/opt/homebrew/bin/bash

fi

# ━━ Linux ━━
if [[ $OSTYPE == linux* ]]; then
    # bash completions
    source /usr/share/bash-completion/completions/git

    # git completions
    source /usr/share/git/completion/git-prompt.sh

    #export SHELL=/opt/homebrew/bin/bash
fi

# start starship
if hash starship 2>/dev/null; then
    eval "$(starship init bash)"
fi

export PATH
