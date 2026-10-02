---
name: windows
description: Windows orchestrator - routes to PowerShell, Batch, or .NET testing agents
invocation: auto
---

# Windows Router

## Registry

| Skill                      | Purpose          | Triggers                                |
| -------------------------- | ---------------- | --------------------------------------- |
| [[windows/powershell]]     | Modern scripting | .ps1, JSON/XML, REST, complex logic     |
| [[windows/batch]]          | Legacy/universal | .bat/.cmd, simple ops, bootstrap, no PS |
| [[windows/dotnet-testing]] | .NET tests       | MSTest, NUnit, xUnit, C#                |

## Bootstrap Pattern

Batch → PowerShell bootstrap (full path, `%*` forwarding): [[windows/batch]].

## Paths

| Var     | Batch           | PowerShell         |
| ------- | --------------- | ------------------ |
| Home    | `%USERPROFILE%` | `$env:USERPROFILE` |
| AppData | `%APPDATA%`     | `$env:APPDATA`     |
| Temp    | `%TEMP%`        | `$env:TEMP`        |

## Execution

**Prescriptive** — load skills first, do NOT explore first, spawn sub-agents:

1. Match task → skill (use Registry table)
2. For each step:
   `Agent({ name: "windows-<step>", prompt: "Load [[windows/<skill>]] first. <task> + <prev artifact>" })`
3. Sub-agent loads skill → acts (no "exploring" preamble)
4. Pass artifacts between agents
5. Return after final agent

Example: "Create installer" → batch (install.bat) → powershell (setup.ps1)
