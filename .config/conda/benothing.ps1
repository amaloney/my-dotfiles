<#
.SYNOPSIS
    Cleanup of Anaconda/Miniconda installations.

.DESCRIPTION
    Uninstalls Anaconda or Miniconda on the user's system (assumes "Just Me" installation),
    then removes leftover files, directories, environment variables, and PATH entries.

.PARAMETER DryRun
    Preview what would be deleted without actually deleting (like conda --dry-run).

.PARAMETER Force
    Skip confirmation prompts.

.PARAMETER SkipUninstaller
    Skip running the uninstaller, only clean up leftover files.

.PARAMETER Name
    Only uninstall installations matching this name (e.g., "Anaconda3", "Miniconda3").
    If not specified, uninstalls all conda-related installations.

.EXAMPLE
    .\nuke-conda.ps1 -DryRun
    Preview what would be deleted (no changes made).

.EXAMPLE
    .\nuke-conda.ps1 -Force
    Run full cleanup without prompts.

.EXAMPLE
    .\nuke-conda.ps1 -SkipUninstaller
    Only clean up leftovers (assumes uninstaller already ran).

.EXAMPLE
    .\nuke-conda.ps1 -Name "Anaconda3"
    Only uninstall Anaconda3, leaving Miniconda3 intact.
#>

param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$SkipUninstaller,
    [string]$Name = ""
)

$ErrorActionPreference = "Stop"

# Configuration loaded from benothing.yaml (single source of truth)
$script:ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:ConfigFile = Join-Path $script:ScriptDir "benothing.yaml"

function Get-YamlList {
    param([string]$Key)
    # Try yq first (cross-platform), then powershell-yaml module
    if (Get-Command yq -ErrorAction SilentlyContinue) {
        $result = & yq -r ".$Key[]? // empty" $script:ConfigFile 2>$null
        if ($result) { return $result -split "`n" | Where-Object { $_ } }
    }
    if (Get-Module -ListAvailable -Name powershell-yaml) {
        Import-Module powershell-yaml -ErrorAction SilentlyContinue
        $yaml = Get-Content $script:ConfigFile -Raw | ConvertFrom-Yaml
        $parts = $Key -split '\.'
        $value = $yaml
        foreach ($part in $parts) { $value = $value.$part }
        if ($value) { return $value }
    }
    return $null
}

function Initialize-Config {
    $yamlLoaded = $false

    if (Test-Path $script:ConfigFile) {
        $items = Get-YamlList "common.user_profile_items"
        if ($items) {
            $yamlLoaded = $true
            # Common (all platforms)
            $script:UserProfileItems = $items
            $script:UserProfilePatterns = Get-YamlList "common.user_profile_patterns"
            $script:EnvVarsToRemove = Get-YamlList "common.env_vars"

            # Windows-specific
            $script:LocalAppDataDirs = Get-YamlList "windows.appdata_local"
            $script:RoamingAppDataDirs = Get-YamlList "windows.appdata_roaming"
            $script:SystemConfigDirs = Get-YamlList "windows.system_config_dirs"
            $script:StartMenuPatterns = Get-YamlList "windows.start_menu_patterns"

            # Build install dirs from common + windows
            $common = Get-YamlList "common.install_dirs"
            $winSystem = Get-YamlList "windows.install_dirs"
            $script:InstallDirs = @()
            foreach ($dir in $common) {
                $script:InstallDirs += Join-Path $env:USERPROFILE $dir
            }
            if ($winSystem) { $script:InstallDirs += $winSystem }

            Write-Host "Loaded configuration from $script:ConfigFile" -ForegroundColor Green
        }
    }

    if (-not $yamlLoaded) {
        # Fallback to hardcoded defaults (kept in sync with YAML)
        if (Test-Path $script:ConfigFile) {
            Write-Host "Note: yq/powershell-yaml not found, using hardcoded defaults" -ForegroundColor Yellow
        }
        Initialize-DefaultConfig
    }
}

