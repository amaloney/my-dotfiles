# Harnesses

Single source of truth for agent-harness configuration: Claude Code, Kilo, OpenCode. Installed by `install.sh`
at the dotfiles root.

## Layout

| Path | Scope | Contents |
| --- | --- | --- |
| `AGENTS.md` | shared | Canonical global instructions — invariants + skill routing |
| `handoff-contract.md` | shared | Multi-agent pipeline rules (create → bug → code-hygiene → pytest) |
| `agents/` | shared | Pipeline stage agents: bug, code-hygiene, code-index |
| `skills/` | shared | All skills — see [skills/README.md](skills/README.md) |
| `scripts/` | shared | Cross-skill scripts (skill-graph, skill vectors, pronoun check) |
| `plugins/` | kilo + opencode | JS plugin-API files: harness-refresh, strip-blobs |
| `kilo/` | kilo only | `kilo.jsonc`, `tui.json` |
| `claude/` | claude only | `settings.json`, `keybindings.json`, `README.md` |
| `opencode/` | opencode only | `opencode.jsonc` — not linked out (Kilo warns on `~/.config/opencode`) |

## Skill vs agent

Skill = harness-agnostic content (rules, procedures). Agent = invocation binding for that content
(frontmatter: `mode`/`steps`/`permission` for Kilo, `name` for Claude; body: stage contract + guardrails).
Agents never hold rule content — they load the skill.

## Content ownership (single owner; others link)

| Content | Owner |
| --- | --- |
| Python bug patterns + shared detection | `skills/debugging/references/python.md` |
| Rust bug patterns + debug tooling | `skills/debugging/references/rust.md` |
| Security patterns (vulns, insecure defaults) | `skills/python/security` |
| Rust security patterns (unsafe, supply chain) | `skills/rust/security` |
| Hygiene rules (types, naming, structure) | `skills/python/{types,naming,structure}` |
| Rust hygiene rules (types, naming, structure) | `skills/rust/{types,naming,structure}` |
| Rust lint selection (ast-check → clippy) | `skills/ast-check/references/rust-clippy.md` |
| Edge/IO patterns | `skills/bug` |
| Code-index tooling, flywheel + graph theory | `skills/code-index/scripts/` (Rust extraction: `extract_rust.py`) |
| Python repo bootstrap | `skills/python/repo-init` |
| Rust repo bootstrap | `skills/rust/repo-init` |

## Intentional per-harness duplication (why)

- **Config schemas differ** — `kilo.jsonc` / `opencode.jsonc` / claude `settings.json` have no shared-include
  mechanism; permission blocks are mirrored by hand.
- **Same intent, different mechanism** — code-index refresh exists as a Kilo plugin (`plugins/harness-refresh.js`)
  AND a Claude hook (`settings.json` SessionStart/PostToolUse). Both, by design.
- **`keybindings.json`** — Claude-only concept.

## Pipeline vs routing

- `AGENTS.md` = universal invariants + skill routing table (all harnesses).
- `handoff-contract.md` = pipeline orchestration rules. Kilo loads it via `kilo.jsonc` `instructions`; Claude via the
  `@`-import line in `AGENTS.md`.
- Known gap: the contract references a `refactor-python` stage with no agent definition yet.

## Memory types (agent memory tools)

| Type | When to save | Example |
| --- | --- | --- |
| user | User role, preferences, knowledge | "User is senior Python dev" |
| feedback | Corrections and confirmations | "Don't mock the database" |
| project | Ongoing work, goals, deadlines | "Merge freeze starts Thursday" |
| reference | External system pointers | "Bugs tracked in Linear project X" |

## Quick reference

```bash
# Code index (per-repo, under .harness/code_index/)
python3 .harness/code_index/query_temporal.py search "build docker"
python3 .harness/code_index/query_temporal.py callers my_function
python3 .harness/code_index/query_temporal.py impact MyService
python3 .harness/code_index/query_temporal.py changes 7d

# Flywheel
python3 .harness/code_index/flywheel.py status
python3 .harness/code_index/flywheel.py skills --class proven
python3 .harness/code_index/flywheel.py recommend missing_module

# Skill graph (structure gates + blast radius; pre-commit runs both automatically)
# Vector rebuild is automatic on SKILL.md edits (Kilo plugin + Claude hooks,
# self-filtering via scripts/skill-vectors-refresh.sh); pre-commit then runs
# drift + suggest advisory. Human feedback on suggestions stays manual.
bash .config/harnesses/scripts/skill-graph.sh --check
bash .config/harnesses/scripts/skill-graph.sh --dependents python/testing

# Skill edges (semantic layer; state in ~/.config/harnesses/vectors/, gitignored)
python3 .config/harnesses/scripts/suggest_edges.py suggest [skill]   # missing-edge candidates
python3 .config/harnesses/scripts/suggest_edges.py feedback a b accept|reject
python3 .config/harnesses/scripts/suggest_edges.py drift             # score drops on existing edges
# Snapshots for drift are recorded automatically by build_skill_vectors.py --rebuild

# Skill network visualizer (sigma.js, zero-dependency node server)
node .config/harnesses/scripts/skill_network.js 7474   # http://localhost:7474
```

## Sources & inspirations

| Repo | What was used |
| --- | --- |
| [trailofbits/skills](https://github.com/trailofbits/skills) | modern-python, property-testing, insecure-defaults patterns |
| [LambdaTest/agent-skills](https://github.com/LambdaTest/agent-skills) | pytest patterns, BDD patterns |
| [Agent-Skills-for-Context-Engineering](https://github.com/davidpp/Agent-Skills-for-Context-Engineering) | memory-systems, multi-agent patterns, flywheel concept |
| [context-engineering-kit](https://github.com/anthropics/context-engineering-kit) | plugin architecture patterns |
| [Roarpeng/GraphFlow](https://github.com/Roarpeng/GraphFlow) | code knowledge graph, learning flywheel |

| Concept | Source | Implementation |
| --- | --- | --- |
| Gini purity | ToB skills | Each skill = one concept |
| Corpus pattern | ToB insecure-defaults | VULNERABLE/SECURE examples |
| Recon phase | ToB multi-agent | profile.json before work |
| Flywheel | GraphFlow | Skills accumulate from outcomes |
| Bi-temporal | Graphiti | valid_from/valid_until tracking |
| Episode memory | Context Engineering | Task → outcome → lessons |
