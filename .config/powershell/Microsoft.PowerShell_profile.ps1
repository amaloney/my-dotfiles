# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PowerShell Profile
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PSReadLine - history search with arrow keys (like bash .inputrc)
Set-PSReadLineOption -EditMode Emacs
Set-PSReadLineOption -HistorySearchCursorMovesToEnd
Set-PSReadLineKeyHandler -Key UpArrow -Function HistorySearchBackward
Set-PSReadLineKeyHandler -Key DownArrow -Function HistorySearchForward

# History settings
Set-PSReadLineOption -HistoryNoDuplicates
Set-PSReadLineOption -MaximumHistoryCount 10000

# Editor
$env:EDITOR = "nvim"
$env:VISUAL = "nvim"

# Aliases
Set-Alias -Name vim -Value nvim
Set-Alias -Name vi -Value nvim

# eza (if installed)
if (Get-Command eza -ErrorAction SilentlyContinue) {
    Remove-Item Alias:ls -ErrorAction SilentlyContinue
    function ls { eza --icons @args }
    function ll { eza -la --icons @args }
    function la { eza -a --icons @args }
    function lt { eza --tree --icons @args }
}

# Starship prompt
if (Get-Command starship -ErrorAction SilentlyContinue) {
    $env:STARSHIP_CONFIG = "$HOME\.config\starship.toml"
    Invoke-Expression (&starship init powershell)
}