function Initialize-DefaultConfig {
    # Hardcoded defaults - kept in sync with benothing.yaml
    $script:UserProfileItems = @(
        ".anaconda", ".astropy", ".conda", ".condarc", ".continuum", ".copilot",
        ".ipynb_checkpoints", ".ipython", ".jupyter", ".matplotlib",
        ".python_history", ".virtual_documents"
    )
    $script:UserProfilePatterns = @(".spyder*")
    $script:LocalAppDataDirs = @("conda", "conda-anaconda-tos", "ContinuumIO")
    $script:RoamingAppDataDirs = @(".anaconda", "jupyter")
    $script:EnvVarsToRemove = @(
        "CONDA_DEFAULT_ENV", "CONDA_PREFIX", "CONDA_SHLVL", "CONDA_EXE",
        "CONDA_PYTHON_EXE", "CONDA_PROMPT_MODIFIER", "_CE_CONDA", "_CE_M",
        "CONDARC", "CONDA_ROOT_PREFIX", "CONDA_ENVS_DIRS", "CONDA_PKGS_DIRS",
        "CONDA_CHANNELS", "CONDA_SUBDIR", "CONDA_BLD_PATH", "CONDA_CHANGEPS1",
        "CONDA_ENV_PROMPT", "CONDA_AUTO_ACTIVATE_BASE", "CONDA_AUTO_STACK",
        "CONDA_AUTO_UPDATE_CONDA", "CONDA_ALWAYS_YES", "CONDA_DRY_RUN",
        "CONDA_QUIET", "CONDA_VERBOSITY", "CONDA_JSON", "CONDA_SSL_VERIFY",
        "CONDA_TOKEN", "CONDA_AUTH_USERNAME", "CONDA_AUTH_PASSWORD",
        "CONDA_SOLVER", "CONDA_EXPERIMENTAL_SOLVER", "CONDA_DEFAULT_THREADS",
        "CONDA_EXECUTE_THREADS", "CONDA_REPODATA_THREADS", "CONDA_VERIFY_THREADS",
        "CONDA_OFFLINE", "CONDA_CHANNEL_PRIORITY", "CONDA_CHANNEL_ALIAS",
        "CONDA_SAFETY_CHECKS", "CONDA_EXTRA_SAFETY_CHECKS", "CONDA_NO_PLUGINS",
        "CONDA_REGISTER_ENVS", "CONDA_SHORTCUTS"
    )
    $script:InstallDirs = @(
        "$env:USERPROFILE\anaconda3", "$env:USERPROFILE\miniconda3",
        "$env:USERPROFILE\miniforge3", "$env:USERPROFILE\mambaforge",
        "$env:USERPROFILE\Anaconda3", "$env:USERPROFILE\Miniconda3",
        "$env:ProgramData\anaconda3", "$env:ProgramData\miniconda3",
        "$env:ProgramData\miniforge3", "C:\ProgramData\Anaconda3",
        "C:\ProgramData\Miniconda3", "$env:USERPROFILE\.conda"
    )
    $script:SystemConfigDirs = @("C:\ProgramData\conda")
    $script:StartMenuPaths = @(
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Anaconda3*",
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Miniconda3*",
        "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Anaconda3*",
        "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Miniconda3*"
    )
}

# Total steps for progress tracking
$TotalSteps = 7
$CurrentStep = 0

function Update-MainProgress {
    param(
        [string]$Activity,
        [string]$Status
    )
    $script:CurrentStep++
    $percent = [math]::Round(100 * ($script:CurrentStep / $TotalSteps))
    Write-Progress -Id 0 -Activity "Nuke Conda" -Status $Activity `
        -PercentComplete $percent -CurrentOperation $Status
}

function Remove-LargeDirectory {
    param(
        [string]$Path,
        [switch]$DryRun
    )

    if (-not (Test-Path $Path)) {
        return $false
    }

    $item = Get-Item -LiteralPath $Path -Force
    if (-not $item.PSIsContainer) {
        if ($DryRun) {
            Write-Host "  [DryRun] file $Path" -ForegroundColor Yellow
        } else {
            Write-Host "  [DELETE] file $Path" -ForegroundColor Red
            Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
        }
        return $true
    }

    # Count files for progress (quick estimate using top-level only for speed)
    $files = Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue
    $totalFiles = @($files).Count

    if ($DryRun) {
        Write-Host "  [DryRun] dir  $Path ($totalFiles files)" -ForegroundColor Yellow
        return $true
    }

    Write-Host "  [DELETE] dir  $Path ($totalFiles files)" -ForegroundColor Red

    if ($totalFiles -gt 100) {
        # Large directory - show progress
        $deleted = 0
        foreach ($file in $files) {
            Remove-Item -LiteralPath $file.FullName -Force -ErrorAction SilentlyContinue
            $deleted++
            if ($deleted % 50 -eq 0) {
                $pct = [math]::Round(100 * ($deleted / $totalFiles))
                Write-Progress -Id 1 -ParentId 0 -Activity "Deleting $Path" `
                    -Status "$deleted / $totalFiles files" -PercentComplete $pct
            }
        }
        Write-Progress -Id 1 -ParentId 0 -Activity "Deleting $Path" -Completed
        # Remove empty directories
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        # Small directory - just delete
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
    }

    return $true
}

