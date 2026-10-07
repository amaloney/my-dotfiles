---
name: python/structure
description: File structure - line length, imports, layout, comments
invocation: auto
---

# Structure

Handoff: `next: done`.

Lines <120. **Single return at end** — unless an early return skips expensive work (DB query, API call, heavy
computation). Multiple returns for simple conditionals add cognitive load; consolidate to one.

## File Order (strict)

```python
# 1. Imports
# 2. TYPE_CHECKING block (if needed)
# 3. Module constants (ALL_CAPS) — NEVER inline
# 4. Module-level functions
# 5. Classes (attrs → methods)
```

**Constants:** [[python/org]].

## Imports

**Absolute imports always.** Never `from .` / `from ..` — relative imports break when a file is exec'd as a
script (`panel serve`, `python file.py`), hide the package boundary from grep, and turn moves/renames into
silent breakage. Applies to packages too: `from xray.report import build_workbook`, never
`from .report import build_workbook`.

Enforcement gap — tooling does not catch this. Ruff/isort sort relative imports happily; flagging them is a
mandatory review-time gate, run on every file you create or edit:

```bash
grep -nE '^\s*from \.' <file>    # clean output = pass
```

## Functions

**Syntactic sugar adds complexity.** A one-liner helper that just wraps an expression doesn't reduce complexity — it
adds indirection. Inline it.

**Gate before creating any function:** ask "is this more than one expression, used more than once?" No to either →
do not create it. `normalize_name()` wrapping one regex, called once, is the canonical violation — it forces the
reader to jump away to learn it is just `re.sub(...).lower()`.

| Pattern                                    | Problem                | Fix                 |
| ------------------------------------------ | ---------------------- | ------------------- |
| `def get_x(): return obj.x`                | Wrapper adds nothing   | Inline `obj.x`      |
| `def normalize_name(n): return re.sub(...)`| Single-use, single expression | Inline at call site + why-comment |
| `def csv_env(n): return {…comprehension…}` | Sugar, not abstraction | Inline at call site |

**When to extract:** Logic is reused 3+ times, OR name documents non-obvious intent, OR expression is complex enough to
obscure the calling code. Docstrings do not rescue sugar — a 13-line docstring on a 1-line function is the smell.

**Same gate applies to dataclass docstrings.** An `Attributes:` section that restates field names with type
rephrasings is sugar — the field declarations already say it. Delete it; keep one line stating what the record IS.
Property one-liners earn their place only when semantics are non-obvious (threshold, clamp, computed unit) — and the
doc must name the non-obvious part, not rephrase the name.

## Comments

Only when WHY is non-obvious. No tombstones, no decorative blocks.

## Docstrings

Docstrings are first-class — written with the signature, not after. Public functions get Google-style docstrings
([pyguide](https://google.github.io/styleguide/pyguide.html#docstrings)) with `Args:` and `Returns:` (`Raises:` when
applicable). One-liner only for trivial helpers whose signature says everything.

[[python/org]] [[python/types]]
