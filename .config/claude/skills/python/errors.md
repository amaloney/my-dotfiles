---
name: python/errors
description: Exception handling patterns
invocation: auto
---

# Exceptions

Always `except Exception as exc:` + log. Never bare `except:` or silent `pass`.

[[python/bugs#bare-except]] [[python/bugs#common-bugs]]
