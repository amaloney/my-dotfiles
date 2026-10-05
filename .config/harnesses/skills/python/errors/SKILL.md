---
name: python/errors
description: Exception handling patterns
invocation: auto
---

# Exceptions

Handoff: `next: done`.

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

## Scoped Exceptions

Catch the narrowest exception the library exposes — `requests.RequestException`, `json.JSONDecodeError`,
`subprocess.CalledProcessError` — over broad `except Exception`. Broad catches mask programming errors
(typos, attribute errors) as fetch failures. Broad `except Exception` is reserved for aggregator
boundaries where one source must never sink the whole result.

[[debugging/references/python]]
