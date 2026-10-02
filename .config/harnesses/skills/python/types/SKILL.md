---
name: python/types
description: Type annotation rules - parameters, returns, optionals, callables
invocation: auto
---

# Type Annotations

All functions: typed parameters + `-> Type` returns.

| Rule           | Use                        | Avoid              |
| -------------- | -------------------------- | ------------------ |
| Optional       | `Type \| None`             | `Optional[Type]`   |
| Callables      | `collections.abc.Callable` | `typing.Callable`  |
| Self-returning | `typing.Self`              | forward ref string |

Instance attrs: declare in `__init__` when not obvious from assignment.

## Returns

- Paths are `pathlib.Path`, never `str` — function params, return values, and config constants alike.
- Single return type per function. `dict | None` mixes success/failure into the return — raise a typed
  exception for failure instead. `dict` for the happy path, exception for the failure path.
- A tuple return for "result + metadata" (e.g. `(data, rate_limit)`) is one coherent type, not a mixed
  return — acceptable when both are always produced.

[[python/naming]] [[debugging/references/python]]
