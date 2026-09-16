---
name: windows
description: Windows orchestrator - routes to PowerShell or Batch agents
invocation: auto
---

# Windows Router

## Registry

| Skill | Purpose | Triggers |
|-------|---------|----------|
| [[windows/powershell]] | Modern scripting | .ps1, JSON, complex logic |
| [[windows/batch]] | Legacy/universal | .bat/.cmd, simple ops, no PS |

## Decision

| Need | Use | Why |
|------|-----|-----|
| JSON/XML, REST, complex logic | PowerShell | Native objects, cleaner |
| Universal, simple, bootstrap | Batch | No execution policy |

## Pipelines

| Task | Chain |
|------|-------|
| Automation | powershell |
| Legacy | batch |
| Installer | batch → powershell |

## Bootstrap Pattern

```batch
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" ^
    -NoProfile -ExecutionPolicy Bypass -File "%~dp0main.ps1" %*
```

## Paths

| Var | Batch | PowerShell |
|-----|-------|------------|
| Home | `%USERPROFILE%` | `$env:USERPROFILE` |
| AppData | `%APPDATA%` | `$env:APPDATA` |
| Temp | `%TEMP%` | `$env:TEMP` |

## Execution

**Prescriptive** — load skills first, do NOT explore first, spawn sub-agents:

1. Match task → pipeline (use Decision table)
2. For each step: `Agent({ name: "windows-<step>", prompt: "Load [[windows/<skill>]] first. <task> + <prev artifact>" })`
3. Sub-agent loads skill → acts (no "exploring" preamble)
4. Pass artifacts between agents
5. Return after final agent

Example: "Create installer" → batch (install.bat) → powershell (setup.ps1)
