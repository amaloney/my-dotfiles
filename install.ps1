# Windows Dotfiles Installation Script
# Run as: powershell -ExecutionPolicy Bypass -File install.ps1
# Uses directory junctions (no special permissions required)
# Use -System (requires admin) to install to ProgramData for all users

param(
    [switch]$Force,
    [switch]$DryRun,
    [switch]$SkipTools,
    [switch]$Update,  # Update settings only, skip tool installation
    [switch]$System,  # Install to system-wide location for all users
    [switch]$Admin    # Install to Administrator user's profile
)

$ErrorActionPreference = "Stop"
$dotfiles = if ($PSScriptRoot) { $PSScriptRoot } else { $PWD.Path }

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

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-CommandExists {
    param([string]$Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Test-WingetPackageInstalled {
    param([string]$PackageId)
    $result = winget list --id $PackageId 2>$null
    return $LASTEXITCODE -eq 0 -and $result -match $PackageId
}

function Test-FontInstalled {
    param([string]$FontName)
    $fonts = [System.Drawing.Text.InstalledFontCollection]::new()
    return $fonts.Families | Where-Object { $_.Name -like "*$FontName*" }
}

function Install-Tool {
    param(
        [string]$Name,
        [string]$WingetId,
        [string]$Command,
        [switch]$RequiresAdmin
    )

    Write-Status "$Name"

    if ($Command -and (Test-CommandExists $Command)) {
        Write-Skip "$Name already installed"
        return
    }

    if (-not $Command -and (Test-WingetPackageInstalled $WingetId)) {
        Write-Skip "$Name already installed"
        return
    }

    if ($RequiresAdmin -and -not (Test-IsAdmin)) {
        Write-Host "   MANUAL: $Name requires admin. Run: winget install --id $WingetId" -ForegroundColor Yellow
        return
    }

    if ($DryRun) {
        Write-Host "   Would install: winget install --id $WingetId" -ForegroundColor Gray
        return
    }

    Write-Host "   Installing $Name..." -ForegroundColor Gray
    winget install --id $WingetId -e --source winget --accept-source-agreements --accept-package-agreements
    # Winget exit codes: 0 = success, -1978335189 = no update available, -1978335212 = already installed
    $successCodes = @(0, -1978335189, -1978335212)
    if ($LASTEXITCODE -in $successCodes) {
        Write-Done "$Name installed"
    } else {
        Write-Host "   ERROR: Failed to install $Name (exit code: $LASTEXITCODE)" -ForegroundColor Red
    }
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

# Check admin for system-wide or admin-user install
if ($System -and -not (Test-IsAdmin)) {
    Write-Host "Error: -System requires admin privileges. Run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}
if ($Admin -and -not (Test-IsAdmin)) {
    Write-Host "Error: -Admin requires admin privileges. Run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}
if ($System -and $Admin) {
    Write-Host "Error: -System and -Admin are mutually exclusive." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Dotfiles Installer for Windows" -ForegroundColor Magenta
Write-Host "===============================" -ForegroundColor Magenta
Write-Host "Source: $dotfiles"
Write-Host "Config: $dotfiles\.config"
Write-Host "Method: Directory junctions (no admin required)"
if ($DryRun) { Write-Host "(DRY RUN - no changes will be made)" -ForegroundColor Yellow }
if ($Update) { Write-Host "(UPDATE MODE - settings only, no tool installation)" -ForegroundColor Yellow }
if ($System) { Write-Host "(SYSTEM-WIDE - installing to ProgramData for all users)" -ForegroundColor Yellow }
if ($Admin) { Write-Host "(ADMIN USER - installing to Administrator's profile)" -ForegroundColor Yellow }
Write-Host ""

# Set config paths based on install type
if ($System) {
    $nvimPath = "$env:ProgramData\nvim"
    $yaziPath = "$env:ProgramData\yazi\config"
    $ezaPath = "$env:ProgramData\eza"
} elseif ($Admin) {
    $adminProfile = "C:\Users\Administrator"
    $nvimPath = "$adminProfile\AppData\Local\nvim"
    $yaziPath = "$adminProfile\AppData\Roaming\yazi\config"
    $ezaPath = "$adminProfile\AppData\Roaming\eza"
} else {
    $nvimPath = "$env:LOCALAPPDATA\nvim"
    $yaziPath = "$env:APPDATA\yazi\config"
    $ezaPath = "$env:APPDATA\eza"
}

# Neovim
Write-Status "Neovim"
$nvimSource = "$dotfiles\.config\nvim"
if (-not (Test-Path $nvimSource)) {
    Write-Host "   ERROR: Source not found: $nvimSource" -ForegroundColor Red
} else {
    New-Junction -Link $nvimPath -Target $nvimSource
}

# Yazi file manager
Write-Status "Yazi"
$yaziSource = "$dotfiles\.config\yazi"
if (-not (Test-Path $yaziSource)) {
    Write-Host "   ERROR: Source not found: $yaziSource" -ForegroundColor Red
} else {
    New-Junction -Link $yaziPath -Target $yaziSource
}

# Eza (ls replacement)
Write-Status "Eza"
$ezaSource = "$dotfiles\.config\eza"
if (-not (Test-Path $ezaSource)) {
    Write-Host "   ERROR: Source not found: $ezaSource" -ForegroundColor Red
} else {
    New-Junction -Link $ezaPath -Target $ezaSource
}

# PowerShell profile (copy, since symlinks require admin)
Write-Status "PowerShell Profile"
$psProfileSource = "$dotfiles\.config\powershell\Microsoft.PowerShell_profile.ps1"
$psProfileDir = "$env:USERPROFILE\Documents\PowerShell"
$psProfilePath = "$psProfileDir\Microsoft.PowerShell_profile.ps1"
if (-not (Test-Path $psProfileSource)) {
    Write-Host "   ERROR: Source not found: $psProfileSource" -ForegroundColor Red
} else {
    if (-not (Test-Path $psProfileDir)) {
        if ($DryRun) {
            Write-Host "   Would create directory: $psProfileDir" -ForegroundColor Gray
        } else {
            New-Item -ItemType Directory -Path $psProfileDir -Force | Out-Null
        }
    }
    if (Test-Path $psProfilePath) {
        $sourceHash = (Get-FileHash $psProfileSource).Hash
        $destHash = (Get-FileHash $psProfilePath).Hash
        if ($sourceHash -eq $destHash) {
            Write-Skip "$psProfilePath already up to date"
        } elseif ($Force) {
            if ($DryRun) {
                Write-Host "   Would copy: $psProfileSource -> $psProfilePath" -ForegroundColor Gray
            } else {
                Copy-Item $psProfileSource $psProfilePath -Force
                Write-Done "Updated $psProfilePath"
            }
        } else {
            Write-Skip "$psProfilePath exists (use -Force to overwrite)"
        }
    } else {
        if ($DryRun) {
            Write-Host "   Would copy: $psProfileSource -> $psProfilePath" -ForegroundColor Gray
        } else {
            Copy-Item $psProfileSource $psProfilePath
            Write-Done "Copied to $psProfilePath"
        }
    }
}

# Starship config (copy, since symlinks require admin)
Write-Status "Starship Config"
$starshipSource = "$dotfiles\.config\starship.toml"
$starshipPath = "$env:USERPROFILE\.config\starship.toml"
$starshipDir = "$env:USERPROFILE\.config"
if (-not (Test-Path $starshipSource)) {
    Write-Host "   ERROR: Source not found: $starshipSource" -ForegroundColor Red
} else {
    if (-not (Test-Path $starshipDir)) {
        if ($DryRun) {
            Write-Host "   Would create directory: $starshipDir" -ForegroundColor Gray
        } else {
            New-Item -ItemType Directory -Path $starshipDir -Force | Out-Null
        }
    }
    if (Test-Path $starshipPath) {
        $sourceHash = (Get-FileHash $starshipSource).Hash
        $destHash = (Get-FileHash $starshipPath).Hash
        if ($sourceHash -eq $destHash) {
            Write-Skip "$starshipPath already up to date"
        } elseif ($Force) {
            if ($DryRun) {
                Write-Host "   Would copy: $starshipSource -> $starshipPath" -ForegroundColor Gray
            } else {
                Copy-Item $starshipSource $starshipPath -Force
                Write-Done "Updated $starshipPath"
            }
        } else {
            Write-Skip "$starshipPath exists (use -Force to overwrite)"
        }
    } else {
        if ($DryRun) {
            Write-Host "   Would copy: $starshipSource -> $starshipPath" -ForegroundColor Gray
        } else {
            Copy-Item $starshipSource $starshipPath
            Write-Done "Copied to $starshipPath"
        }
    }
}

# Install tools (unless skipped or update-only mode)
if (-not $SkipTools -and -not $Update) {
    Write-Host ""
    Write-Host "Installing Tools" -ForegroundColor Magenta
    Write-Host "================" -ForegroundColor Magenta
    Write-Host ""

    Install-Tool -Name "Neovim" -WingetId "Neovim.Neovim" -Command "nvim"
    Install-Tool -Name "Yazi" -WingetId "sxyazi.yazi" -Command "yazi"
    Install-Tool -Name "Eza" -WingetId "eza-community.eza" -Command "eza"
    Install-Tool -Name "Starship" -WingetId "Starship.Starship" -Command "starship"
    Install-Tool -Name "Python" -WingetId "Python.Python.3.12" -Command "python"
    Install-Tool -Name "Git" -WingetId "Git.Git" -Command "git"

    # Nerd Font - download and install SauceCodePro Nerd Font
    Write-Status "Nerd Font (SauceCodePro)"
    $userFonts = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
    $systemFonts = "$env:SystemRoot\Fonts"

    # Check if font files already exist (user or system location)
    $userFontFiles = Get-ChildItem "$userFonts\SauceCodePro*.ttf" -ErrorAction SilentlyContinue
    $systemFontFiles = Get-ChildItem "$systemFonts\SauceCodePro*.ttf" -ErrorAction SilentlyContinue

    if ($userFontFiles -or $systemFontFiles) {
        Write-Skip "SauceCodePro Nerd Font already installed"
    } elseif ($DryRun) {
        Write-Host "   Would download and install SauceCodePro Nerd Font" -ForegroundColor Gray
    } else {
        $fontUrl = "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/SourceCodePro.zip"
        $downloadsDir = Join-Path $env:USERPROFILE "Downloads"
        $fontZip = Join-Path $downloadsDir "SourceCodePro.zip"
        $tempDir = "$env:TEMP\SourceCodePro"

        try {
            # Skip download if cached zip exists
            if (Test-Path $fontZip) {
                Write-Host "   Using cached download from $fontZip" -ForegroundColor Gray
            } else {
                Write-Host "   Downloading SauceCodePro Nerd Font..." -ForegroundColor Gray
                Invoke-WebRequest -Uri $fontUrl -OutFile $fontZip -UseBasicParsing
            }

            if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
            Expand-Archive -Path $fontZip -DestinationPath $tempDir -Force

            if (-not (Test-Path $userFonts)) {
                New-Item -ItemType Directory -Path $userFonts -Force | Out-Null
            }

            $installed = 0
            Get-ChildItem "$tempDir\*.ttf" | ForEach-Object {
                $destPath = Join-Path $userFonts $_.Name
                if (-not (Test-Path $destPath)) {
                    Copy-Item $_.FullName $destPath
                    $installed++
                }
            }

            # Register fonts in registry (user fonts)
            $regPath = "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
            Get-ChildItem "$userFonts\SauceCodePro*.ttf" -ErrorAction SilentlyContinue | ForEach-Object {
                $fontName = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
                Set-ItemProperty -Path $regPath -Name "$fontName (TrueType)" -Value $_.FullName -ErrorAction SilentlyContinue
            }

            # Keep the zip in Downloads for future runs, only clean up extract dir
            Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue

            if ($installed -gt 0) {
                Write-Done "Installed $installed font files (restart terminal to use)"
            } else {
                Write-Done "Font files already in place"
            }
        } catch {
            Write-Host "   ERROR: Failed to install font: $_" -ForegroundColor Red
            Write-Host "   MANUAL: Download from https://www.nerdfonts.com/font-downloads" -ForegroundColor Yellow
        }
    }

    # debugpy (Python package)
    Write-Status "debugpy"
    if (-not (Test-CommandExists "pip")) {
        Write-Skip "pip not found (install Python first, then re-run)"
    } else {
        $debugpyCheck = pip show debugpy 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Skip "debugpy already installed"
        } elseif ($DryRun) {
            Write-Host "   Would install: pip install debugpy" -ForegroundColor Gray
        } else {
            Write-Host "   Installing debugpy..." -ForegroundColor Gray
            pip install debugpy
            if ($LASTEXITCODE -eq 0) {
                Write-Done "debugpy installed"
            }
        }
    }
}

# Update settings (runs on full install or with -Update flag)
if (-not $SkipTools -or $Update) {
    Write-Host ""
    Write-Host "Updating Settings" -ForegroundColor Magenta
    Write-Host "=================" -ForegroundColor Magenta
    Write-Host ""

    # Configure Windows Terminal to use Nerd Font
    Write-Status "Windows Terminal Font"
    $wtSettingsPath = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
    $fontName = "SauceCodePro Nerd Font Mono"
    if (Test-Path $wtSettingsPath) {
        $wtSettings = Get-Content $wtSettingsPath -Raw | ConvertFrom-Json
        $currentFont = $wtSettings.profiles.defaults.font.face
        if ($currentFont -eq $fontName) {
            Write-Skip "Windows Terminal already using $fontName"
        } elseif ($DryRun) {
            Write-Host "   Would set Windows Terminal font to: $fontName" -ForegroundColor Gray
        } else {
            if (-not $wtSettings.profiles.defaults) {
                $wtSettings.profiles | Add-Member -NotePropertyName "defaults" -NotePropertyValue @{} -Force
            }
            if (-not $wtSettings.profiles.defaults.font) {
                $wtSettings.profiles.defaults | Add-Member -NotePropertyName "font" -NotePropertyValue @{} -Force
            }
            $wtSettings.profiles.defaults.font | Add-Member -NotePropertyName "face" -NotePropertyValue $fontName -Force
            $wtSettings | ConvertTo-Json -Depth 100 | Set-Content $wtSettingsPath -Encoding UTF8
            Write-Done "Windows Terminal font set to $fontName"
        }
    } else {
        Write-Skip "Windows Terminal settings not found (not installed?)"
    }
}

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
if ($System) {
    Write-Host "Config installed to $env:ProgramData (available to all users)" -ForegroundColor Green
}
if ($Admin) {
    Write-Host "Config installed to Administrator's profile" -ForegroundColor Green
}
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Restart Windows Terminal to apply font changes"
Write-Host "  2. Open Neovim and run :Mason to install LSP servers"
if (-not $System -and -not $Admin) {
    Write-Host ""
    Write-Host "For Administrator user:" -ForegroundColor Cyan
    Write-Host "  Run as Admin: powershell -ExecutionPolicy Bypass -File install.ps1 -Admin"
    Write-Host ""
    Write-Host "For all users (ProgramData):" -ForegroundColor Cyan
    Write-Host "  Run as Admin: powershell -ExecutionPolicy Bypass -File install.ps1 -System"
}