function Remove-ItemSafely {
    param(
        [string]$Path,
        [switch]$DryRun
    )

    if (Test-Path $Path) {
        Remove-LargeDirectory -Path $Path -DryRun:$DryRun
        return $true
    } else {
        Write-Host "  [SKIP]   not found: $Path" -ForegroundColor DarkGray
        return $false
    }
}

function Remove-EnvVarSafely {
    param(
        [string]$Name,
        [switch]$DryRun
    )

    $value = [Environment]::GetEnvironmentVariable($Name, 'User')
    if ($value) {
        if ($DryRun) {
            Write-Host "  [DryRun] $Name = $value" -ForegroundColor Yellow
        } else {
            Write-Host "  [DELETE] $Name = $value" -ForegroundColor Red
            [Environment]::SetEnvironmentVariable($Name, $null, 'User')
        }
        return $true
    } else {
        Write-Host "  [SKIP]   $Name (not set)" -ForegroundColor DarkGray
        return $false
    }
}

function Confirm-Cleanup {
    if (-not $Force -and -not $DryRun) {
        Write-Host "This will permanently uninstall Anaconda/Miniconda and delete all related files." `
            -ForegroundColor Red
        Write-Host "Run with -DryRun first to see what would be deleted." `
            -ForegroundColor Yellow
        $confirm = Read-Host "Type 'yes' to continue"
        if ($confirm -ne 'yes') {
            Write-Host "Aborted." -ForegroundColor Yellow
            exit 0
        }
    }
}

function Invoke-Uninstallers {
    Update-MainProgress -Activity "Running Uninstallers" -Status "Checking registry..."
    Write-Host "`n=== Running Anaconda/Miniconda Uninstallers ===" -ForegroundColor Green

    if ($SkipUninstaller) {
        Write-Host "  [SKIP]   Uninstaller skipped (-SkipUninstaller)" -ForegroundColor DarkGray
        return
    }

    $matchPattern = if ($Name) { $Name } else { "conda" }
    $regPath = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    $entries = Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue |
        Get-ItemProperty |
        Where-Object { $_.DisplayName -match $matchPattern }

    if (-not $entries) {
        $searchTerm = if ($Name) { $Name } else { "Anaconda/Miniconda" }
        Write-Host "  [SKIP]   No $searchTerm installations found in registry." -ForegroundColor DarkGray
        return
    }

    $i = 0
    $total = @($entries).Count
    foreach ($entry in $entries) {
        $i++
        $pct = [math]::Round(100 * ($i / $total))
        Write-Progress -Id 1 -ParentId 0 -Activity "Uninstalling" `
            -Status $entry.DisplayName -PercentComplete $pct
        if ($DryRun) {
            Write-Host "  [DryRun] Would uninstall: $($entry.DisplayName)" -ForegroundColor Yellow
        } else {
            Write-Host "  [UNINST] $($entry.DisplayName)" -ForegroundColor Cyan
            # NSIS uninstallers ignore -WindowStyle; use cmd /c start /min to suppress the window
            $uninstallCmd = $entry.UninstallString
            Start-Process -FilePath "cmd.exe" `
                -ArgumentList "/c", "start", "/min", "/wait", "`"Uninstall`"", "`"$uninstallCmd`"", "/S" `
                -Wait -WindowStyle Hidden -ErrorAction SilentlyContinue
        }
    }
    Write-Progress -Id 1 -ParentId 0 -Activity "Uninstalling" -Completed
}

function Remove-UserProfileItems {
    Update-MainProgress -Activity "Cleaning User Profile" -Status "$env:USERPROFILE"
    Write-Host "`n=== Cleaning User Profile ===" -ForegroundColor Green

    $i = 0
    foreach ($item in $UserProfileItems) {
        $i++
        $path = Join-Path $env:USERPROFILE $item
        $pct = [math]::Round(100 * ($i / $UserProfileItems.Count))
        Write-Progress -Id 1 -ParentId 0 -Activity "User Profile" -Status $item -PercentComplete $pct
        Remove-ItemSafely -Path $path -DryRun:$DryRun | Out-Null
    }
    Write-Progress -Id 1 -ParentId 0 -Activity "User Profile" -Completed

    foreach ($pattern in $UserProfilePatterns) {
        Get-Item -Path (Join-Path $env:USERPROFILE $pattern) -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-ItemSafely -Path $_.FullName -DryRun:$DryRun | Out-Null
        }
    }
}

