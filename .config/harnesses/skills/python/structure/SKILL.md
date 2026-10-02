---
name: python/structure
description: File structure - line length, imports, layout, comments
invocation: auto
---

# Structure

Lines <120. **Single return at end** — unless an early return skips expensive work (DB query, API call, heavy
computation). Multiple returns for simple conditionals add cognitive load; consolidate to one.

## File Order (strict)

```python
# 1. Imports
# 2. TYPE_CHECKING block (if needed)
# 3. Module constants (ALL_CAPS) — NEVER inline
# 4. Module-level functions
# 5. Classes (attrs → methods)
```

**Constants:** Top of module after imports, or in `config.py`. NEVER mid-file.

## Functions

**Syntactic sugar adds complexity.** A one-liner helper that just wraps an expression doesn't reduce complexity — it
adds indirection. Inline it.

| Pattern                                    | Problem                | Fix                 |
| ------------------------------------------ | ---------------------- | ------------------- |
| `def get_x(): return obj.x`                | Wrapper adds nothing   | Inline `obj.x`      |
| `def csv_env(n): return {…comprehension…}` | Sugar, not abstraction | Inline at call site |

**When to extract:** Logic is reused 3+ times, OR name documents non-obvious intent, OR expression is complex enough to
obscure the calling code.

## Comments

Only when WHY is non-obvious. No tombstones, no decorative blocks.

[[python/org]] [[python/types]]
