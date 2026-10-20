# Harnesses

Single source of truth for agent-harness configuration: Claude Code, Kilo, OpenCode. Installed by `install.sh` at the
dotfiles root.

## Layout

| Path                  | Scope           | Contents                                                               |
| --------------------- | --------------- | ---------------------------------------------------------------------- |
| `AGENTS.md`           | shared          | Canonical global instructions — invariants + skill routing             |
| `handoff-contract.md` | shared          | Multi-agent pipeline rules (create → bug → code-hygiene → pytest)      |
| `agents/`             | shared          | Pipeline stage agents: bug, code-hygiene, code-index                   |
| `skills/`             | shared          | All skills — see [skills/README.md](skills/README.md)                  |
| `scripts/`            | shared          | Cross-skill scripts (skill-graph, skill vectors, pronoun check)        |
| `plugins/`            | kilo + opencode | JS plugin-API files: harness-refresh, strip-blobs                      |
| `kilo/`               | kilo only       | `kilo.jsonc`, `tui.json`                                               |
| `claude/`             | claude only     | `settings.json`, `keybindings.json`, `README.md`                       |
| `opencode/`           | opencode only   | `opencode.jsonc` — not linked out (Kilo warns on `~/.config/opencode`) |

## Skill vs agent

Skill = harness-agnostic content. Agent = invocation binding (frontmatter + stage contract). Agents load skills, never
hold rules.

## Content ownership (single owner; others link)

| Content                                       | Owner                                                             |
| --------------------------------------------- | ----------------------------------------------------------------- |
| Python bug patterns + shared detection        | `skills/debugging/references/python.md`                           |
| Rust bug patterns + debug tooling             | `skills/debugging/references/rust.md`                             |
| Security patterns (vulns, insecure defaults)  | `skills/python/security`                                          |
| Rust security patterns (unsafe, supply chain) | `skills/rust/security`                                            |
| Hygiene rules (types, naming, structure)      | `skills/python/{types,naming,structure}`                          |
| Rust hygiene rules (types, naming, structure) | `skills/rust/{types,naming,structure}`                            |
| Rust lint selection (ast-check → clippy)      | `skills/ast-check/references/rust-clippy.md`                      |
| Edge/IO patterns                              | `skills/bug`                                                      |
| Code-index tooling, flywheel + graph theory   | `skills/code-index/scripts/` (Rust extraction: `extract_rust.py`) |
| Python repo bootstrap                         | `skills/python/repo-init`                                         |
| Rust repo bootstrap                           | `skills/rust/repo-init`                                           |

## Per-harness duplication

Config schemas differ (no shared-include). Code-index refresh: Kilo plugin + Claude hook (both by design).

## Pipeline vs routing

`AGENTS.md` = invariants + routing. `handoff-contract.md` = pipeline rules. Gap: `refactor-python` stage undefined.

## Memory types (agent memory tools)

| Type      | When to save                      | Example                            |
| --------- | --------------------------------- | ---------------------------------- |
| user      | User role, preferences, knowledge | "User is senior Python dev"        |
| feedback  | Corrections and confirmations     | "Don't mock the database"          |
| project   | Ongoing work, goals, deadlines    | "Merge freeze starts Thursday"     |
| reference | External system pointers          | "Bugs tracked in Linear project X" |

## Quick reference

**Code index**: `query_temporal.py search|callers|impact|changes`. **Flywheel**: `flywheel.py status|skills|recommend`.
**Skill graph**: `skill-graph.sh --check|--dependents`. **Edges**: `suggest_edges.py suggest|feedback|drift`.
**Visualizer**: `node skill_network.js 7474`.

## Sources & inspirations

| Repo                                                                                                    | What was used                                               |
| ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| [trailofbits/skills](https://github.com/trailofbits/skills)                                             | modern-python, property-testing, insecure-defaults patterns |
| [LambdaTest/agent-skills](https://github.com/LambdaTest/agent-skills)                                   | pytest patterns, BDD patterns                               |
| [Agent-Skills-for-Context-Engineering](https://github.com/davidpp/Agent-Skills-for-Context-Engineering) | memory-systems, multi-agent patterns, flywheel concept      |
| [context-engineering-kit](https://github.com/anthropics/context-engineering-kit)                        | plugin architecture patterns                                |
| [Roarpeng/GraphFlow](https://github.com/Roarpeng/GraphFlow)                                             | code knowledge graph, learning flywheel                     |

| Concept        | Source                | Implementation                  |
| -------------- | --------------------- | ------------------------------- |
| Gini purity    | ToB skills            | Each skill = one concept        |
| Corpus pattern | ToB insecure-defaults | VULNERABLE/SECURE examples      |
| Recon phase    | ToB multi-agent       | profile.json before work        |
| Flywheel       | GraphFlow             | Skills accumulate from outcomes |
| Bi-temporal    | Graphiti              | valid_from/valid_until tracking |
| Episode memory | Context Engineering   | Task → outcome → lessons        |