function Remove-LocalAppDataItems {
    Update-MainProgress -Activity "Cleaning AppData\Local" -Status "$env:LOCALAPPDATA"
    Write-Host "`n=== Cleaning AppData\Local ===" -ForegroundColor Green

    $i = 0
    foreach ($dir in $LocalAppDataDirs) {
        $i++
        $path = Join-Path $env:LOCALAPPDATA $dir
        $pct = [math]::Round(100 * ($i / $LocalAppDataDirs.Count))
        Write-Progress -Id 1 -ParentId 0 -Activity "AppData\Local" -Status $dir -PercentComplete $pct
        Remove-ItemSafely -Path $path -DryRun:$DryRun | Out-Null
    }
    Write-Progress -Id 1 -ParentId 0 -Activity "AppData\Local" -Completed

    Get-ChildItem $env:LOCALAPPDATA -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "conda" } |
        ForEach-Object {
            Remove-ItemSafely -Path $_.FullName -DryRun:$DryRun | Out-Null
        }
}

function Remove-RoamingAppDataItems {
    Update-MainProgress -Activity "Cleaning AppData\Roaming" -Status "$env:APPDATA"
    Write-Host "`n=== Cleaning AppData\Roaming ===" -ForegroundColor Green

    $i = 0
    foreach ($dir in $RoamingAppDataDirs) {
        $i++
        $path = Join-Path $env:APPDATA $dir
        $pct = [math]::Round(100 * ($i / $RoamingAppDataDirs.Count))
        Write-Progress -Id 1 -ParentId 0 -Activity "AppData\Roaming" -Status $dir -PercentComplete $pct
        Remove-ItemSafely -Path $path -DryRun:$DryRun | Out-Null
    }
    Write-Progress -Id 1 -ParentId 0 -Activity "AppData\Roaming" -Completed
}

function Remove-StartMenuShortcuts {
    Update-MainProgress -Activity "Cleaning Start Menu" -Status "Shortcuts"
    Write-Host "`n=== Cleaning Start Menu ===" -ForegroundColor Green

    foreach ($pattern in $StartMenuPaths) {
        Get-Item -Path $pattern -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-ItemSafely -Path $_.FullName -DryRun:$DryRun | Out-Null
        }
    }
}

function Remove-CondaEnvVars {
    Update-MainProgress -Activity "Cleaning Environment Variables" -Status "User variables"
    Write-Host "`n=== Cleaning Environment Variables ===" -ForegroundColor Green

    $i = 0
    foreach ($var in $EnvVarsToRemove) {
        $i++
        $pct = [math]::Round(100 * ($i / $EnvVarsToRemove.Count))
        Write-Progress -Id 1 -ParentId 0 -Activity "Environment Variables" -Status $var -PercentComplete $pct
        Remove-EnvVarSafely -Name $var -DryRun:$DryRun | Out-Null
    }
    Write-Progress -Id 1 -ParentId 0 -Activity "Environment Variables" -Completed
}

function Remove-CondaFromPath {
    Update-MainProgress -Activity "Cleaning PATH" -Status "User PATH"
    Write-Host "`n=== Cleaning PATH ===" -ForegroundColor Green

    $userPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
    if (-not $userPath) { return }

    $allParts = $userPath -split ';' | Where-Object { $_ }
    $condaParts = $allParts | Where-Object {
        $_ -match 'anaconda' -or $_ -match 'miniconda' -or $_ -match 'conda'
    }
    $cleanParts = $allParts | Where-Object {
        $_ -notmatch 'anaconda' -and $_ -notmatch 'miniconda' -and $_ -notmatch 'conda'
    }

    if (-not $condaParts) {
        Write-Host "  [SKIP]   No conda entries in PATH" -ForegroundColor DarkGray
        return
    }

    foreach ($part in $condaParts) {
        if ($DryRun) {
            Write-Host "  [DryRun] PATH: $part" -ForegroundColor Yellow
        } else {
            Write-Host "  [DELETE] PATH: $part" -ForegroundColor Red
        }
    }
    if (-not $DryRun) {
        [Environment]::SetEnvironmentVariable('PATH', ($cleanParts -join ';'), 'User')
    }
}

function Write-CompletionMessage {
    Write-Progress -Id 0 -Activity "Nuke Conda" -Completed
    Write-Host "`n=== Done ===" -ForegroundColor Green
    if ($DryRun) {
        Write-Host "Run without -DryRun to perform actual cleanup." -ForegroundColor Yellow
    } else {
        Write-Host "Cleanup complete. You may need to restart your terminal." -ForegroundColor Green
    }
}

function Main {
    Initialize-Config
    Confirm-Cleanup
    Invoke-Uninstallers
    Remove-UserProfileItems
    Remove-LocalAppDataItems
    Remove-RoamingAppDataItems
    Remove-StartMenuShortcuts
    Remove-CondaEnvVars
    Remove-CondaFromPath
    Write-CompletionMessage
}

Main
