#Requires -Version 5.1
<#
.SYNOPSIS
    Automated Windows 11 VDI setup script.
.DESCRIPTION
    Sets up a vanilla Windows 11 VDI with developer tools suitable for package builds and custom installers.
.PARAMETER Install
    Comma-separated list of components to install. Valid options:
    VSCode, BuildTools, Git, Miniconda, Neovim, Yazi, Eza, Ripgrep, TreeSitter, NerdFont, Starship, PowerShell7, Psmux
    All components are installed if none are specified
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\vdi-setup.ps1

    To install everything, which is suitable for both package builds and custom installer builds. Note that:
      for custom installers;
        - install constructor
      for package builds;
        - install conda-build, anaconda-linter
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\vdi-setup.ps1 -Install VSCode,Miniconda

    What you'll want for package builds. Plus the usual items from conda; conda-build, anaconda-linter.
#>

param(
    [switch]$AdminPhase,
    [string]$LogFile,
    [string[]]$Install
)

# Valid install components
$script:ValidComponents = @(
    "VSCode", "BuildTools", "Git", "Miniconda", "Neovim", "Yazi", "Eza",
    "Ripgrep", "TreeSitter", "NerdFont", "Starship", "PowerShell7", "Psmux"
)

# Determine which components to install (all if none specified)
$script:Components = if ($Install -and $Install.Count -gt 0) {
    # Validate provided components
    foreach ($comp in $Install) {
        if ($comp -notin $script:ValidComponents) {
            $validOpts = $script:ValidComponents -join ', '
            Write-Host "ERROR: Invalid component '$comp'. Valid options: $validOpts" -ForegroundColor Red
            exit 1
        }
    }
    $Install
} else {
    $script:ValidComponents
}

function Test-ComponentSelected {
    param([string]$Name)
    return $Name -in $script:Components
}

$ErrorActionPreference = "Stop"

# Log file shared between user and admin phases
$script:LogPath = if ($LogFile) { $LogFile } else { Join-Path $env:TEMP "vdi-setup.log" }

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $script:LogPath -Value $logMessage -ErrorAction SilentlyContinue
}

# Helper function to check winget exit codes and fail fast on errors
function Test-WinGetResult {
    param([string]$Name)
    # Known "success" exit codes:
    #   0 = Success
    #  -1978335189 (0x8A15002B) = No applicable update (already installed, up to date)
    #  -1978335212 (0x8A150014) = Package already installed
    $successCodes = @(0, -1978335189, -1978335212)
    if ($LASTEXITCODE -notin $successCodes) {
        Write-Log "ERROR: Failed to install $Name (exit code: $LASTEXITCODE)" "Red"
        exit $LASTEXITCODE
    }
}

# Check if running on Windows 11 (build 22000+)
function Test-Windows11 {
    return [Environment]::OSVersion.Version.Build -ge 22000
}

# Enforce Windows 11 requirement
if (-not (Test-Windows11)) {
    Write-Host "ERROR: This script requires Windows 11 (build 22000+)." -ForegroundColor Red
    Write-Host "Current build: $([Environment]::OSVersion.Version.Build)" -ForegroundColor Red
    exit 1
}

# Check if running with elevated privileges
function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]$identity
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Refresh PATH from registry to pick up newly installed tools
function Update-PathFromRegistry {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = (@($machinePath, $userPath) | Where-Object { $_ }) -join ";"
}

# Enable Windows Developer Mode via registry (required for some dev tools)
function Enable-DeveloperMode {
    $regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock"
    $propParams = @{
        Path = $regPath
        Name = "AllowDevelopmentWithoutDevLicense"
        ErrorAction = "SilentlyContinue"
    }
    $currentValue = Get-ItemProperty @propParams
    if ($currentValue.AllowDevelopmentWithoutDevLicense -eq 1) {
        Write-Log "Developer Mode already enabled, skipping..." "Yellow"
        return
    }

    Write-Log "Enabling Developer Mode..." "Cyan"
    try {
        if (-not (Test-Path $regPath)) {
            New-Item -Path $regPath -Force | Out-Null
        }
        Set-ItemProperty -Path $regPath -Name "AllowDevelopmentWithoutDevLicense" -Value 1 -Type DWord
        Write-Log "  Developer Mode enabled successfully" "Gray"
    } catch {
        Write-Log "ERROR: Failed to enable Developer Mode: $_" "Red"
        throw
    }
}

# Configure Microsoft Edge to skip first-run experience and disable bloat
function Set-EdgeConfiguration {
    $edgePolicyPath = "HKLM:\SOFTWARE\Policies\Microsoft\Edge"
    $currentValue = Get-ItemProperty -Path $edgePolicyPath -Name "HideFirstRunExperience" -ErrorAction SilentlyContinue
    if ($currentValue.HideFirstRunExperience -eq 1) {
        Write-Log "Edge already configured, skipping..." "Yellow"
        return
    }

    Write-Log "Configuring Microsoft Edge..." "Cyan"
    try {
        if (-not (Test-Path $edgePolicyPath)) {
            New-Item -Path $edgePolicyPath -Force | Out-Null
        }

        # Skip first-run experience / welcome wizard
        Set-ItemProperty -Path $edgePolicyPath -Name "HideFirstRunExperience" -Value 1 -Type DWord

        # Disable sign-in prompt
        Set-ItemProperty -Path $edgePolicyPath -Name "BrowserSignin" -Value 0 -Type DWord

        # Disable sync
        Set-ItemProperty -Path $edgePolicyPath -Name "SyncDisabled" -Value 1 -Type DWord

        # Disable Copilot/AI features
        Set-ItemProperty -Path $edgePolicyPath -Name "CopilotCDPPageContext" -Value 0 -Type DWord
        Set-ItemProperty -Path $edgePolicyPath -Name "HubsSidebarEnabled" -Value 0 -Type DWord

        # Disable personalization and data collection
        Set-ItemProperty -Path $edgePolicyPath -Name "PersonalizationReportingEnabled" -Value 0 -Type DWord
        $spotlightParams = @{
            Path = $edgePolicyPath
            Name = "SpotlightExperiencesAndRecommendationsEnabled"
            Value = 0
            Type = "DWord"
        }
        Set-ItemProperty @spotlightParams

        # Disable promotional content, recommendations, and shopping features
        Set-ItemProperty -Path $edgePolicyPath -Name "PromotionalTabsEnabled" -Value 0 -Type DWord
        Set-ItemProperty -Path $edgePolicyPath -Name "ShowRecommendationsEnabled" -Value 0 -Type DWord
        Set-ItemProperty -Path $edgePolicyPath -Name "EdgeShoppingAssistantEnabled" -Value 0 -Type DWord
        Set-ItemProperty -Path $edgePolicyPath -Name "ShowMicrosoftRewards" -Value 0 -Type DWord
        Set-ItemProperty -Path $edgePolicyPath -Name "NewTabPageContentEnabled" -Value 0 -Type DWord
        Set-ItemProperty -Path $edgePolicyPath -Name "NewTabPageQuickLinksEnabled" -Value 0 -Type DWord
        Set-ItemProperty -Path $edgePolicyPath -Name "ConfigureDoNotTrack" -Value 1 -Type DWord

        # Set startup page to edge://settings
        # RestoreOnStartup: 4 = Open a list of URLs
        Set-ItemProperty -Path $edgePolicyPath -Name "RestoreOnStartup" -Value 4 -Type DWord
        $startupUrlsPath = "$edgePolicyPath\RestoreOnStartupURLs"
        if (-not (Test-Path $startupUrlsPath)) {
            New-Item -Path $startupUrlsPath -Force | Out-Null
        }
        Set-ItemProperty -Path $startupUrlsPath -Name "1" -Value "edge://settings" -Type String

        Write-Log "  Edge first-run experience disabled" "Gray"
        Write-Log "  Edge sign-in and sync disabled" "Gray"
        Write-Log "  Edge Copilot/AI features disabled" "Gray"
        Write-Log "  Edge promotions and recommendations disabled" "Gray"
        Write-Log "  Edge startup page set to edge://settings" "Gray"
    } catch {
        Write-Log "WARNING: Failed to configure Edge: $_" "Yellow"
    }
}

