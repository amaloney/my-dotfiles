---
name: code-hygiene
description: Focused code hygiene for Python and Rust
---

# Code Hygiene Skill

Input: artifact path(s) + scope. Output: status, path, and next stage. Cosmetic/structural only; never change behavior.

**Hooks run `style_gates.py` automatically** — this skill provides context for full reviews and edge cases.

Read only rules needed for actual findings:

| Concern                    | Python             | Rust             |
| -------------------------- | ------------------ | ---------------- |
| Private names / visibility | `python/naming`    | `rust/structure` |
| Naming                     | `python/naming`    | `rust/naming`    |
| Structure                  | `python/structure` | `rust/structure` |
| Types                      | (hook: pyrefly)    | `rust/types`     |

`focused`: one trivial single-file fix; targeted check; return `next: done`. Skip unrelated leaves and broad lint/test
stages.

`full`: read applicable rule leaves, run the language gate, then hand off to testing.

Python: hooks run `style_gates.py` after every edit (naming, private, wrapper, comment, docstring) and at stop (adds
reuse check against code_index + pyrefly). Fix findings as they appear — don't suppress unless intentional.

Rust:
`cargo fmt --check && cargo clippy --all-targets -- -D warnings -W clippy::pedantic -A clippy::module_name_repetitions -A clippy::must_use_candidate -A clippy::missing_errors_doc`.

If a change alters behavior, stop and report it. Read/save pattern memory only when relevant or novel.

## TYPE_CHECKING Guards

**Never remove imports inside `if TYPE_CHECKING:` blocks.** These prevent circular imports at runtime while allowing
type hints.

```python
# PRESERVE - do not "fix" as unused import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from package.module import SomeClass  # Used only for type hints
```

Even if the import appears unused, the TYPE_CHECKING guard exists for a reason. Removing it causes circular imports.
