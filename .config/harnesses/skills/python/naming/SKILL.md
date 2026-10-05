---
name: python/naming
description: Naming conventions - variables, constants, underscore rules
invocation: auto
---

# Naming

| Rule                      | Good                    | Bad                      |
| ------------------------- | ----------------------- | ------------------------ |
| No single-letter vars     | `for item in items`     | `for i in items`         |
| No cryptic abbreviations  | `for record in records` | `for rec in records`     |
| Prefix constants          | `URL_PYPI_API`          | `PYPI_API_URL`           |
| No reflexive `_`          | `def get_card(self):`   | `def _get_card(self):`   |

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

## Cryptic Abbreviations

Spell names out. If a reader must mentally expand a name, the name is wrong. This applies to every binding —
variables, parameters, loop targets, `except ... as` names, `with ... as` names, and comprehension variables.

```python
# BAD
for rec in records:
    persist(rec)
with urlopen(req) as resp:
    shutil.copyfileobj(resp, fh)

# GOOD
for record in records:
    persist(record)
with urlopen(request) as response:
    shutil.copyfileobj(response, file_handle)
```

| Bad   | Good                      |
| ----- | ------------------------- |
| `rec` | `record`                  |
| `req` | `request` / `http_request` |
| `resp` | `response`               |
| `fh`  | `file_handle`             |
| `exc` | `error`                   |
| `ret` | `result`                  |
| `hdr` | `header`                  |
| `buf` | `buffer`                  |

Allowed idioms — established vocabulary, not abbreviations of a local concept: `args`, `kwargs`, `argv`, `url`,
`api`, `id`.

**Enforcement gap — tooling does not catch this.** Ruff pep8-naming (`N`) only checks case conventions; `rec` is
legal lowercase and passes. Detection is a mandatory review-time gate, run on every file you create or edit:

```bash
grep -nE '\b(rec|req|resp|fh|exc|ret|hdr|buf)\b' <file>
```

Clean output = pass. When review rejects an abbreviation not in the list, add it to the table and the pattern.

## Underscore Prefix

No true private in Python. Public API is controlled by `__all__`, not underscores. **Default to NO underscore.**
Only add `_` when:

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
builtins or true framework internals. For every `_name`:

| Question                              | Action                                       |
| ------------------------------------- | -------------------------------------------- |
| Called only within this file?         | Rename public anyway — hiding buys nothing   |
| Another module would use it?          | Make public                                  |
| Genuinely internal mutable state?     | Keep underscore (only case)                  |

**Module-level functions are not private.** Same rule as methods: default to NO underscore. Only two legitimate uses:
a `@property` backing field, or an explicit internal API contract the module publishes.

| Pattern | Underscore? | Reason |
| --- | --- | --- |
| `def parse_rate_limit():` | NO | Module helper; importable, not private |
| `def build_request():` | NO | Same |
| `self._value` backing `@property value` | YES | Property backing field |
| `def _register_impl():` in a plugin package | MAYBE | Explicit internal API contract |

[[python/types]] [[debugging/references/python]]
