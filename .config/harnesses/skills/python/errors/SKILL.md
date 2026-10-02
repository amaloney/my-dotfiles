---
name: python/errors
description: Exception handling patterns
invocation: auto
---

# Exceptions

Always `except Exception as exc:` + log. Never bare `except:` or silent `pass`.

## Multi-Failure Fetch Pattern

One logical result with several failure modes → single exit:

| Pattern | Verdict |
| --- | --- |
| `data = None` before try; each except only logs; single `return data` at end | GOOD |
| `return None` inside each except branch | BAD — repeated exits hide the shape |

```python
data = None
try:
    data = fetch(...)
except FileNotFoundError:
    logger.warning(...)
except ValueError as exc:
    logger.warning(...)

if data and cache_dir:
    write_cache(...)

return data
```

[[debugging/references/python]]
