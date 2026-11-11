---
name: cli-verification
description: Verify CLI tool flags before completing tasks that add new options
invocation: auto
keywords: ["cli", "flags", "options", "winget", "installer", "package manager", "command line"]
---

# CLI Verification

**When**: Before completing any task that adds or modifies CLI flags/options.

**Why**: Flag names and valid values vary by tool, version, and platform. Guessing leads to silent failures or wrong
behavior (e.g., `--installer-type msi` vs `wix` for winget).

## Verification by Shell

### Bash / POSIX

```bash
<tool> --help                      # Most tools
<tool> <subcommand> --help         # Subcommands (git, docker, kubectl)
man <tool>                         # Full docs
tldr <tool>                        # Quick examples (if installed)
```

### PowerShell

```powershell
Get-Help <Cmdlet> -Full            # Native cmdlets
Get-Command <Cmdlet> -Syntax       # Quick syntax
<tool> --help                      # External tools (git, winget)
<tool> /?                          # Windows-native tools
```

### Batch / CMD

```batch
<tool> /?                          # Most Windows tools
<tool> --help                      # Cross-platform tools
help <command>                     # Built-in commands
```

## Package Managers

| Manager | List available options                          |
| ------- | ----------------------------------------------- |
| winget  | `winget show --id <pkg>` (shows installer type) |
| apt     | `apt show <pkg>`, `apt-cache policy <pkg>`      |
| brew    | `brew info <pkg>`, `brew options <pkg>`         |
| conda   | `conda search <pkg> --info`                     |
| choco   | `choco info <pkg>`                              |
| scoop   | `scoop info <pkg>`                              |

### Winget Installer Types

```powershell
winget show --id Microsoft.PowerShell
# Look for "Installer Type:" in output
# Valid types: msix, msi, wix, exe, zip, inno, nullsoft, burn
```

## Checklist Before Completion

When a task adds CLI flags:

1. **Unfamiliar flag?** Run `--help` or equivalent
2. **Package-specific value?** Query the package manifest (winget show, brew info)
3. **Platform-specific?** Verify flag exists on target platform
4. **Version-sensitive?** Check if flag was added in a recent version

## Common Mistakes

| Mistake                          | Prevention                                    |
| -------------------------------- | --------------------------------------------- |
| Assuming flag name from memory   | Always verify with `--help`                   |
| Generic type when specific needed| `winget show` reveals actual installer type   |
| Flag exists but wrong value      | Check allowed values in help output           |
| Works locally, fails remote      | Note platform/version in verification         |
