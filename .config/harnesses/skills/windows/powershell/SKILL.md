---
name: windows/powershell
description: Gotchas, patterns, and best practices for Windows PowerShell (.ps1) scripts
invocation: auto
---

# Windows PowerShell

- **Error handling**: `$ErrorActionPreference = "Stop"`
- **Parameters**: Full names (`Get-ChildItem -Recurse` not `gci -r`)
- **Exit**: Always `exit 0` or `exit 1` explicitly

## Exit Codes & Errors

```powershell
$LASTEXITCODE   # From external programs
$?              # Boolean from cmdlets
try { cmd -ErrorAction Stop } catch { Write-Error "Failed: $_"; exit 1 }
```

## Output & Strings

| Pattern          | Notes                                |
| ---------------- | ------------------------------------ |
| `$null = cmd`    | Suppress (faster than `\| Out-Null`) |
| `"Hello $name"`  | Interpolated                         |
| `'Hello $name'`  | Literal                              |
| `"$($obj.prop)"` | Subexpression for properties         |

## Environment Variables

```powershell
$env:VAR = "value"                                       # Session
$env:VAR = $null                                         # Remove
[Environment]::SetEnvironmentVariable("VAR","val","User") # Persistent
```

## File Deletion

**Prefer PowerShell over batch** — `RMDIR /Q /S` fails silently on permission/attribute issues:

```powershell
# Robust deletion with error tracking
$Survivors = @()
Get-ChildItem -Path $Target -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        Remove-Item -Path $_.FullName -Force -Recurse -ErrorAction Stop
    } catch {
        $Survivors += $_.FullName
    }
}
if ($Survivors) { Write-Warning "Failed to delete: $($Survivors -join ', ')" }
```

## JSON & Paths

```powershell
$data = Get-Content f.json | ConvertFrom-Json
$json = $obj | ConvertTo-Json -Depth 10
$full = Join-Path $env:USERPROFILE ".config"
Test-Path $path -PathType Container/Leaf
```

## External Programs

```powershell
& "C:\Program Files\app.exe" arg1    # Call operator for paths with spaces
Start-Process app.exe -Wait          # Block until exit
Start-Process app.exe -Verb RunAs    # Elevated
```

## Re-entry Guard

```powershell
if ($env:_SCRIPT_RUNNING) { return }
$env:_SCRIPT_RUNNING = "1"
try { <# body #> } finally { $env:_SCRIPT_RUNNING = $null }
```

## Gotchas

| Pattern        | Notes                                      |
| -------------- | ------------------------------------------ |
| `$a -eq 2`     | Filters arrays, returns matches (not bool) |
| `$null -eq $a` | Correct order (not `$a -eq $null`)         |
| `$list += $x`  | O(n) - use ArrayList for large             |
| `$script:x`    | Child scopes copy parent vars              |
| `. $hook`      | Space after dot required for sourcing      |

## Common Paths

`$env:USERPROFILE` `$env:APPDATA` `$env:LOCALAPPDATA` `$env:TEMP` `$PSScriptRoot`

## Conda

```powershell
$hook = Join-Path $env:CONDA_PREFIX "shell\condabin\conda-hook.ps1"
if (Test-Path $hook) { . $hook; conda activate $env:CONDA_PREFIX }
```

## Modules

```powershell
# MyModule.psm1
function Public-Func { "exported" }
function Private-Helper { "internal" }
Export-ModuleMember -Function Public-Func

Import-Module .\MyModule.psm1 -Force
$script:var = "module scope"                         # Within module only
```

## Registry

```powershell
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion"
Set-ItemProperty -Path "HKCU:\Environment" -Name "VAR" -Value "val"
Test-Path "HKLM:\SOFTWARE\MyApp"
New-Item -Path "HKLM:\SOFTWARE" -Name "MyApp"
Remove-ItemProperty -Path "HKCU:\Environment" -Name "VAR"
```

## WMI/CIM

```powershell
Get-CimInstance Win32_OperatingSystem | Select Caption,Version
Get-CimInstance Win32_Process | Where Name -eq "notepad.exe"
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="calc.exe"}
Get-CimInstance Win32_Service | Where State -eq "Running"
```

## Task Scheduler

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\script.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "3am"
Register-ScheduledTask -TaskName "DailyBackup" -Action $action -Trigger $trigger -User "SYSTEM"
Unregister-ScheduledTask -TaskName "DailyBackup" -Confirm:$false
Get-ScheduledTask | Where TaskName -like "*Backup*"
```

## Template

```powershell
#Requires -Version 5.1
param([string]$Param = "default")
$ErrorActionPreference = "Stop"
if ($env:_SCRIPT_RUNNING) { exit 0 }
$env:_SCRIPT_RUNNING = "1"
try { <# main #> } catch { Write-Error "Failed: $_"; exit 1 } finally { $env:_SCRIPT_RUNNING = $null }
exit 0
```
