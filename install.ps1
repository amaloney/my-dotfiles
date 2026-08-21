# Windows Dotfiles Installation Script
# Run as: powershell -ExecutionPolicy Bypass -File install.ps1
# Requires: Developer Mode enabled OR run as Administrator

param(
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$dotfiles = $PSScriptRoot

function Write-Status {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host ":: $Message" -ForegroundColor $Color
}

function Write-Skip {
    param([string]$Message)
    Write-Host "   SKIP: $Message" -ForegroundColor Yellow
}

function Write-Done {
    param([string]$Message)
    Write-Host "   OK: $Message" -ForegroundColor Green
}

function New-Symlink {
    param(
        [string]$Link,
        [string]$Target
    )

    $linkParent = Split-Path -Parent $Link
    if (-not (Test-Path $linkParent)) {
        if ($DryRun) {
            Write-Host "   Would create directory: $linkParent" -ForegroundColor Gray
        } else {
            New-Item -ItemType Directory -Path $linkParent -Force | Out-Null
        }
    }

    if (Test-Path $Link) {
        $existing = Get-Item $Link -Force
        if ($existing.LinkType -eq "SymbolicLink") {
            $currentTarget = $existing.Target
            if ($currentTarget -eq $Target) {
                Write-Skip "$Link already linked correctly"
                return
            }
        }

        if ($Force) {
            if ($DryRun) {
                Write-Host "   Would remove: $Link" -ForegroundColor Gray
            } else {
                Remove-Item $Link -Recurse -Force
            }
        } else {
            Write-Skip "$Link exists (use -Force to overwrite)"
            return
        }
    }

    if ($DryRun) {
        Write-Host "   Would link: $Link -> $Target" -ForegroundColor Gray
    } else {
        New-Item -ItemType SymbolicLink -Path $Link -Target $Target | Out-Null
        Write-Done "$Link -> $Target"
    }
}

# Check for symlink capability
$testLink = "$env:TEMP\symlink_test_$(Get-Random)"
$testTarget = "$env:TEMP"
try {
    New-Item -ItemType SymbolicLink -Path $testLink -Target $testTarget -ErrorAction Stop | Out-Null
    Remove-Item $testLink -Force
} catch {
    Write-Host "ERROR: Cannot create symlinks." -ForegroundColor Red
    Write-Host "Enable Developer Mode (Settings > Privacy & Security > For developers)" -ForegroundColor Yellow
    Write-Host "Or run this script as Administrator." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Dotfiles Installer for Windows" -ForegroundColor Magenta
Write-Host "===============================" -ForegroundColor Magenta
Write-Host "Source: $dotfiles"
if ($DryRun) { Write-Host "(DRY RUN - no changes will be made)" -ForegroundColor Yellow }
Write-Host ""

# Neovim
Write-Status "Neovim"
New-Symlink -Link "$env:LOCALAPPDATA\nvim" -Target "$dotfiles\.config\nvim"

# Yazi file manager
Write-Status "Yazi"
New-Symlink -Link "$env:APPDATA\yazi\config" -Target "$dotfiles\.config\yazi"

# Eza (ls replacement)
Write-Status "Eza"
New-Symlink -Link "$env:APPDATA\eza" -Target "$dotfiles\.config\eza"

# Claude Code
Write-Status "Claude Code"
New-Symlink -Link "$env:USERPROFILE\.claude" -Target "$dotfiles\.claude"

# Git config (if exists)
if (Test-Path "$dotfiles\.gitconfig") {
    Write-Status "Git"
    New-Symlink -Link "$env:USERPROFILE\.gitconfig" -Target "$dotfiles\.gitconfig"
}

# Windows Terminal settings (optional - uncomment if you have settings)
# Write-Status "Windows Terminal"
# $wtPath = Get-ChildItem "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_*\LocalState" -ErrorAction SilentlyContinue | Select-Object -First 1
# if ($wtPath) {
#     New-Symlink -Link "$($wtPath.FullName)\settings.json" -Target "$dotfiles\windows-terminal\settings.json"
# }

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Install Neovim:  winget install Neovim.Neovim"
Write-Host "  2. Install tools:   Open Neovim and run :Mason"
Write-Host "  3. Install Python:  winget install Python.Python.3.12"
Write-Host "  4. Install debugpy: pip install debugpy"
