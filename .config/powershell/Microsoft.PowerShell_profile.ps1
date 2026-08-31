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
    function ls { eza --icons=auto @args }
    function ll { eza -la --icons=auto @args }
    function la { eza -a --icons=auto @args }
    function lt { eza --tree --icons=auto @args }
}

# Activate pixi in current shell (preserves readline, unlike `pixi shell`)
function pixi-activate {
    param([string]$ManifestPath = ".")
    $hook = pixi shell-hook --manifest-path $ManifestPath
    Invoke-Expression $hook
    # Set CONDA_DEFAULT_ENV for starship (project-env format)
    if ($env:PIXI_PROJECT_NAME) {
        $env:CONDA_DEFAULT_ENV = "$($env:PIXI_PROJECT_NAME)-$($env:PIXI_ENVIRONMENT_NAME)"
    }
}

# Starship prompt
if (Get-Command starship -ErrorAction SilentlyContinue) {
    $env:STARSHIP_CONFIG = "$HOME\.config\starship.toml"
    Invoke-Expression (&starship init powershell)
}
