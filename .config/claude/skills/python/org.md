---
name: python/org
description: File organization - config.py, utils.py patterns
invocation: auto
---

# Organization

## Constants

| Scope           | Location                      |
| --------------- | ----------------------------- |
| Project-wide    | `config.py`                   |
| Module-specific | Top of module (after imports) |
| Inline/mid-file | **NEVER**                     |

**config.py**: constants, settings, type aliases, enums. **utils.py**: shared functions.

## Colors (package_build_observer)

Colors in `config.py` → `Gruvbox` class. See `textual-ui.md`. No hardcoded hex in Python — use `Gruvbox.X`. TCSS hex
must match constants. Status mappings (`DEP_STATUS_COLORS`, `LEGEND_ENTRIES`) validated at import.

[[python/structure]] [[python/naming]]