# Install winget and its prerequisites system-wide (requires admin)
function Install-WinGet {
    # Check if winget is already installed and working
    $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
    if ($wingetCmd) {
        $wingetVersion = & winget --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "WinGet already installed ($wingetVersion), skipping..." "Yellow"
            return
        }
    }

    Write-Log "Installing WinGet prerequisites..." "Cyan"

    # NuGet provider is required for Install-Module
    Write-Log "  Installing NuGet provider..." "Gray"
    try {
        Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force | Out-Null
    } catch {
        Write-Log "ERROR: Failed to install NuGet provider: $_" "Red"
        throw
    }

    # Install the WinGet PowerShell module for Repair-WinGetPackageManager
    Write-Log "  Installing Microsoft.WinGet.Client module..." "Gray"
    try {
        if (-not (Get-Module -ListAvailable -Name Microsoft.WinGet.Client)) {
            Install-Module -Name Microsoft.WinGet.Client -Force -Repository PSGallery -Scope AllUsers | Out-Null
        }
        Import-Module Microsoft.WinGet.Client -Force
    } catch {
        Write-Log "ERROR: Failed to install/import Microsoft.WinGet.Client: $_" "Red"
        throw
    }

    # Register the App Installer package (contains winget)
    Write-Log "  Registering App Installer package..." "Gray"
    $appInstallerPkg = "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe"
    try {
        Add-AppxPackage -RegisterByFamilyName -MainPackage $appInstallerPkg -ErrorAction Stop
    } catch {
        Write-Log "  AppxPackage registration failed, attempting repair..." "Yellow"

        # Repair/update winget to install App Installer
        Write-Log "  Repairing WinGet package manager..." "Gray"
        Repair-WinGetPackageManager -IncludePrerelease -AllUsers -ErrorAction Stop

        # Retry registration after repair
        Write-Log "  Retrying App Installer registration..." "Gray"
        try {
            Add-AppxPackage -RegisterByFamilyName -MainPackage $appInstallerPkg -ErrorAction Stop
        } catch {
            Write-Log "  AppxPackage registration skipped: $_" "Yellow"
        }
    }

    # Repair/update winget to latest version
    Write-Log "  Repairing WinGet package manager..." "Gray"
    Repair-WinGetPackageManager -IncludePrerelease -AllUsers -ErrorAction SilentlyContinue

    # Reset sources to ensure clean state (use & call operator for external executables)
    Write-Log "  Resetting WinGet sources..." "Gray"
    & winget source reset --force --disable-interactivity 2>&1 | Out-Null

    Write-Log "  Updating WinGet sources..." "Gray"
    & winget source update --disable-interactivity 2>&1 | Out-Null
}

# Repair winget for the current user (non-admin)
function Install-UserWinGet {
    # Check if winget is already working
    $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
    if ($wingetCmd) {
        $wingetVersion = & winget --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "WinGet already available for user ($wingetVersion), skipping..." "Yellow"
            return
        }
    }

    Write-Log "Repairing WinGet for current user..." "Cyan"
    Import-Module Microsoft.WinGet.Client -Force -ErrorAction SilentlyContinue

    # Run repair to install App Installer for the current user
    Write-Log "  Running Repair-WinGetPackageManager..." "Gray"
    Repair-WinGetPackageManager -IncludePrerelease -ErrorAction SilentlyContinue

    # Verify winget is now available
    $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $wingetCmd) {
        Write-Log "ERROR: winget not found. Check log at $script:LogPath" "Red"
        exit 1
    }

    # Update sources (reset requires admin, so just update)
    Write-Log "  Updating WinGet sources..." "Gray"
    & winget source update --disable-interactivity 2>&1 | Out-Null
}

# Install user-level tools (VS Code, Git, VS Build Tools, extensions)
function Install-UserTools {
    Write-Log "Installing user-level tools..." "Cyan"

    # VS Code - installed per-user to avoid admin requirements
    if (Test-ComponentSelected "VSCode") {
        $vscodePath = Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\Code.exe"
        if (Test-Path $vscodePath) {
            Write-Log "  Visual Studio Code already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing Visual Studio Code..." "Gray"
            $vscodeArgs = @(
                "install", "Microsoft.VisualStudioCode",
                "--silent", "--accept-source-agreements", "--accept-package-agreements", "--scope", "user"
            )
            # msstore source requires interactive agreement acceptance
            $vscodeArgs += @("--source", "winget")
            & winget @vscodeArgs
            Test-WinGetResult "Visual Studio Code"
        }
    }

    # # VS Build Tools - required for compiling native Python extensions
    # if (Test-ComponentSelected "BuildTools") {
    #     $buildToolsPath = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\2022\BuildTools"
    #     if (Test-Path $buildToolsPath) {
    #         Write-Log "  VS 2022 Build Tools already installed, skipping..." "Yellow"
    #     } else {
    #         Write-Log "  Installing VS 2022 Build Tools (may take minutes)..." "Gray"
    #         $vsOverride = "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --passive"
    #         & winget install Microsoft.VisualStudio.2022.BuildTools --source winget `
    #             --accept-source-agreements --accept-package-agreements --override $vsOverride
    #         Test-WinGetResult "Visual Studio 2022 Build Tools"
    #     }
    # }

    # Git - version control
    if (Test-ComponentSelected "Git") {
        $gitPath = Join-Path $env:ProgramFiles "Git\git-cmd.exe"
        if (Test-Path $gitPath) {
            Write-Log "  Git already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing Git..." "Gray"
            $gitArgs = @(
                "install", "--id", "Git.Git", "-e",
                "--source", "winget", "--silent",
                "--accept-source-agreements", "--accept-package-agreements"
            )
            & winget @gitArgs
            Test-WinGetResult "Git"
        }
    }

    # Refresh PATH so 'code' command is available
    Update-PathFromRegistry

    # Install VS Code extensions (only if VSCode selected)
    if (Test-ComponentSelected "VSCode") {
        $codeCmd = Get-Command code -ErrorAction SilentlyContinue
        if (-not $codeCmd) {
            Write-Log "WARNING: VS Code 'code' not found, skipping extensions..." "Yellow"
        } else {
            $installedExtensions = @(& code --list-extensions 2>&1 | Where-Object { $_ -is [string] })
            $extensions = @(
                @{ Id = "ms-python.python"; Name = "Python" },
                @{ Id = "charliermarsh.ruff"; Name = "Ruff" },
                @{ Id = "ms-toolsai.jupyter"; Name = "Jupyter" }
            )
            foreach ($ext in $extensions) {
                if ($installedExtensions -contains $ext.Id) {
                    Write-Log "  VS Code $($ext.Name) extension already installed..." "Yellow"
                } else {
                    Write-Log "  Installing VS Code $($ext.Name) extension..." "Gray"
                    & code --install-extension $ext.Id --force
                    if ($LASTEXITCODE -ne 0) {
                        Write-Log "ERROR: Failed to install $($ext.Name) extension" "Red"
                        exit $LASTEXITCODE
                    }
                }
            }
        }
    }
}

