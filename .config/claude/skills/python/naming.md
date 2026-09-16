---
name: python/naming
description: Naming conventions - variables, constants, underscore rules
invocation: auto
---

# Naming

| Rule                  | Good                      | Bad                    |
| --------------------- | ------------------------- | ---------------------- |
| No single-letter vars | `for version in versions` | `for v in versions`    |
| Prefix constants      | `URL_PYPI_API`            | `PYPI_API_URL`         |
| No reflexive `_`      | `def get_card(self):`     | `def _get_card(self):` |

**Underscore**: No true private in Python. Reserve `_` for genuinely internal state only. Ask: called only in this file?
→ still doesn't need hiding. Another module would use it? → make public. `__all__` controls public API.

[[python/types]] [[python/bugs#shadow-builtin]]
