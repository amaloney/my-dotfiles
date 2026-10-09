# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ~/.bashrc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# readline configuration
export INPUTRC=$HOME/.inputrc

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
    export XDG_CONFIG_HOME="${HOME}/.config"
    export XDG_CACHE_HOME="${HOME}/.cache"
    export XDG_DATA_HOME="${HOME}/.local/share"
    export XDG_STATE_HOME="${HOME}/.local./state"
    export XDG_DATA_DIRS=/usr/local/share:/usr/share
    export XDG_CONFIG_DIRS=/etc/xdg
fi

# start starship
if hash starship 2>/dev/null; then
    export STARSHIP_CONFIG=$HOME/.config/starship.toml
    eval "$(starship init bash)"
fi

# activate pixi in current shell (preserves readline, unlike `pixi shell`)
pixi-activate() {
    local manifest_path="${1:-.}"
    local env_arg=""
    [[ -n "$2" ]] && env_arg="--environment $2"
    eval "$(pixi shell-hook --manifest-path "$manifest_path" $env_arg)"
    # set CONDA_DEFAULT_ENV for starship (project-env format)
    if [[ -n "$PIXI_PROJECT_NAME" ]]; then
        export CONDA_DEFAULT_ENV="${PIXI_PROJECT_NAME}-${PIXI_ENVIRONMENT_NAME}"
    fi
}

__conda_setup="$(\"$HOME/miniconda3/bin/conda\" 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        . "$HOME/miniconda3/etc/profile.d/conda.sh"
    else
        PATH="$HOME/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup

append_path $PIXI/bin
append_path $CARGO_HOME/bin
append_path $LOCAL_HOME/bin
append_path $GEM_HOME/bin
export PATH
