# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ~/.bashrc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# check the window size after each command and, if necessary, update the values of LINES and COLUMNS.
shopt -s checkwinsize

# bash completion(s)
# git
source /usr/share/bash-completion/completions/git
source /usr/share/git/completion/git-prompt.sh

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

# Python
#eval "$(uv generate-shell-completion bash)"
#eval "$(uvx --generate-shell-completion bash)"

# bash alias(es)
[[ -f ~/.bash_aliases ]] &&
    . ~/.bash_aliases

# start starship
eval "$(starship init bash)"

# prevent duplicates in the path
append_path () {
    case ":$PATH:" in
        *:"$1":*)
            ;;
        *)
            PATH="${PATH:+$PATH:}$1"
    esac
}

# PATH environment variable
CARGO_HOME=$HOME/.cargo
append_path $CARGO_HOME/bin
LOCAL_HOME=$HOME/.local
append_path $LOCAL_HOME/bin
TEX_HOME=/usr/local/texlive/2025/bin/x86_64-linux
append_path $TEX_HOME

# yazi - yank
function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
	command yazi "$@" --cwd-file="$tmp"
	IFS= read -r -d '' cwd < "$tmp"
	[ -n "$cwd" ] && [ "$cwd" != "$PWD" ] && builtin cd -- "$cwd"
	rm -f -- "$tmp"
}
