# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ~/.bashrc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# bash completion
source /usr/share/bash-completion/completions/git

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

export LD_LIBRARY_PATH=/usr/lib

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# Use ranger as a file manager in the terminal. This will open the editor on a selected
# file.
ranger() {
    local IFS=$'\t\n'
    local tempfile="$(mktemp -t tmp.XXXXXX)"
    local ranger_cmd=(
        command
        ranger
        --cmd="map Q chain shell echo %d > "$tempfile"; quitall"
    )

    ${ranger_cmd[@]} "$@"
    if [[ -f "$tempfile" ]] && [[ "$(cat -- "$tempfile")" != "$(echo -n `pwd`)" ]]; then
        cd -- "$(cat "$tempfile")" || return
    fi
    command rm -f -- "$tempfile" 2>/dev/null
    $EDITOR
}

# Change the desktop to "night time" settings in the terminal.
nighttime() {
    gsettings set org.gnome.settings-daemon.plugins.color night-light-enabled true
}

# Change the desktop to "day time" settings in the terminal.
daytime() {
    gsettings set org.gnome.settings-daemon.plugins.color night-light-enabled false
}

# Present Working Directory string, with .. for truncation.
generate_pwd() {
  pwd | sed s.$HOME.~.g | awk -F "/" '
    BEGIN { ORS="/" }
    END {
      for (i = 1; i <= NF; i++) {
        if ((i == 1 && $1 != "") || i == NF-1 || i == NF) {
          print $i
        }
        else if (i == 1 && $1 == "") {
          print "/"$2
          i++
        }
        else {
          print ".."
        }
      }
    }
  '
}

# Aliases
[[ -f ~/.bash_aliases ]] && . ~/.bash_aliases

# color variables.
white="\033[00;38;5;15m"
normal="\033[00;00;00;00m"
green="\033[00;38;5;47m"
green_u="\033[04;38;5;47m"
gray="\033[00;38;5;240m"
gray_u="\033[04;38;5;240m"
magenta="\033[00;38;5;165m"
yellow="\033[00;38;5;226m"
orange="\033[00;38;5;208m"
cyan="\033[00;38;5;45m"
purple="\033[00;38;5;013m"

prompt_command() {
  # Local variables used in various parts of this prompt command.
  local terminal_width=$(tput cols)

  # Show the current working directory.
  local cwd_str=$(generate_pwd)
  local cwd_str_width=${#cwd_str}
  local cwd_str_colored=$(printf "$gray%s$normal" "$cwd_str")

  # Show the git repository name if it exists.
  local git_prefix='git:'
  local git_str=$(git branch 2>/dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/')
  local git_str_width=$(( ${#git_prefix} + ${#git_str} ))
  local git_str_colored=$(printf "$cyan%s$yellow%s$normal" "$git_prefix" "$git_str")

  # Show the conda environment if it exists.
  local conda_prefix='conda:'
  local conda_str=$CONDA_DEFAULT_ENV
  local conda_str_width=$(( ${#conda_prefix} + ${#conda_str} ))
  local conda_str_colored=$(printf "$cyan%s$yellow%s$normal" "$conda_prefix" "$conda_str")

  # Show the workspace name.
  local workspace_prefix='workspace:'
  local workspace_number=$(xprop -root -notype _NET_CURRENT_DESKTOP | cut -d "=" -f 2 | xargs)
  local workspace_names=($(xprop -root -notype _NET_DESKTOP_NAMES | cut -d "=" -f 2 | sed -r 's/["|,]//g' | xargs))
  local workspace_name=${workspace_names[workspace_number]}
  local workspace_str_width=$(( ${#workspace_prefix} + ${#workspace_name} ))
  local workspace_str_colored=$(printf "$cyan%s$yellow%s$normal" "$workspace_prefix" "$workspace_name")

  # Combine the left string.
  local left_str_colored=$(printf "%s %s %s %s" "$cwd_str_colored" "$git_str_colored" "$conda_str_colored" "$workspace_str_colored")
  local left_str_width=$(( $cwd_str_width + 1 + $git_str_width + 1 + $conda_str_width + 1 + $workspace_str_width))

  # Combine the right string.
  local date_str=$(date '+%A %B %d %Y')
  local time_str=$(date '+%H:%M:%S')
  local right_str=$(printf "%s ║ %s" "$date_str" "$time_str")
  local right_str_width=${#right_str}
  local right_str_colored=$(printf "$purple%s$normal" "$right_str")

  # Calculate the gap width
  local info_width=$(( $left_str_width + $right_str_width ))
  local gap_width=$(( $terminal_width - $left_str_width - $right_str_width ))

  printf "\n$left_str_colored$gray_u%*s$right_str_colored\n" "$gap_width"

}

# PS1 adjustments.
PROMPT_COMMAND=prompt_command
PS1="\[$green_u\]\u\[$green\]\$ \[$normal\]"
export PS1

# Define the path
export GEM_HOME="$(ruby -e 'puts Gem.user_dir')"
export CARGO_HOME=$HOME/.cargo
export GO_HOME=$HOME/go
export PERL_HOME=/usr/bin/vendor_perl
export LOCAL_HOME=$HOME/.local
PATH=/usr/local/bin:/usr/bin:/usr/local/sbin
PATH=$LOCAL_HOME/bin:$GEM_HOME/bin:$CARGO_HOME/bin:$GO_HOME/bin:$PERL_HOME/bin:$PATH
export PATH

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('$HOME/mambaforge/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$HOME/mambaforge/etc/profile.d/conda.sh" ]; then
        . "$HOME/mambaforge/etc/profile.d/conda.sh"
    else
        export PATH="$HOME/mambaforge/bin:$PATH"
    fi
fi
unset __conda_setup

if [ -f "$HOME/mambaforge/etc/profile.d/mamba.sh" ]; then
    . "$HOME/mambaforge/etc/profile.d/mamba.sh"
fi
# <<< conda initialize <<<

# Add Google cloud commands. Arch Linux workaround.
source /etc/profile.d/google-cloud-cli.sh
