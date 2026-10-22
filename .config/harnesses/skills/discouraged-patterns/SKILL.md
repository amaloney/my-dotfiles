---
name: discouraged-patterns
description: AI code smells - patterns that look careful but add noise or hide bugs
invocation: auto
keywords: [code review, slop, anti-pattern, smell]
---

# Discouraged Patterns (Code)

Handoff: `next: done`.

Patterns that score well in RLHF but degrade code quality. Models add the _look_ of care (try/except, named constants,
docstrings) even where they do nothing.

## Comments

| Smell                                | Fix                     |
| ------------------------------------ | ----------------------- |
| Docstring repeats function name      | Delete or explain _why_ |
| "# increment counter" above `i += 1` | Delete                  |
| Comment claims something verifiable  | Verify or delete        |

**Rule**: Comments explain _why_ (constraint, workaround, magic number). Never _what_.

## Single-Use Abstractions

| Smell                           | Fix                                          |
| ------------------------------- | -------------------------------------------- |
| Module-level constant used once | Inline it                                    |
| Helper called from one place    | Inline unless name explains what value can't |
| Wrapper that rewords an error   | Delete                                       |

**Rule**: Pull out on second caller, not before.

## Error Handling

| Smell                                               | Fix                                     |
| --------------------------------------------------- | --------------------------------------- |
| `try/except Exception` around code that can't fail  | Remove                                  |
| Return `None` on timeout                            | Raise or return sentinel caller expects |
| `try: import X except ImportError` for required dep | Remove try/except                       |
| Catch-and-log without re-raise                      | Re-raise or justify                     |

**Rule**: Ask how it could fail and what the caller sees when it does.

## Duplication

| Smell                              | Fix                         |
| ---------------------------------- | --------------------------- |
| New helper when equivalent exists  | Use existing, fix if needed |
| Same regex/logic in multiple files | Extract to single source    |
| Parsing logic repeated             | Consolidate                 |
| Parallel aggregation classes       | Keep one, delete others     |
| Constants in multiple files        | Move all to constants.py    |
| TypedDict + dataclass for same     | Pick one representation     |

**Rule**: Fix the one helper; don't keep two. Query code-index `find_duplicates()` before creating new entities.

## Symptom vs Root Cause

| Smell                               | Example                                     | Fix                  |
| ----------------------------------- | ------------------------------------------- | -------------------- |
| Patching callers                    | `.strip()` at every call site               | Fix output at source |
| Editing test expectations           | Change expected value to match wrong output | Fix the code         |
| Adding guards for impossible states | `if x is not None` when x is always set     | Remove guard         |

**Rule**: Trace to origin; patch there.

## Structure

| Smell                                           | Fix                                           |
| ----------------------------------------------- | --------------------------------------------- |
| Imports inside function (no justification)      | Move to top                                   |
| Class above related constants/functions         | Order: imports, constants, functions, classes |
| Utility file > 500 lines                        | Split by domain                               |
| Inconsistent naming (`font_size` vs `fontsize`) | Pick one, rename all                          |

## Review Checklist

Before approving AI-generated code:

1. Search repo for existing function doing same job
2. Verify comment claims are true
3. Justify every try/except by how inner code could fail
4. List constants/helpers used once — inline candidates
5. Check if fix is at root cause or symptom
6. If most lines need fixing, start over

## Relevant Lints

| Rule      | Catches                  |
| --------- | ------------------------ |
| `BLE001`  | `except Exception`       |
| `PLC0415` | imports inside functions |
| `# noqa`  | review every instance    |
