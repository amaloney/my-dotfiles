---
name: code-hygiene
description: Code hygiene stage. Removes private/underscore methods, enforces full type annotations (args + returns), naming and structure rules. Runs after bug stage, before python/testing. Ported from python/types + python/naming + python/structure + python/violations.
---

# Code Hygiene Skill

Input contract: `file path(s) + stage spec`. Output contract: `status + path + next: [[python/testing]]`.
Cosmetic/structural only — never change behavior. If a change alters behavior, it belongs to the bug stage; do not
hand back (ranks forbid it) — emit `next: done` with a regression note; main may relaunch bug with a fresh budget.

## Passes (in order)

Rule content is owned by the python/ subskills — read these before editing. Single owners; do not duplicate their
tables here.

| # | Pass | Owner file |
|---|------|------------|
| 1 | Remove private methods | `~/.config/harnesses/skills/python/naming/SKILL.md` (Underscore Prefix) |
| 2 | Type everything (args + returns) | `~/.config/harnesses/skills/python/types/SKILL.md` |
| 3 | Naming | `~/.config/harnesses/skills/python/naming/SKILL.md` |
| 4 | Structure | `~/.config/harnesses/skills/python/structure/SKILL.md` |

## Verify

```bash
ruff check <path> --select ANN,E,F,I,UP,SIM
```

Clean output = done. Hand off. Fixing violations at scale: [[python/violations]].

## Pattern memory

At start: recall `code-hygiene` patterns (GOOD/BAD). On novel fix: save back. Example:

```
# BAD
def _fetch(self, url): ...
def fetch(self, url): return self._fetch(url)
# GOOD
def fetch(self, url: str) -> dict[str, Any]: ...
```
