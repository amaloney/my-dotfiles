---
name: python/types
description: Type annotation rules - parameters, returns, optionals, callables
invocation: auto
---

# Type Annotations

Handoff: `next: done`.

All functions: typed parameters + `-> Type` returns.

| Rule           | Use                        | Avoid              |
| -------------- | -------------------------- | ------------------ |
| Optional       | `Type \| None`             | `Optional[Type]`   |
| Callables      | `collections.abc.Callable` | `typing.Callable`  |
| Self-returning | `typing.Self`              | forward ref string |

Instance attrs: declare in `__init__` when not obvious from assignment.

## `from __future__ import annotations`

Omit it by default. Required only for: forward references that can't be reordered, circular type
imports (prefer `TYPE_CHECKING` + quotes), or annotation syntax above the project's Python floor. On
floors ≥ 3.10 it is almost never needed — unions (`X | None`), builtin generics (`dict[str, Any]`),
and `Self` all evaluate natively. Runtime introspection (`get_type_hints`, pydantic-style consumers)
is simpler without it, and 3.14+ makes deferred evaluation the native default (PEP 649) — don't add
the import by habit.

## Returns

- Paths are `pathlib.Path`, never `str` — function params, return values, and config constants alike.
- Single return type per function. `dict | None` mixes success/failure into the return — raise a typed
  exception for failure instead. `dict` for the happy path, exception for the failure path.
- A tuple return for "result + metadata" (e.g. `(data, rate_limit)`) is one coherent type, not a mixed
  return — acceptable when both are always produced.

[[python/naming]] [[debugging/references/python]]