# Configure VS Code user settings
function Set-VSCodeSettings {
    if (-not (Test-ComponentSelected "VSCode")) {
        return
    }

    # Check if VS Code is actually installed
    $vscodePath = Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\Code.exe"
    if (-not (Test-Path $vscodePath)) {
        Write-Log "  VS Code not installed, skipping settings configuration..." "Yellow"
        return
    }

    $settingsDir = Join-Path $env:APPDATA "Code\User"
    $settingsPath = Join-Path $settingsDir "settings.json"

    # Check if settings already configured (telemetry key as marker)
    if (Test-Path $settingsPath) {
        $existingContent = Get-Content $settingsPath -Raw -ErrorAction SilentlyContinue
        if ($existingContent -match '"telemetry.telemetryLevel":\s*"off"') {
            Write-Log "  VS Code settings already configured, skipping..." "Yellow"
            return
        }
    }

    Write-Log "Configuring VS Code settings..." "Cyan"

    # Ensure settings directory exists
    if (-not (Test-Path $settingsDir)) {
        New-Item -Path $settingsDir -ItemType Directory -Force | Out-Null
    }

    # Settings to apply
    $settings = @{
        "terminal.integrated.scrollback" = 10000000
        # Disable telemetry, experiments, and crash reporting
        "telemetry.telemetryLevel" = "off"
        "workbench.enableExperiments" = $false
        "telemetry.enableCrashReporter" = $false
        # Disable AI/Copilot features and hide chat sidebar
        "github.copilot.enable" = @{
            "*" = $false
        }
        "editor.inlineSuggest.enabled" = $false
        "chat.commandCenter.enabled" = $false
        "workbench.secondarySideBar.visible" = $false
        "github.copilot.chat.welcomeMessage" = "never"
        # Line length settings
        "editor.rulers" = @(120)
        "editor.wordWrapColumn" = 119
        # Skip first-run wizard and welcome page
        "workbench.startupEditor" = "none"
        "workbench.welcomePage.walkthroughs.openOnInstall" = $false
        # Set Solarized Light theme
        "workbench.colorTheme" = "Solarized Light"
        # Disable workspace trust (no restricted mode prompts)
        "security.workspace.trust.enabled" = $false
        # Restore windows including terminals from previous session
        "window.restoreWindows" = "all"
    }

    # Only add conda terminal profile if Miniconda is selected and hook exists
    $condaHookPath = Join-Path $env:USERPROFILE "miniconda3\shell\condabin\conda-hook.ps1"
    if ((Test-ComponentSelected "Miniconda") -and (Test-Path $condaHookPath)) {
        $condaActivateCmd = "& '$condaHookPath'; conda activate"
        $settings["terminal.integrated.profiles.windows"] = @{
            "PowerShell (Conda)" = @{
                "source" = "PowerShell"
                "args" = @("-NoExit", "-Command", $condaActivateCmd)
            }
            "PowerShell" = @{
                "source" = "PowerShell"
            }
            "Command Prompt" = @{
                "path" = "cmd.exe"
            }
        }
        $settings["terminal.integrated.defaultProfile.windows"] = "PowerShell (Conda)"
    }

    # Merge with existing settings if file exists
    if (Test-Path $settingsPath) {
        try {
            $existingContent = Get-Content $settingsPath -Raw
            if ($existingContent) {
                # Strip JSONC comments (// and /* */) before parsing - VS Code supports JSONC but PS doesn't
                $jsonContent = $existingContent -replace '(?m)//.*$', '' -replace '/\*[\s\S]*?\*/', ''
                # Remove trailing commas before ] or }
                $jsonContent = $jsonContent -replace ',(\s*[}\]])', '$1'

                $json = $jsonContent | ConvertFrom-Json
                # Convert PSCustomObject to hashtable (PS 5.1 compatible - no -AsHashtable)
                $existingSettings = @{}
                $json.PSObject.Properties | ForEach-Object { $existingSettings[$_.Name] = $_.Value }

                foreach ($key in $settings.Keys) {
                    $existingSettings[$key] = $settings[$key]
                }
                $settings = $existingSettings
            }
        } catch {
            # Backup existing settings before overwriting
            $backupPath = "$settingsPath.bak"
            Copy-Item -Path $settingsPath -Destination $backupPath -Force -ErrorAction SilentlyContinue
            Write-Log "  WARNING: Could not parse existing settings, backed up to $backupPath" "Yellow"
        }
    }

    # Write settings file
    $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
    Write-Log "  Terminal scrollback set to 10000000 lines" "Gray"
    Write-Log "  Telemetry, experiments, and crash reporting disabled" "Gray"
    Write-Log "  AI/Copilot features disabled" "Gray"
    Write-Log "  Line ruler at 120, word wrap at 119" "Gray"
    Write-Log "  First-run wizard and welcome page disabled" "Gray"
    Write-Log "  Theme set to Solarized Light" "Gray"
    Write-Log "  Workspace trust disabled (no restricted mode)" "Gray"
    if ($settings.ContainsKey("terminal.integrated.defaultProfile.windows")) {
        Write-Log "  Default terminal set to PowerShell with conda auto-activation" "Gray"
    }
}

function Initialize-VSCode {
    if (-not (Test-ComponentSelected "VSCode")) {
        return
    }

    # Check if VS Code is actually installed
    $vscodePath = Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\Code.exe"
    if (-not (Test-Path $vscodePath)) {
        Write-Log "  VS Code not installed, skipping initialization..." "Yellow"
        return
    }

    # Check if VS Code has already been initialized (globalStorage exists after first run)
    $globalStoragePath = Join-Path $env:APPDATA "Code\User\globalStorage"
    if (Test-Path $globalStoragePath) {
        Write-Log "  VS Code already initialized, skipping..." "Yellow"
        return
    }

    Write-Log "Initializing VS Code (first-run setup)..." "Cyan"

    $codeCmd = Get-Command code -ErrorAction SilentlyContinue
    if (-not $codeCmd) {
        Write-Log "  VS Code 'code' command not found, skipping initialization" "Yellow"
        return
    }

    # Launch VS Code with --wait to initialize settings and dismiss first-run dialogs
    # Using CLI approach instead of SendKeys to avoid race conditions with window focus
    Write-Log "  Launching VS Code to apply settings..." "Gray"

    # Create a temp file to open, which causes VS Code to fully initialize
    $tempFile = Join-Path $env:TEMP "vscode-init-$([guid]::NewGuid().ToString('N').Substring(0,8)).txt"
    "VS Code initialization" | Set-Content $tempFile -Encoding UTF8

    # Launch VS Code with the temp file - it will apply settings on startup
    $codeProcess = Start-Process -FilePath $codeCmd.Source -ArgumentList "-n", $tempFile -PassThru

    # Wait for VS Code to fully initialize (check for window to appear)
    $timeout = 30
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        Start-Sleep -Seconds 2
        $elapsed += 2
        # Check if VS Code window exists
        $vscodeWindow = Get-Process -Name "Code" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle }
        if ($vscodeWindow) { break }
    }

    # Give it a moment to fully render
    Start-Sleep -Seconds 3

    # Close VS Code gracefully using CloseMainWindow (sends WM_CLOSE, not a hard kill)
    Write-Log "  Closing VS Code..." "Gray"
    Get-Process -Name "Code" -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle } |
        ForEach-Object { $_.CloseMainWindow() | Out-Null }

    # Wait for VS Code to exit gracefully
    $timeout = 10
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        Start-Sleep -Seconds 1
        $elapsed += 1
        $remaining = Get-Process -Name "Code" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle }
        if (-not $remaining) { break }
    }

    # Clean up temp file
    Remove-Item $tempFile -Force -ErrorAction SilentlyContinue

    Write-Log "  VS Code initialized and ready for use" "Gray"
}

