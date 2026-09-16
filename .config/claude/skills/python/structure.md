---
name: python/structure
description: File structure - line length, imports, layout, comments
invocation: auto
---

# Structure

Lines <120. Single return at end.

## File Order (strict)

```python
# 1. Imports
# 2. TYPE_CHECKING block (if needed)
# 3. Module constants (ALL_CAPS) — NEVER inline
# 4. Module-level functions
# 5. Classes (attrs → methods)
```

**Constants:** Top of module after imports, or in `config.py`. NEVER mid-file.

## Comments

Only when WHY is non-obvious. No tombstones, no decorative blocks.

[[python/org]] [[python/types]]
