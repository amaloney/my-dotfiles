---
name: bug
description:
  Bug audit and fix stage. Fans out to audit sub-subagents (logic, edge/IO/security), aggregates findings, applies
  fixes. Runs after code creation/refactor, before code-hygiene. Ported from python/bugs + python/security; Rust via
  rust/security.
---

# Bug Skill

Input contract: `file path(s) + stage spec`. Output contract: `status + path + next: code-hygiene`.

## Fan-out protocol

Spawn two sub-subagents (Task tool, owned by you, invisible to main). Each receives only the file path(s) + its audit
category:

| Sub-sub | Category         | Focus                                              |
| ------- | ---------------- | -------------------------------------------------- |
| A       | logic            | common bugs, infinite loops, async, imports        |
| B       | edge/IO/security | partial writes, non-200s, timeouts, vulns, secrets |

Aggregate their findings, rank by severity, apply fixes yourself, then hand off. Sub-subagents are read-only; you hold
the edit permission.

## Pattern sources (single owners — do not duplicate)

Pick by the artifact's file extension:

| Language     | A — logic                                                    | B — security                                         |
| ------------ | ------------------------------------------------------------ | ---------------------------------------------------- |
| `.py`        | `~/.config/harnesses/skills/debugging/references/python.md`  | `~/.config/harnesses/skills/python/security/SKILL.md` |
| `.rs`        | `~/.config/harnesses/skills/debugging/references/rust.md`    | `~/.config/harnesses/skills/rust/security/SKILL.md`  |

Rust sub-sub A also runs `cargo clippy --all-targets -- -W clippy::correctness -W clippy::suspicious` as its static
pass ([[ast-check]] mapping). Mixed-language artifacts → each sub-subagent gets both rows.

Owner files hold the pattern tables and detection commands. Sub-subagent prompts carry only path + category, so
include the matching owner path in their prompt context.

## Edge / IO

Owned here — no other home:

| Pattern                        | Fix                             |
| ------------------------------ | ------------------------------- |
| Partial write (crash mid-file) | Write tmp + atomic rename       |
| Non-200 / empty response       | Status check before parse       |
| No timeout                     | Explicit finite timeout, always |
| Unchecked cache freshness      | TTL or conditional request      |

## Pattern memory

At start: recall `bug` patterns (GOOD/BAD). On novel fix: save the pattern back, tagged with the language. Format:

```
# BAD
resp = requests.get(url); data = resp.json()
# GOOD
resp = requests.get(url, timeout=30); resp.raise_for_status(); data = resp.json()
```

## Fix rules

- Minimal diffs — fix the bug, don't refactor (code-hygiene is the next stage).
- Never weaken a test to make it pass.
- Reproduction-first only when a failing loop already exists; this stage audits statically.
- Finding not statically confirmable (intermittent, timing/env-dependent, needs a repro)? Do not guess-fix — report
  it with evidence in the result; main routes it to [[debugging]].