# Ensure Windows Terminal settings.json exists with valid JSON to prevent menuinst errors
# during Miniconda installation. menuinst tries to add a terminal profile and fails with
# JSONDecodeError if the file is empty or missing.
function Initialize-WindowsTerminalSettings {
    # Windows Terminal settings paths (regular and preview)
    $wtPackageDirs = @(
        (Join-Path $env:LOCALAPPDATA "Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState"),
        (Join-Path $env:LOCALAPPDATA "Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState")
    )

    foreach ($localStateDir in $wtPackageDirs) {
        # Only process if the LocalState directory exists (indicates WT is installed)
        if (-not (Test-Path $localStateDir)) {
            continue
        }

        $settingsPath = Join-Path $localStateDir "settings.json"

        # Check if file needs initialization
        $needsInit = $false
        if (-not (Test-Path $settingsPath)) {
            $needsInit = $true
        } else {
            $content = Get-Content $settingsPath -Raw -ErrorAction SilentlyContinue
            if ([string]::IsNullOrWhiteSpace($content)) {
                $needsInit = $true
            } else {
                # Verify it's valid JSON
                try {
                    $null = $content | ConvertFrom-Json
                } catch {
                    $needsInit = $true
                }
            }
        }

        if ($needsInit) {
            Write-Log "  Initializing Windows Terminal settings at $settingsPath" "Gray"
            # Minimal valid settings - Windows Terminal will populate defaults on first launch
            $minimalSettings = @{
                '$help' = 'https://aka.ms/terminal-documentation'
                '$schema' = 'https://aka.ms/terminal-profiles-schema'
                profiles = @{
                    defaults = @{}
                    list = @()
                }
            }
            $minimalSettings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
        }
    }
}

# Configure Windows Terminal to use Nerd Font
function Set-WindowsTerminalFont {
    if (-not (Test-ComponentSelected "NerdFont")) {
        return
    }

    Write-Log "Configuring Windows Terminal font..." "Cyan"

    # Find Windows Terminal settings (regular or preview)
    $wtPaths = @(
        (Join-Path $env:LOCALAPPDATA "Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"),
        (Join-Path $env:LOCALAPPDATA "Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json")
    )

    $settingsPath = $wtPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $settingsPath) {
        Write-Log "  Windows Terminal not found, skipping font configuration..." "Yellow"
        return
    }

    try {
        $content = Get-Content $settingsPath -Raw
        # Strip JSONC comments for parsing
        $jsonContent = $content -replace '(?m)//.*$', '' -replace '/\*[\s\S]*?\*/', ''
        $jsonContent = $jsonContent -replace ',(\s*[}\]])', '$1'
        $settings = $jsonContent | ConvertFrom-Json

        # Check if font is already set
        if ($settings.profiles.defaults.font.face -eq "SauceCodePro Nerd Font Mono") {
            Write-Log "  Windows Terminal font already configured, skipping..." "Yellow"
            return
        }

        # Ensure profiles.defaults exists
        if (-not $settings.profiles) {
            $settings | Add-Member -NotePropertyName "profiles" -NotePropertyValue ([PSCustomObject]@{})
        }
        if (-not $settings.profiles.defaults) {
            $settings.profiles | Add-Member -NotePropertyName "defaults" -NotePropertyValue ([PSCustomObject]@{})
        }

        # Set the font
        $fontConfig = [PSCustomObject]@{ face = "SauceCodePro Nerd Font Mono" }
        if ($settings.profiles.defaults.font) {
            $memberParams = @{
                NotePropertyName = "face"
                NotePropertyValue = "SauceCodePro Nerd Font Mono"
                Force = $true
            }
            $settings.profiles.defaults.font | Add-Member @memberParams
        } else {
            $settings.profiles.defaults | Add-Member -NotePropertyName "font" -NotePropertyValue $fontConfig -Force
        }

        # Write back (preserve formatting as much as possible)
        $settings | ConvertTo-Json -Depth 20 | Set-Content $settingsPath -Encoding UTF8
        Write-Log "  Windows Terminal font set to SauceCodePro Nerd Font Mono" "Gray"
    } catch {
        Write-Log "  WARNING: Could not configure Windows Terminal font: $_" "Yellow"
    }
}

# Configure Yazi with gruvbox theme and plugins
function Set-YaziConfiguration {
    if (-not (Test-ComponentSelected "Yazi")) {
        return
    }

    $yaziConfigDir = Join-Path $env:APPDATA "yazi\config"
    $yaziThemePath = Join-Path $yaziConfigDir "theme.toml"
    $yaziConfigPath = Join-Path $yaziConfigDir "yazi.toml"
    $yaziFlavorsDir = Join-Path $env:APPDATA "yazi\flavors"

    # Check if already configured
    if (Test-Path $yaziThemePath) {
        $existingTheme = Get-Content $yaziThemePath -Raw -ErrorAction SilentlyContinue
        if ($existingTheme -match "gruvbox") {
            Write-Log "  Yazi already configured with gruvbox theme, skipping..." "Yellow"
            return
        }
    }

    Write-Log "Configuring Yazi with gruvbox theme..." "Cyan"

    # Create config directories
    if (-not (Test-Path $yaziConfigDir)) {
        New-Item -Path $yaziConfigDir -ItemType Directory -Force | Out-Null
    }
    if (-not (Test-Path $yaziFlavorsDir)) {
        New-Item -Path $yaziFlavorsDir -ItemType Directory -Force | Out-Null
    }

    # Download gruvbox-dark flavor from yazi-rs/flavors
    $flavorDir = Join-Path $yaziFlavorsDir "gruvbox-dark.yazi"
    if (-not (Test-Path $flavorDir)) {
        Write-Log "  Downloading gruvbox-dark flavor..." "Gray"
        try {
            $flavorUrl = "https://github.com/yazi-rs/flavors/archive/refs/heads/main.zip"
            $flavorZip = Join-Path $env:TEMP "yazi-flavors.zip"
            $flavorExtract = Join-Path $env:TEMP "yazi-flavors"

            Invoke-WebRequest -Uri $flavorUrl -OutFile $flavorZip -UseBasicParsing
            if (Test-Path $flavorExtract) { Remove-Item $flavorExtract -Recurse -Force }
            Expand-Archive -Path $flavorZip -DestinationPath $flavorExtract -Force

            # Copy gruvbox-dark.yazi flavor
            $sourceFlavor = Join-Path $flavorExtract "flavors-main\gruvbox-dark.yazi"
            if (Test-Path $sourceFlavor) {
                Copy-Item -Path $sourceFlavor -Destination $flavorDir -Recurse -Force
                Write-Log "  Installed gruvbox-dark flavor" "Gray"
            }

            Remove-Item $flavorZip -Force -ErrorAction SilentlyContinue
            Remove-Item $flavorExtract -Recurse -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Log "  WARNING: Could not download gruvbox flavor: $_" "Yellow"
        }
    }

    # Create yazi.toml to use the gruvbox flavor
    $yaziConfig = @"
# Yazi configuration

[manager]
show_hidden = true
sort_by = "natural"
sort_sensitive = false
sort_dir_first = true

[preview]
max_width = 1000
max_height = 1000
"@

    # Create theme.toml to use gruvbox flavor
    $yaziTheme = @"
# Use gruvbox-dark flavor
[flavor]
use = "gruvbox-dark"
"@

    Set-Content -Path $yaziConfigPath -Value $yaziConfig -Encoding UTF8
    Set-Content -Path $yaziThemePath -Value $yaziTheme -Encoding UTF8
    Write-Log "  Yazi configured with gruvbox-dark theme" "Gray"
    Write-Log "  Config directory: $yaziConfigDir" "Gray"
}

