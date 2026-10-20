---
name: python/naming
description: Naming conventions - variables, constants, underscore rules
invocation: auto
---

# Naming

Handoff: `next: done`.

| Rule                     | Good                    | Bad                    |
| ------------------------ | ----------------------- | ---------------------- |
| No single-letter vars    | `for item in items`     | `for i in items`       |
| No cryptic abbreviations | `for record in records` | `for rec in records`   |
| Prefix constants         | `URL_PYPI_API`          | `PYPI_API_URL`         |
| No reflexive `_`         | `def get_card(self):`   | `def _get_card(self):` |

**Single-letter variables NEVER acceptable** — `v`, `s`, `i`, `x` communicate nothing. Use `item`, `value`, `stripped`.

## Cryptic Abbreviations

Spell out. If reader must expand mentally, name is wrong. Applies to all bindings.

| Bad    | Good                       |
| ------ | -------------------------- |
| `rec`  | `record`                   |
| `req`  | `request` / `http_request` |
| `resp` | `response`                 |
| `fh`   | `file_handle`              |
| `exc`  | `error`                    |
| `ret`  | `result`                   |
| `hdr`  | `header`                   |
| `buf`  | `buffer`                   |

Allowed: `args`, `kwargs`, `argv`, `url`, `api`, `id` (established vocabulary).

**Enforcement**: `style-gates.sh` runs `grep -nE '\b(rec|req|resp|fh|exc|ret|hdr|buf)\b'`. Suppress: `# naming:allow`.

## Underscore Prefix

No true private in Python. `__all__` controls API. **Default: NO underscore.** Only add `_` for: builtin shadows (`_id`,
`_type`) or framework internals.

| Pattern               | Underscore? | Reason                                             |
| --------------------- | ----------- | -------------------------------------------------- |
| `self.layout`         | NO          | Instance attr, normal access                       |
| `self.upload_btn`     | NO          | UI widget, implementation detail but not "private" |
| `self.store`          | NO          | Injected dependency                                |
| `def on_click(self):` | NO          | Callback, called by framework                      |
| `def refresh(self):`  | NO          | Internal method, but not hiding anything           |
| `self._cache`         | MAYBE       | True internal state that would break if accessed   |

**Refactoring**: remove `_` from methods/attrs unless shadowing builtins or true internals.

| Question                          | Action                                     |
| --------------------------------- | ------------------------------------------ |
| Called only within this file?     | Rename public anyway — hiding buys nothing |
| Another module would use it?      | Make public                                |
| Genuinely internal mutable state? | Keep underscore (only case)                |

**Module functions**: NO underscore default. Only: `@property` backing field or explicit internal API.

[[python/types]] [[debugging/references/python]]
