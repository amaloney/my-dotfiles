# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ~/.bashrc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# conda functions
[[ -f ~/useful-conda-functions ]] &&
    source ~/useful-conda-functions

# local machine bash preferences
[[ -f ~/.bashrc-local ]] &&
    source ~/.bashrc-local

# shared bash functions
[[ -f ~/.bash-functions ]] &&
    source ~/.bash-functions

# bash completion(s)
# git
[[ -f  /usr/share/bash-completion/completions/git ]] &&
    source /usr/share/bash-completion/completions/git
[[ -f /usr/share/git/completion/git-prompt.sh ]] &&
    source /usr/share/git/completion/git-prompt.sh

# bash alias(es)
[[ -f ~/.bash-aliases ]] &&
    source ~/.bash-aliases

# bash history
export HISTCONTROL=ignoreboth:erasedups
export HISTFILE=~/.bash_history
export HISTFILESIZE=-1
export HISTSIZE=-1
shopt -s histappend

# check the window size after each command and, if necessary, update the values of LINES and COLUMNS.
shopt -s checkwinsize

# pager and editor environment variables
export EDITOR=nvim
export MANPAGER="nvim +Man!"
export VISUAL=nvim
export TERM=xterm-ghostty

# PATH updates
PIXI=$HOME/.pixi
append_path $PIXI/bin
CARGO_HOME=$HOME/.cargo
append_path $CARGO_HOME/bin
TEX_HOME=/usr/local/texlive/2025/bin/x86_64-linux
append_path $TEX_HOME
LOCAL_HOME=$HOME/.local
append_path $LOCAL_HOME/bin
# GEM_HOME="$(ruby -e 'puts Gem.user_dir')"
# append_path "$GEM_HOME/bin"

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
    prepend_path $HOMEBREW/bin:$HOMEBREW/sbin

    export SHELL=/opt/homebrew/bin/bash

fi

# ━━ Linux ━━
if [[ $OSTYPE == linux* ]]; then
    # bash completions
    source /usr/share/bash-completion/completions/git

    # git completions
    source /usr/share/git/completion/git-prompt.sh

    export SHELL=/usr/bin/bash
fi

# start starship
if hash starship 2>/dev/null; then
    eval "$(starship init bash)"
fi

# Activate pixi
function pixi_activate() {
    # default to current directory if no path is given
    local manifest_path="${1:-.}"
    eval "$(pixi shell-hook --manifest-path $manifest_path --environment dev)"
}

export PATH