# Configure Starship prompt in PowerShell profile
function Set-StarshipConfiguration {
    if (-not (Test-ComponentSelected "Starship")) {
        return
    }

    # Check if starship is available
    $starshipCmd = Get-Command starship -ErrorAction SilentlyContinue
    if (-not $starshipCmd) {
        Write-Log "  Starship not installed, skipping configuration..." "Yellow"
        return
    }

    # PowerShell 7 profile path
    $pwshProfileDir = Join-Path $env:USERPROFILE "Documents\PowerShell"
    $pwshProfilePath = Join-Path $pwshProfileDir "Microsoft.PowerShell_profile.ps1"

    # Windows PowerShell profile path
    $psProfileDir = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell"
    $psProfilePath = Join-Path $psProfileDir "Microsoft.PowerShell_profile.ps1"

    $starshipInit = 'Invoke-Expression (&starship init powershell)'

    foreach ($profileInfo in @(
        @{ Dir = $pwshProfileDir; Path = $pwshProfilePath; Name = "PowerShell 7" },
        @{ Dir = $psProfileDir; Path = $psProfilePath; Name = "Windows PowerShell" }
    )) {
        # Check if already configured
        if (Test-Path $profileInfo.Path) {
            $content = Get-Content $profileInfo.Path -Raw -ErrorAction SilentlyContinue
            if ($content -match "starship init") {
                Write-Log "  Starship already configured in $($profileInfo.Name) profile, skipping..." "Yellow"
                continue
            }
        }

        Write-Log "  Configuring Starship in $($profileInfo.Name) profile..." "Gray"

        # Ensure profile directory exists
        if (-not (Test-Path $profileInfo.Dir)) {
            New-Item -Path $profileInfo.Dir -ItemType Directory -Force | Out-Null
        }

        # Append starship init to profile
        Add-Content -Path $profileInfo.Path -Value "`n# Starship prompt`n$starshipInit" -Encoding UTF8
    }

    Write-Log "  Starship prompt configured" "Gray"
}

# Download and install Miniconda for Python environment management
function Install-Miniconda {
    if (-not (Test-ComponentSelected "Miniconda")) {
        return
    }

    Write-Log "Installing Miniconda..." "Cyan"

    $downloadUrl = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    $downloadPath = Join-Path $env:USERPROFILE "Downloads\Miniconda3-latest-Windows-x86_64.exe"
    $installPath = Join-Path $env:USERPROFILE "miniconda3"

    # Check if already installed
    $condaExePath = Join-Path $installPath "Scripts\conda.exe"
    if (Test-Path $condaExePath) {
        Write-Log "  Miniconda already installed, skipping..." "Yellow"
        return
    }

    # Ensure Downloads folder exists
    $downloadFolder = Split-Path $downloadPath -Parent
    if (-not (Test-Path $downloadFolder)) {
        New-Item -Path $downloadFolder -ItemType Directory -Force | Out-Null
    }

    # Download installer if not already present
    # Use temp file to prevent partial downloads from corrupting re-runs
    if (Test-Path $downloadPath) {
        # Verify file size is reasonable (>50MB for Miniconda)
        $fileSize = (Get-Item $downloadPath).Length
        if ($fileSize -gt 50MB) {
            Write-Log "  Miniconda installer already downloaded, skipping..." "Yellow"
        } else {
            $sizeMB = [math]::Round($fileSize/1MB)
            Write-Log "  Existing installer appears incomplete (${sizeMB}MB), re-downloading..." "Yellow"
            Remove-Item $downloadPath -Force -ErrorAction SilentlyContinue
        }
    }

    if (-not (Test-Path $downloadPath)) {
        Write-Log "  Downloading Miniconda installer..." "Gray"
        $tempDownloadPath = "$downloadPath.tmp"
        try {
            # Download to temp file first
            Invoke-WebRequest -Uri $downloadUrl -OutFile $tempDownloadPath -UseBasicParsing -TimeoutSec 600
            # Verify download completed (check size)
            $fileSize = (Get-Item $tempDownloadPath).Length
            if ($fileSize -lt 50MB) {
                throw "Downloaded file too small ($([math]::Round($fileSize/1MB))MB), likely incomplete"
            }
            # Atomic rename on success
            Move-Item -Path $tempDownloadPath -Destination $downloadPath -Force
        } catch {
            # Clean up partial download
            Remove-Item $tempDownloadPath -Force -ErrorAction SilentlyContinue
            Write-Log "ERROR: Failed to download Miniconda: $_" "Red"
            throw
        }
    }

    # Run silent installation (/S = silent, /D = install directory, must be last argument)
    Write-Log "  Running Miniconda installer (silent)..." "Gray"
    $installerArgs = "/InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=`"$installPath`""
    $process = Start-Process -FilePath $downloadPath -ArgumentList $installerArgs -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        Write-Log "ERROR: Miniconda install failed (code: $($process.ExitCode))" "Red"
        exit $process.ExitCode
    }

    Write-Log "  Miniconda installed to $installPath" "Gray"

    # Set PYTHONUTF8=1 to prevent encoding errors on Windows
    # This fixes 'charmap' codec errors when conda reads config files with non-ASCII bytes
    $existingUtf8 = [Environment]::GetEnvironmentVariable("PYTHONUTF8", "User")
    if ($existingUtf8 -ne "1") {
        Write-Log "  Setting PYTHONUTF8=1 for UTF-8 encoding support..." "Gray"
        [Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
        $env:PYTHONUTF8 = "1"
    }
}

function Install-CondaDevTools {
    if (-not (Test-ComponentSelected "Miniconda")) {
        return
    }

    $condaHook = Join-Path $env:USERPROFILE "miniconda3\shell\condabin\conda-hook.ps1"
    $condaExe = Join-Path $env:USERPROFILE "miniconda3\Scripts\conda.exe"

    if (-not (Test-Path $condaExe)) {
        Write-Log "  Miniconda not installed, skipping dev tools" "Yellow"
        return
    }

    # Check if dev tools are already installed
    $constructorPath = Join-Path $env:USERPROFILE "miniconda3\Scripts\constructor.exe"
    $condaBuildPath = Join-Path $env:USERPROFILE "miniconda3\Scripts\conda-build.exe"
    $nodejsPath = Join-Path $env:USERPROFILE "miniconda3\node.exe"
    if ((Test-Path $constructorPath) -and (Test-Path $condaBuildPath) -and (Test-Path $nodejsPath)) {
        Write-Log "  Conda dev tools already installed, skipping..." "Yellow"
        return
    }

    Write-Log "Installing conda dev tools (constructor, conda-build, nodejs)..." "Cyan"

    # Run in a subshell to avoid polluting the current session
    # PYTHONUTF8=1 prevents encoding errors with non-ASCII config files
    $installScript = @"
`$ErrorActionPreference = 'Stop'
`$env:PYTHONUTF8 = '1'
& '$condaHook'
conda activate
conda tos accept
conda install --yes constructor conda-build nodejs
"@

    try {
        $result = powershell -NoProfile -ExecutionPolicy Bypass -Command $installScript 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Log "  PowerShell subshell failed, trying direct conda.exe..." "Yellow"
            & $condaExe tos accept
            & $condaExe install --yes constructor conda-build nodejs
        }
        Write-Log "  Conda dev tools installed successfully" "Gray"
    } catch {
        Write-Log "ERROR: Failed to install conda dev tools: $_" "Red"
        throw
    }
}

function Confirm-ClAvailableAfterCondaActivation {
    Write-Log "Verifying cl.exe remains on PATH after conda activation..." "Cyan"

    $condaExe = Join-Path $env:USERPROFILE "miniconda3\Scripts\conda.exe"
    if (-not (Test-Path $condaExe)) {
        Write-Log "  Miniconda not installed, skipping conda/cl.exe interaction check" "Yellow"
        return
    }

    # Run conda's PowerShell hook and check cl.exe in a fresh, isolated pwsh
    # process - not the current session - so this reflects what a real user
    # gets after opening a new terminal and activating conda.
    $checkScript = @"
`$ErrorActionPreference = 'Stop'
(& '$condaExe' 'shell.powershell' 'hook') | Out-String | Invoke-Expression
conda activate base
`$cl = Get-Command cl.exe -ErrorAction SilentlyContinue
if (`$cl) {
    Write-Output "FOUND:`$(`$cl.Source)"
} else {
    Write-Output "NOTFOUND"
}
"@

    # Check if pwsh (PowerShell 7+) is available, otherwise fall back to Windows PowerShell
    $pwshCmd = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($pwshCmd) {
        $result = & pwsh -NoProfile -Command $checkScript 2>&1
    } else {
        $result = & powershell -NoProfile -Command $checkScript 2>&1
    }

    if ($result -match "^FOUND:(.+)$") {
        Write-Log "  cl.exe still reachable after conda activation: $($matches[1])" "Green"
    } else {
        Write-Log "ERROR: cl.exe NOT found on PATH after conda activate base" "Red"
        Write-Log "  This usually means a conda package's activate.d script is overriding PATH order." "Red"
        Write-Log "  Output: $result" "Red"
        exit 1
    }
}

