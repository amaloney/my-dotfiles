# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ~/.bash_aliases
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
alias less=$PAGER
alias more=$PAGER
alias ls='eza --almost-all --icons --group-directories-first --git -G'
alias ll='ls -1'
alias la='ls -lha'
alias tree='eza --tree --level 2'
alias grep="grep --color=auto --ignore-case"
alias diff='diff --color=auto'
alias ip='ip -color=auto'
alias mux=$GEM_HOME/bin/tmuxinator
