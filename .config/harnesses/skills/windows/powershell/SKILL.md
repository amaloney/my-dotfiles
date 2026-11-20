---
name: windows/powershell
description: Gotchas, patterns, and best practices for Windows PowerShell (.ps1) scripts
invocation: auto
extensions: [".ps1", ".psm1", ".psd1"]
keywords: ["powershell"]
---

# Windows PowerShell

Handoff: `next: done`.

**Line limit**: 120 characters max. Break long lines with backtick `` ` `` continuation or splatting.

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

Prefer PowerShell over batch (`RMDIR /Q /S` fails silently). Track survivors with try/catch per-item.

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

## Command Injection Prevention

When interpolating values into `-Command` strings, escape single quotes to prevent injection:

```powershell
# Escape ASCII ' plus typographic variants (U+2018, U+2019, U+201A, U+201B)
# Use single-quoted string so \u escapes pass to .NET regex (PS 5.1 doesn't parse \u in double quotes)
# This is encoding-independent (PS 5.1 reads BOM-less UTF-8 as ANSI, corrupting literal Unicode chars)
$quotePattern = '[''‘’‚‛]'
$safeValue = $userInput -replace $quotePattern, '$0$0'

Start-Process powershell.exe -ArgumentList @(
    '-Command', "Write-Host '$safeValue'"
)
```

## Control Flow Style

Multi-line braces for control flow statements:

```powershell
# Preferred
if (-not $selection) {
    return
}

# Avoid single-line block statements
if (-not $selection) { return }
```

**Exception**: Loop guards with `continue`/`break` are acceptable single-line:

```powershell
foreach ($item in $items) {
    if (-not $item.IsValid) { continue }
    if ($item.Count -eq 0) { continue }
    # main logic
}
```

Inline conditional assignments are fine:

```powershell
$idx = if ($found -ge 0) { $found } else { 0 }
```

## Assignment Alignment

Do not align `=` signs in consecutive assignments or hashtables:

```powershell
# Avoid
$displayName   = $entry.Value
$folderName    = $entry.Key
$path          = $item.Path

# Preferred
$displayName = $entry.Value
$folderName = $entry.Key
$path = $item.Path

# Same for hashtables
@{
    DisplayName = $entry.Value
    FolderName = $folderName
    Path = $entry.Key
}
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

## Performance

### Pre-compile Regex

For repeated regex operations, pre-compile at script scope:

```powershell
$script:myRegex = [regex]::new('^prefix-(\d+)$', 'Compiled')

# In function (fast)
$match = $script:myRegex.Match($input)
if ($match.Success) { $match.Groups[1].Value }

# Avoid in loops (recompiles each time)
if ($input -match '^prefix-(\d+)$') { $Matches[1] }
```

### .NET Over Cmdlets

For hot paths, .NET methods are faster (benchmarked in pwsh 7.5):

| Cmdlet                        | .NET Alternative                        | Speedup |
| ----------------------------- | --------------------------------------- | ------- |
| `Get-Content $f -Raw`         | `[IO.File]::ReadAllText($f)`            | ~25x    |
| `Get-Date`                    | `[datetime]::Now`                       | ~6x     |
| `Split-Path $p -Parent`       | `[IO.Path]::GetDirectoryName($p)`       | ~3x     |
| `Split-Path $p -Leaf`         | `[IO.Path]::GetFileName($p)`            | ~3x     |
| `Set-Content $f $text`        | `[IO.File]::WriteAllText($f, $text)`    | ~10x    |
| `Remove-Item $f`              | `[IO.File]::Delete($f)`                 | ~5x     |
| `Test-Path $f`                | `[IO.File]::Exists($f)`                 | ~4x     |
| `Test-Path $d -PathType Cont` | `[IO.Directory]::Exists($d)`            | ~4x     |
| `Get-ChildItem $d`            | `[IO.Directory]::GetFiles($d, '*.ext')` | ~8x     |
| `Join-Path $a $b`             | `[IO.Path]::Combine($a, $b)`            | ~3x     |

### Loop Patterns

```powershell
# Fast - foreach statement
foreach ($item in $collection) { Process $item }

# Slow - pipeline overhead
$collection | ForEach-Object { Process $_ }

# Fast - indexed comparison
for ($i = 0; $i -lt $arr1.Count; $i++) {
    if ($arr1[$i] -ne $arr2[$i]) { $changed = $true; break }
}

# Slow - string join comparison
if (($arr1 -join '|') -ne ($arr2 -join '|')) { $changed = $true }
```

### Cache Expensive Objects

```powershell
$script:wshell = $null

function Get-ShortcutTarget($lnkPath) {
    if ($null -eq $script:wshell) {
        $script:wshell = New-Object -ComObject WScript.Shell
    }
    $script:wshell.CreateShortcut($lnkPath).TargetPath
}
```

### String Methods Over Regex

For simple checks, string methods are faster:

```powershell
# Fast
if ($name.StartsWith('prefix')) { }
if ($name.EndsWith('.txt')) { }
if ($name.Contains('needle')) { }

# Slower (regex compilation)
if ($name -match '^prefix') { }
```

## Docker Testing

Test scripts on PowerShell without a Windows machine:

```bash
# .NET SDK includes pwsh (smaller, faster pull)
docker run -it mcr.microsoft.com/dotnet/sdk:9.0 pwsh

# Syntax validation
docker run --rm -v "$(pwd):/scripts:ro" mcr.microsoft.com/dotnet/sdk:9.0 pwsh -NoProfile -Command '
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    "/scripts/myscript.ps1", [ref]$null, [ref]$errors)
if ($errors) { $errors | ForEach-Object { Write-Error $_.Message }; exit 1 }
Write-Output "Syntax OK"
'

# Standalone PowerShell image
docker run -it mcr.microsoft.com/powershell:latest pwsh

# Windows Server Core with PowerShell 5.1 (Windows containers only)
docker run -it mcr.microsoft.com/windows/servercore:ltsc2022 powershell
```

Note: Linux containers run pwsh 7.x. Windows Forms/GUI scripts require Windows.

## Template

`#Requires -Version 5.1`, param block, `$ErrorActionPreference = "Stop"`, re-entry guard, try/catch/finally, explicit
exit.
