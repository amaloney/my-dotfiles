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

[[python/naming]] [[python/bugs#common-bugs]]
