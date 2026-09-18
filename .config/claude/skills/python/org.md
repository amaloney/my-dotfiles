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

## Colors

If using a color theme (e.g., Gruvbox), define colors in `config.py` as a class. No hardcoded hex in Python — use named constants.

[[python/structure]] [[python/naming]]
