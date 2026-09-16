---
name: windows/batch
description: Windows batch scripting (.bat/.cmd) and CLI command reference
invocation: auto
---

# Windows Batch & CLI

## Essentials

```batch
@ECHO OFF
SETLOCAL EnableDelayedExpansion
EXIT /B 0                           REM Always explicit (not GOTO :eof)
```

## Delayed Expansion (Critical)

Variables expand at **parse time**. Inside IF/FOR blocks, use `!var!`:

```batch
FOR /F "tokens=*" %%G IN ('dir /b') DO ( ECHO !count! & SET /A count+=1 )
```

## Variables & Exit Codes

| Pattern | Notes |
|---------|-------|
| `SET "_var=value"` | Quotes prevent trailing spaces |
| `IF DEFINED _var` | Check before use |
| `EXIT /B 0/1` | Success/error |
| `IF %ERRORLEVEL% EQU 0` | Exact match (ERRORLEVEL 1 means >=1) |
| `>NUL 2>&1` | Suppress output (order matters!) |

## Control Flow

```batch
CALL other.bat                      REM Returns after completion
CALL :label                         REM Subroutine
start "" "app.exe"                  REM First "" is title (required!)
IF cond ( cmd ) ELSE ( other )      REM ELSE same line as )
FOR %%G IN (*.txt) DO ECHO %%G      REM Files (uppercase avoids A-F conflict)
FOR /F "usebackq delims=" %%I IN (`cmd`) DO SET VAR=%%I  REM Capture output
```

## Escaping

`^&` `^\|` `^<` `^>` | `%%` (in batch) | `^^!` (delayed expansion) | `^(` `^)`

## Built-in Variables

`%USERPROFILE%` `%LOCALAPPDATA%` `%APPDATA%` `%TEMP%` `%PROGRAMDATA%` `%SYSTEMROOT%` `%ERRORLEVEL%`

## Re-entry Guard

```batch
IF DEFINED _SCRIPT_RUNNING EXIT /B 0
SET _SCRIPT_RUNNING=1
REM ... body ...
SET _SCRIPT_RUNNING=
```

## PowerShell from Batch

```batch
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" ^
    -NoProfile -ExecutionPolicy Bypass -File "script.ps1"
```

## CLI Commands

| Task | Command |
|------|---------|
| List users | `net user` |
| Profile paths | `reg query "HKLM\...\ProfileList"` |
| Copy | `robocopy` (most robust) |
| Delete dir | `rmdir /s /q` |
| Find | `where`, `findstr` (regex) |
| Registry | `reg query/add/delete` |
| Processes | `tasklist /v`, `taskkill /im name.exe /f` |
| Services | `sc query/start/stop` |
| Network | `ipconfig /all`, `netstat -an`, `net use` |
| Check admin | `net session >nul 2>&1` then check errorlevel |

## Gotchas

- **RMDIR no wildcards**: Use `FOR /D` loop
- **GOTO breaks IF blocks**: Put before block, not inside
- **START quoting**: First quoted arg is window title
- **Debug first**: `ECHO VAR=%VAR%` before guessing

## Template

```batch
@ECHO OFF
SETLOCAL EnableDelayedExpansion
IF DEFINED _SCRIPT_RUNNING EXIT /B 0
SET _SCRIPT_RUNNING=1
REM Main logic
:end
SET _SCRIPT_RUNNING=
ENDLOCAL
EXIT /B 0
```
