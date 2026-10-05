---
name: python/org
description: File organization - config.py, utils.py patterns
invocation: auto
---

# Organization

Handoff: `next: done`.

## Constants

| Scope | Location |
| --- | --- |
| Shared by 2+ modules, or project-wide setting | `config.py` |
| Used by exactly one module | Top of that module (after imports) |
| Inline/mid-file | **NEVER** |

**config.py** holds only constants/settings/type aliases/enums with cross-module reach. A constant imported by one
module lives in that module — config.py is not a default dumping ground. **utils.py**: shared functions.

## Path-Valued Constants

Config constants that are paths are `pathlib.Path` instances, never `str` — call sites then compose with
`/` instead of `os.path.join` or `Path(...)` re-wrapping. Example: `METADATA_DIR: Path = Path("metadata")`.

## Cache Directory Convention

Fetchers take `cache_dir: Path | None`; `None` maps to a source-specific default subdirectory under the
project's metadata dir (`METADATA_DIR / "pypi"`, `/ "github"`, etc.). Callers pass nothing for the default;
tests pass `tmp_path`.

## Colors

If using a color theme (e.g., Gruvbox), define colors in `config.py` as a class. No hardcoded hex in Python — use named
constants.

[[python/structure]] [[python/naming]]
