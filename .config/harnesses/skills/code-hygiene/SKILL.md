---
name: code-hygiene
description: Code hygiene stage. Removes private/underscore methods, enforces full type annotations (args + returns), naming and structure rules. Runs after bug stage, before python/testing or rust/testing. Ported from python/types + python/naming + python/structure + python/violations; Rust passes read rust/{types,naming,structure}.
---

# Code Hygiene Skill

Input contract: `file path(s) + stage spec`. Output contract: `status + path + next: [[python/testing]]` (`.py`) or
`next: [[rust/testing]]` (`.rs`).
Cosmetic/structural only — never change behavior. If a change alters behavior, it belongs to the bug stage; do not
hand back (ranks forbid it) — emit `next: done` with a regression note; main may relaunch bug with a fresh budget.

## Passes (in order)

Rule content is owned by the language subskills — read the row for the artifact's extension before editing. Single
owners; do not duplicate their tables here. Paths are relative to `~/.config/harnesses/skills/`.

| # | Pass | `.py` owner | `.rs` owner |
|---|------|-------------|-------------|
| 1 | Python: remove private methods · Rust: minimize visibility | `python/naming/SKILL.md` (Underscore Prefix) | `rust/structure/SKILL.md` (Visibility) |
| 2 | Python: type everything · Rust: signature types (borrowing, newtypes, no gratuitous clones) | `python/types/SKILL.md` | `rust/types/SKILL.md` |
| 3 | Naming | `python/naming/SKILL.md` | `rust/naming/SKILL.md` |
| 4 | Structure | `python/structure/SKILL.md` | `rust/structure/SKILL.md` |

## Verify

```bash
# Python
ruff check <path> --select ANN,E,F,I,UP,SIM
# Rust (crate containing <path>)
cargo fmt --check && cargo clippy --all-targets -- -D warnings -W clippy::pedantic \
  -A clippy::module_name_repetitions -A clippy::must_use_candidate -A clippy::missing_errors_doc
```

Clean output = done. Hand off. Fixing violations at scale: [[python/violations]] / [[rust/violations]].

## Pattern memory

At start: recall `code-hygiene` patterns (GOOD/BAD). On novel fix: save back. Example:

```
# BAD
def _fetch(self, url): ...
def fetch(self, url): return self._fetch(url)
# GOOD
def fetch(self, url: str) -> dict[str, Any]: ...

// BAD (Rust)
pub fn load(path: &String) -> Option<Config>   // failure reason lost, over-wide visibility
// GOOD
pub(crate) fn load(path: &Path) -> Result<Config, ConfigError>
```
