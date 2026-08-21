# Windows Dotfiles Installation Script
# Run as: powershell -ExecutionPolicy Bypass -File install.ps1
# Uses directory junctions (no special permissions required)

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

function New-Junction {
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
        if ($existing.LinkType -eq "Junction") {
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
                # For junctions, use rmdir to remove just the link, not the target contents
                cmd /c "rmdir `"$Link`"" 2>$null
                if (Test-Path $Link) {
                    Remove-Item $Link -Recurse -Force
                }
            }
        } else {
            Write-Skip "$Link exists (use -Force to overwrite)"
            return
        }
    }

    if ($DryRun) {
        Write-Host "   Would link: $Link -> $Target" -ForegroundColor Gray
    } else {
        # Use cmd mklink /J for directory junctions (no admin required)
        $result = cmd /c "mklink /J `"$Link`" `"$Target`"" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Done "$Link -> $Target"
        } else {
            Write-Host "   ERROR: Failed to create junction: $result" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "Dotfiles Installer for Windows" -ForegroundColor Magenta
Write-Host "===============================" -ForegroundColor Magenta
Write-Host "Source: $dotfiles"
Write-Host "Method: Directory junctions (no admin required)"
if ($DryRun) { Write-Host "(DRY RUN - no changes will be made)" -ForegroundColor Yellow }
Write-Host ""

# Neovim
Write-Status "Neovim"
New-Junction -Link "$env:LOCALAPPDATA\nvim" -Target "$dotfiles\.config\nvim"

# Yazi file manager
Write-Status "Yazi"
New-Junction -Link "$env:APPDATA\yazi\config" -Target "$dotfiles\.config\yazi"

# Eza (ls replacement)
Write-Status "Eza"
New-Junction -Link "$env:APPDATA\eza" -Target "$dotfiles\.config\eza"

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Install Neovim:  winget install Neovim.Neovim"
Write-Host "  2. Install tools:   Open Neovim and run :Mason"
Write-Host "  3. Install Python:  winget install Python.Python.3.12"
Write-Host "  4. Install debugpy: pip install debugpy"
