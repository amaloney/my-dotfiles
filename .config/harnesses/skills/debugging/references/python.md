# Python Bug Patterns

Language-specific tables for [[debugging]]. Loaded only for Python tasks.

## Common Bugs {#common-bugs}

| Pattern                          | Bug                             | Fix                        |
| -------------------------------- | ------------------------------- | -------------------------- |
| Mutable default                  | `def f(x=[]):`                  | `x=None`; `x = x or []`    |
| Late binding                     | `[lambda: i for i in range(3)]` | `lambda i=i: i`            |
| Shadow builtin {#shadow-builtin} | `list = []`                     | Rename                     |
| Identity                         | `x is []`                       | `x == []`                  |
| Reference                        | `b = a` mutates both            | `b = a.copy()`             |
| Bare except {#bare-except}       | Catches `KeyboardInterrupt`     | `except Exception as exc:` |
| None access                      | `obj.method().attr`             | Guard with walrus/if       |

## Infinite Loops

| Pattern                               | Fix                                  |
| ------------------------------------- | ------------------------------------ |
| Status polling (only expected states) | Handle ALL terminal states + timeout |
| Queue without visited                 | Track visited set                    |
| Condition never met                   | Add timeout/max iterations           |

## TUI/GUI Memory Leaks

| Pattern                  | Fix                           |
| ------------------------ | ----------------------------- |
| Unbounded widget mount   | Cap count, remove oldest      |
| Event log accumulation   | Track count, remove when full |
| Markup with user content | `markup=False` for untrusted  |

## Async

Missing `await` → add it | Blocking in async → `run_in_executor`

## Imports

Circular → move inside function | Stale `.pyc` → `find . -name "*.pyc" -delete`

## Detection

```bash
rg -n "\._[a-z][a-z_]+\(" --type py | grep -v "self\._\|cls\._"  # Underscore typos
rg -n "except:" --type py                                        # Bare excepts
ruff check --select F401,F821 src/                               # Unused/undefined
```

**Debug**: `breakpoint()` | `from rich import inspect; inspect(obj)`

[[python/style]] [[python/testing]] [[python/property-testing]] [[python/types]] [[python/errors]]