function Install-AdminTools {
    # Neovim - text editor (requires admin for Program Files install)
    if (Test-ComponentSelected "Neovim") {
        $nvimPath = Join-Path $env:ProgramFiles "Neovim\bin\nvim.exe"
        if (Test-Path $nvimPath) {
            Write-Log "  Neovim already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing Neovim..." "Gray"
            $nvimArgs = @(
                "install", "Neovim.Neovim",
                "--source", "winget", "--silent",
                "--accept-source-agreements", "--accept-package-agreements"
            )
            & winget @nvimArgs
            Test-WinGetResult "Neovim"
        }
    }

    # Yazi - terminal file manager (requires admin)
    if (Test-ComponentSelected "Yazi") {
        $yaziPath = Join-Path $env:ProgramFiles "yazi\yazi.exe"
        if (Test-Path $yaziPath) {
            Write-Log "  Yazi already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing Yazi..." "Gray"
            $yaziArgs = @(
                "install", "sxyazi.yazi",
                "--source", "winget", "--silent",
                "--accept-source-agreements", "--accept-package-agreements"
            )
            & winget @yaziArgs
            Test-WinGetResult "Yazi"
        }
    }

    # Eza - modern ls replacement (requires admin)
    if (Test-ComponentSelected "Eza") {
        $ezaPath = Join-Path $env:ProgramFiles "eza\eza.exe"
        if (Test-Path $ezaPath) {
            Write-Log "  Eza already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing Eza..." "Gray"
            $ezaArgs = @(
                "install", "eza-community.eza",
                "--source", "winget", "--silent",
                "--accept-source-agreements", "--accept-package-agreements"
            )
            & winget @ezaArgs
            Test-WinGetResult "Eza"
        }
    }

    # Ripgrep - fast grep replacement (requires admin)
    if (Test-ComponentSelected "Ripgrep") {
        $rgCmd = Get-Command rg -ErrorAction SilentlyContinue
        if ($rgCmd) {
            Write-Log "  Ripgrep already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing Ripgrep..." "Gray"
            $rgArgs = @(
                "install", "BurntSushi.ripgrep.GNU",
                "--source", "winget", "--silent",
                "--accept-source-agreements", "--accept-package-agreements"
            )
            & winget @rgArgs
            Test-WinGetResult "Ripgrep"
        }
    }

    # Tree-sitter CLI - parser generator tool
    if (Test-ComponentSelected "TreeSitter") {
        $tsCmd = Get-Command tree-sitter -ErrorAction SilentlyContinue
        if ($tsCmd) {
            Write-Log "  Tree-sitter CLI already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing Tree-sitter CLI..." "Gray"
            $tsArgs = @(
                "install", "tree-sitter.tree-sitter-cli",
                "--source", "winget", "--silent",
                "--accept-source-agreements", "--accept-package-agreements"
            )
            & winget @tsArgs
            Test-WinGetResult "Tree-sitter CLI"
        }
    }

    # Starship - cross-shell prompt
    if (Test-ComponentSelected "Starship") {
        $starshipCmd = Get-Command starship -ErrorAction SilentlyContinue
        if ($starshipCmd) {
            Write-Log "  Starship already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing Starship..." "Gray"
            $starshipArgs = @(
                "install", "Starship.Starship",
                "--source", "winget", "--silent",
                "--accept-source-agreements", "--accept-package-agreements"
            )
            & winget @starshipArgs
            Test-WinGetResult "Starship"
        }
    }

    # PowerShell 7+ - modern cross-platform PowerShell
    if (Test-ComponentSelected "PowerShell7") {
        # Query GitHub API for latest stable version
        $latestVersion = $null
        try {
            $apiUrl = "https://api.github.com/repos/PowerShell/PowerShell/releases/latest"
            $releaseInfo = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing
            $latestVersion = $releaseInfo.tag_name -replace '^v', ''
        } catch {
            Write-Log "WARNING: Could not query latest PowerShell version from GitHub: $_" "Yellow"
            Write-Log "  Skipping PowerShell 7 installation - run script again when GitHub is reachable" "Yellow"
        }

        if ($latestVersion) {
            # Check if installed and get current version
            $pwshCmd = Get-Command pwsh -ErrorAction SilentlyContinue
            $pwshExePath = Join-Path $env:ProgramFiles "PowerShell\7\pwsh.exe"
            $installedVersion = $null
            $needsInstall = $true

            if ($pwshCmd) {
                $installedVersion = (& $pwshCmd.Source --version 2>$null) -replace 'PowerShell ', ''
            } elseif (Test-Path $pwshExePath) {
                $installedVersion = (& $pwshExePath --version 2>$null) -replace 'PowerShell ', ''
            }

            if ($installedVersion) {
                if ([version]$installedVersion -ge [version]$latestVersion) {
                    Write-Log "  PowerShell 7 is up to date ($installedVersion), skipping..." "Yellow"
                    $needsInstall = $false
                } else {
                    Write-Log "  PowerShell 7 upgrade available: $installedVersion -> $latestVersion" "Cyan"
                }
            }

            if ($needsInstall) {
                Write-Log "  Installing PowerShell $latestVersion via MSI..." "Gray"
                # Use MSI installer directly - winget MSIX can fail on some VDI configurations
                $pwshVersion = $latestVersion
                $pwshMsiUrl = "https://github.com/PowerShell/PowerShell/releases/download/" +
                    "v$pwshVersion/PowerShell-$pwshVersion-win-x64.msi"
                $pwshMsiPath = Join-Path $env:TEMP "PowerShell-$pwshVersion-win-x64.msi"

                try {
                    if (-not (Test-Path $pwshMsiPath)) {
                        Write-Log "    Downloading PowerShell $pwshVersion MSI..." "Gray"
                        Invoke-WebRequest -Uri $pwshMsiUrl -OutFile $pwshMsiPath -UseBasicParsing
                    }

                    Write-Log "    Running MSI installer (silent)..." "Gray"
                    $msiArgs = "/i `"$pwshMsiPath`" /quiet " +
                        "ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=1 " +
                        "ADD_FILE_CONTEXT_MENU_RUNPOWERSHELL=1 " +
                        "ENABLE_PSREMOTING=0 REGISTER_MANIFEST=1 USE_MU=0 ENABLE_MU=0"
                    $msiProcess = Start-Process msiexec.exe -ArgumentList $msiArgs -Wait -PassThru
                    if ($msiProcess.ExitCode -ne 0) {
                        Write-Log "ERROR: PowerShell 7 MSI install failed (code: $($msiProcess.ExitCode))" "Red"
                        exit $msiProcess.ExitCode
                    }
                    Write-Log "  PowerShell 7 installed successfully" "Gray"
                } catch {
                    Write-Log "ERROR: Failed to install PowerShell 7: $_" "Red"
                    throw
                }
            }
        }
    }

    # psmux - native Windows terminal multiplexer (tmux for Windows)
    if (Test-ComponentSelected "Psmux") {
        $psmuxCmd = Get-Command psmux -ErrorAction SilentlyContinue
        if (-not $psmuxCmd) {
            $psmuxCmd = Get-Command tmux -ErrorAction SilentlyContinue
        }
        if ($psmuxCmd) {
            Write-Log "  psmux already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing psmux (Windows tmux)..." "Gray"
            $psmuxArgs = @(
                "install", "--id", "marlocarlo.psmux",
                "--source", "winget", "--silent",
                "--accept-source-agreements", "--accept-package-agreements"
            )
            & winget @psmuxArgs
            Test-WinGetResult "psmux"
        }
    }

    # SourceCodePro Nerd Font - required for Yazi/terminal icons
    if (Test-ComponentSelected "NerdFont") {
        # Check for font files in both system and user fonts directories
        $systemFontsDir = "$env:SystemRoot\Fonts"
        $userFontsDir = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
        $systemFontFiles = Get-ChildItem "$systemFontsDir\SauceCodePro*.ttf" -ErrorAction SilentlyContinue
        $userFontFiles = Get-ChildItem "$userFontsDir\SauceCodePro*.ttf" -ErrorAction SilentlyContinue
        if ($systemFontFiles -or $userFontFiles) {
            Write-Log "  SourceCodePro Nerd Font already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing SourceCodePro Nerd Font..." "Gray"
            $fontUrl = "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.5.1/SourceCodePro.zip"
            $downloadsDir = Join-Path $env:USERPROFILE "Downloads"
            $fontZip = Join-Path $downloadsDir "SourceCodePro.zip"
            $fontExtract = Join-Path $downloadsDir "SourceCodePro"

            try {
                # Skip download if cached zip exists
                if (Test-Path $fontZip) {
                    Write-Log "    Using cached download from $fontZip" "Gray"
                } else {
                    Write-Log "    Downloading from GitHub..." "Gray"
                    Invoke-WebRequest -Uri $fontUrl -OutFile $fontZip -UseBasicParsing
                }

                Write-Log "    Extracting fonts to $fontExtract..." "Gray"
                if (Test-Path $fontExtract) { Remove-Item $fontExtract -Recurse -Force }
                Expand-Archive -Path $fontZip -DestinationPath $fontExtract -Force

                # Ensure user fonts directory exists
                if (-not (Test-Path $userFontsDir)) {
                    New-Item -Path $userFontsDir -ItemType Directory -Force | Out-Null
                }

                # Registry paths for font registration
                $hklmFontsKey = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
                $hkcuFontsKey = "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"

                # Ensure HKCU fonts key exists
                if (-not (Test-Path $hkcuFontsKey)) {
                    New-Item -Path $hkcuFontsKey -Force | Out-Null
                }

                Write-Log "    Installing fonts to system and user directories..." "Gray"
                Get-ChildItem -Path $fontExtract -Filter "*.ttf" | ForEach-Object {
                    $fontFile = $_
                    $fontName = [System.IO.Path]::GetFileNameWithoutExtension($fontFile.Name)
                    $registryName = "$fontName (TrueType)"

                    # Copy to system fonts directory (C:\Windows\Fonts)
                    $systemDest = Join-Path $systemFontsDir $fontFile.Name
                    Copy-Item -Path $fontFile.FullName -Destination $systemDest -Force -ErrorAction SilentlyContinue

                    # Copy to user fonts directory
                    $userDest = Join-Path $userFontsDir $fontFile.Name
                    Copy-Item -Path $fontFile.FullName -Destination $userDest -Force

                    # Register in HKLM (all users) - uses just filename for system fonts
                    $hklmParams = @{
                        Path = $hklmFontsKey
                        Name = $registryName
                        Value = $fontFile.Name
                        Type = "String"
                        ErrorAction = "SilentlyContinue"
                    }
                    Set-ItemProperty @hklmParams

                    # Register in HKCU (current user) - uses full path for user fonts
                    Set-ItemProperty -Path $hkcuFontsKey -Name $registryName -Value $userDest -Type String
                }

                Write-Log "    Fonts copied to $systemFontsDir" "Gray"
                Write-Log "    Fonts copied to $userFontsDir" "Gray"
                Write-Log "    Fonts registered in HKLM and HKCU" "Gray"
                Write-Log "  SourceCodePro Nerd Font installed successfully" "Gray"
            } catch {
                Write-Log "ERROR: Failed to install SourceCodePro Nerd Font: $_" "Red"
                throw
            }
        }
    }

    # VS Build Tools requires elevation - installs system-wide components,
    # SDKs, and redistributables under HKLM. Must run here, not in the
    # user-context Install-UserTools.
    if (Test-ComponentSelected "BuildTools") {
        $vswherePath = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
        $hasVCTools = $false

        if (Test-Path $vswherePath) {
            $vcToolsPath = & $vswherePath -products * `
                -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
                -property installationPath 2>$null
            $hasVCTools = -not [string]::IsNullOrWhiteSpace($vcToolsPath)
        }

        if ($hasVCTools) {
            Write-Log "  VS 2022 Build Tools with C++ workload already installed, skipping..." "Yellow"
        } else {
            Write-Log "  Installing VS 2022 Build Tools with C++ workload (may take minutes)..." "Gray"
            $vsOverride = "--quiet --wait --norestart " +
                "--add Microsoft.VisualStudio.Workload.VCTools " +
                "--add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 " +
                "--add Microsoft.VisualStudio.Component.Windows11SDK.22621"
            & winget install Microsoft.VisualStudio.2022.BuildTools --source winget --scope machine `
                --accept-source-agreements --accept-package-agreements --override $vsOverride
            Test-WinGetResult "Visual Studio 2022 Build Tools"

            Update-PathFromRegistry
            $vcToolsPath = & $vswherePath -products * `
                -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
                -property installationPath 2>$null
            if ([string]::IsNullOrWhiteSpace($vcToolsPath)) {
                Write-Log ("ERROR: VS 2022 Build Tools installed, " +
                    "but C++ (VC.Tools.x86.x64) component not found by vswhere") "Red"
                exit 1
            }
            Write-Log "  Verified C++ toolset at: $vcToolsPath" "Gray"
        }
    }
}

function Confirm-CppToolchain {
    Write-Log "Verifying C++ toolchain..." "Cyan"

    $vswherePath = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path $vswherePath)) {
        Write-Log "ERROR: vswhere.exe not found - VS Installer itself is missing" "Red"
        exit 1
    }

    $vcToolsPath = & $vswherePath -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath 2>$null
    if ([string]::IsNullOrWhiteSpace($vcToolsPath)) {
        Write-Log "ERROR: VC.Tools.x86.x64 component not registered" "Red"
        exit 1
    }
    Write-Log "  Component registered at: $vcToolsPath" "Gray"

    $vcvars = Join-Path $vcToolsPath "VC\Auxiliary\Build\vcvars64.bat"
    if (-not (Test-Path $vcvars)) {
        Write-Log "ERROR: vcvars64.bat missing at $vcvars" "Red"
        exit 1
    }

    $clOutput = cmd.exe /c "`"$vcvars`" >nul 2>&1 && cl.exe 2>&1"
    if ($clOutput -notmatch "Microsoft.*C/C\+\+.*Compiler") {
        Write-Log "ERROR: cl.exe did not execute correctly after vcvars64.bat activation" "Red"
        Write-Log "Output: $clOutput" "Red"
        exit 1
    }
    Write-Log "  cl.exe verified: $(($clOutput -split "`n")[0].Trim())" "Green"
}

