---
name: python/naming
description: Naming conventions - variables, constants, underscore rules
invocation: auto
---

# Naming

| Rule                  | Good                  | Bad                    |
| --------------------- | --------------------- | ---------------------- |
| No single-letter vars | `for item in items`   | `for i in items`       |
| Prefix constants      | `URL_PYPI_API`        | `PYPI_API_URL`         |
| No reflexive `_`      | `def get_card(self):` | `def _get_card(self):` |

**Single-letter variables are NEVER acceptable.** Not in loops, not in comprehensions, not in lambdas. Code is read by
humans — `v`, `s`, `c`, `i`, `x` communicate nothing.

```python
# BAD
for i in items:
    process(i)
{s.lower() for v in values if (s := v.strip())}

# GOOD
for item in items:
    process(item)
{stripped.lower() for value in values if (stripped := value.strip())}
```

## Underscore Prefix

No true private in Python. **Default to NO underscore.** Only add `_` when:

- Name would shadow a builtin (`_id`, `_type`, `_input`)
- Explicitly signaling "framework internal, don't touch"

| Pattern               | Underscore? | Reason                                             |
| --------------------- | ----------- | -------------------------------------------------- |
| `self.layout`         | NO          | Instance attr, normal access                       |
| `self.upload_btn`     | NO          | UI widget, implementation detail but not "private" |
| `self.store`          | NO          | Injected dependency                                |
| `def on_click(self):` | NO          | Callback, called by framework                      |
| `def refresh(self):`  | NO          | Internal method, but not hiding anything           |
| `self._cache`         | MAYBE       | True internal state that would break if accessed   |

```python
# BAD - unnecessary underscores everywhere
self._layout = Column(self._card, self._button)
def _on_upload(self, event): ...
def _refresh(self): ...

# GOOD - clean, no ceremony
self.layout = Column(self.card, self.button)
def on_upload(self, event): ...
def refresh(self): ...
```

**Refactoring underscore-heavy code:** Remove `_` prefix from instance variables and methods. Keep only where shadowing
builtins or true framework internals.

[[python/types]] [[python/bugs#shadow-builtin]]
