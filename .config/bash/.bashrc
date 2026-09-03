# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ~/.bashrc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# readline configuration
export INPUTRC=$HOME/.config/.inputrc

# conda functions
[[ -f ~/useful-conda-functions ]] &&
    source ~/useful-conda-functions

# local machine bash preferences
[[ -f ~/.bashrc-local ]] &&
    source ~/.bashrc-local

# shared bash functions
[[ -f ~/.bashrc-functions ]] &&
    source ~/.bashrc-functions

# bash completion(s)
# git
[[ -f /usr/share/bash-completion/completions/git ]] &&
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

# prevent conda from modifying prompt (let starship handle it)
export CONDA_CHANGEPS1=false
export TERM=xterm-ghostty

# PATH updates
CARGO_HOME=$HOME/.cargo
GEM_HOME="$(ruby -e 'puts Gem.user_dir')"
LOCAL_HOME=$HOME/.local
MINICONDA=$HOME/miniconda3
PIXI=$HOME/.pixi

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
    PERL="/opt/homebrew/Cellar/perl/5.42.2"
    prepend_path $PERL/bin

    export SHELL=/opt/homebrew/bin/bash

fi

# ━━ Linux ━━
if [[ $OSTYPE == linux* ]]; then
    # bash completions
    source /usr/share/bash-completion/completions/git

    # git completions
    source /usr/share/git/completion/git-prompt.sh

    # PATH
    # TEX_HOME=/usr/local/texlive/2025/bin/x86_64-linux
    # append_path $TEX_HOME

    export SHELL=/usr/bin/bash
fi

# start starship
if hash starship 2>/dev/null; then
    export STARSHIP_CONFIG=$HOME/.config/starship.toml
    eval "$(starship init bash)"
fi

# activate pixi in current shell (preserves readline, unlike `pixi shell`)
pixi-activate() {
    local manifest_path="${1:-.}"
    eval "$(pixi shell-hook --manifest-path "$manifest_path")"
    # set CONDA_DEFAULT_ENV for starship (project-env format)
    if [[ -n "$PIXI_PROJECT_NAME" ]]; then
        export CONDA_DEFAULT_ENV="${PIXI_PROJECT_NAME}-${PIXI_ENVIRONMENT_NAME}"
    fi
}

append_path $PIXI/bin
append_path $CARGO_HOME/bin
append_path $LOCAL_HOME/bin
append_path $GEM_HOME/bin
export PATH