function Enable-PersistentCppToolchain {
    if (-not (Test-ComponentSelected "BuildTools")) {
        return
    }

    # Check if already persisted (INCLUDE env var is a good indicator)
    $existingInclude = [Environment]::GetEnvironmentVariable("INCLUDE", "Machine")
    if ($existingInclude -and $existingInclude -match "Microsoft Visual Studio") {
        Write-Log "C++ toolchain environment already persisted, skipping..." "Yellow"
        return
    }

    Write-Log "Persisting C++ toolchain environment to machine scope..." "Cyan"

    $vswherePath = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    $vsInstallPath = & $vswherePath -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath 2>$null
    if ([string]::IsNullOrWhiteSpace($vsInstallPath)) {
        Write-Log "ERROR: Cannot persist C++ toolchain - VC.Tools component not found" "Red"
        exit 1
    }

    $vcvars = Join-Path $vsInstallPath "VC\Auxiliary\Build\vcvars64.bat"
    if (-not (Test-Path $vcvars)) {
        Write-Log "ERROR: vcvars64.bat not found at $vcvars" "Red"
        exit 1
    }

    # Run vcvars64.bat in a cmd subshell and capture the resulting environment
    $envOutput = cmd.exe /c "`"$vcvars`" >nul 2>&1 && set"
    $vcEnv = @{}
    foreach ($line in $envOutput) {
        if ($line -match "^([^=]+)=(.*)$") {
            $vcEnv[$matches[1]] = $matches[2]
        }
    }

    if (-not $vcEnv.ContainsKey("Path")) {
        Write-Log "ERROR: vcvars64.bat did not produce a PATH - activation failed" "Red"
        exit 1
    }

    # Merge only the NEW entries vcvars64.bat adds into the machine PATH,
    # rather than overwriting PATH wholesale with a session-specific value.
    $currentMachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $currentEntries = $currentMachinePath -split ";" | Where-Object { $_ }
    $vcEntries = $vcEnv["Path"] -split ";" | Where-Object { $_ }
    $newEntries = $vcEntries | Where-Object { $_ -notin $currentEntries }

    if ($newEntries.Count -gt 0) {
        $updatedPath = ($currentEntries + $newEntries) -join ";"
        [Environment]::SetEnvironmentVariable("Path", $updatedPath, "Machine")
        Write-Log "  Added $($newEntries.Count) new PATH entries for MSVC toolchain" "Gray"
    } else {
        Write-Log "  MSVC PATH entries already present in machine PATH" "Yellow"
    }

    # cl.exe also needs INCLUDE/LIB/LIBPATH to actually compile anything
    # (not just launch and print its banner) - persist these too.
    foreach ($varName in @("INCLUDE", "LIB", "LIBPATH")) {
        if ($vcEnv.ContainsKey($varName)) {
            [Environment]::SetEnvironmentVariable($varName, $vcEnv[$varName], "Machine")
            Write-Log "  Persisted $varName" "Gray"
        }
    }

    # Broadcast WM_SETTINGCHANGE so already-running processes (e.g. Explorer)
    # notice immediately. Any *new* process after this point picks up the
    # registry values regardless of the broadcast.
    if (-not ([System.Management.Automation.PSTypeName]'Win32.NativeMethods').Type) {
        Add-Type -Namespace Win32 -Name NativeMethods -MemberDefinition @"
            [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
            public static extern IntPtr SendMessageTimeout(
                IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam,
                uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
"@
    }
    $result = [UIntPtr]::Zero
    $null = [Win32.NativeMethods]::SendMessageTimeout(
        [IntPtr]0xffff, 0x1a, [UIntPtr]::Zero, "Environment", 2, 5000, [ref]$result)

    Update-PathFromRegistry
    Write-Log "  C++ toolchain environment persisted to machine scope" "Green"
}

# === Main Execution ===

Write-Log "=== Windows 11 VDI Setup ===" "Green"
Write-Log "Log file: $script:LogPath" "Gray"

if ($AdminPhase) {
    # Running in elevated subprocess - perform admin tasks only
    if (-not (Test-Administrator)) {
        Write-Log "ERROR: -AdminPhase requires Administrator privileges" "Red"
        exit 1
    }
    Write-Log "Running admin phase with elevated privileges..." "Green"
    try {
        Enable-DeveloperMode
        Set-EdgeConfiguration
        Install-WinGet
        Install-AdminTools
        # Confirm-CppToolchain
        Enable-PersistentCppToolchain
        Write-Log "=== Admin Phase Complete ===" "Green"
        exit 0
    } catch {
        Write-Log "ERROR: Admin phase failed with exception: $_" "Red"
        Write-Log "Stack trace: $($_.ScriptStackTrace)" "Red"
        exit 1
    }
}

# Main entry point - run as standard user
Write-Log "Running as standard user: $env:USERNAME" "Green"
Write-Log "Components to install: $($script:Components -join ', ')" "Gray"

# Step 1: Launch elevated subprocess for admin tasks
if (-not (Test-Administrator)) {
    Write-Log "Elevating to install system-wide tools (UAC prompt)..." "Cyan"
    Write-Log "An Administrator PowerShell window will open." "Yellow"
    $scriptPath = $MyInvocation.MyCommand.Path

    # Build command with proper escaping to prevent injection
    # Forward -Install parameter to admin subprocess
    $installArg = if ($Install -and $Install.Count -gt 0) { " -Install $($Install -join ',')" } else { "" }
    $escapedScript = $scriptPath -replace "'", "''"
    $escapedLog = $script:LogPath -replace "'", "''"
    $adminCommand = "& '$escapedScript' -AdminPhase -LogFile '$escapedLog'" +
        $installArg + "; exit `$LASTEXITCODE"
    $encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($adminCommand))

    # Use -NoExit so window stays open for any additional UAC prompts; the admin phase script will exit explicitly
    $adminArgs = @(
        "-ExecutionPolicy", "Bypass", "-NoExit", "-EncodedCommand", $encodedCommand
    )
    $adminProcess = Start-Process powershell -Verb RunAs -ArgumentList $adminArgs -Wait -PassThru

    if ($adminProcess.ExitCode -ne 0) {
        Write-Log "ERROR: Admin phase failed (code: $($adminProcess.ExitCode))" "Red"
        Write-Log "Check log file for details: $script:LogPath" "Yellow"
        Write-Host "`n--- Last 20 lines of log ---" -ForegroundColor Cyan
        Get-Content $script:LogPath -Tail 20 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
        exit $adminProcess.ExitCode
    }
    Write-Log "Admin phase completed successfully." "Green"
}

# Step 2: Continue with user-level installations
try {
    Install-UserWinGet
    Install-UserTools
    Set-VSCodeSettings
    Initialize-VSCode
    Set-WindowsTerminalFont
    Set-YaziConfiguration
    Set-StarshipConfiguration
    Initialize-WindowsTerminalSettings
    Install-Miniconda
    Install-CondaDevTools
    # Confirm-ClAvailableAfterCondaActivation

    # Final PATH refresh so all tools are immediately available
    Update-PathFromRegistry

    Write-Log "=== Setup Complete ===" "Green"
    Write-Log "Full log available at: $script:LogPath" "Gray"
} catch {
    Write-Log "ERROR: User phase failed with exception: $_" "Red"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" "Red"
    exit 1
}
