# Harnesses

Single source of truth for agent-harness configuration: Claude Code, Kilo, OpenCode. Installed by `install.sh` at the
dotfiles root.

## Layout

| Path                  | Scope           | Contents                                                                    |
| --------------------- | --------------- | --------------------------------------------------------------------------- |
| `AGENTS.md`           | shared          | Canonical global instructions — invariants + skill routing                  |
| `handoff-contract.md` | shared          | Multi-agent pipeline rules (create → bug → code-hygiene → pytest)           |
| `agents/`             | shared          | Pipeline agents (bug, code-hygiene, code-index) + read-only locator (scout) |
| `skills/`             | shared          | All skills — see [skills/README.md](skills/README.md)                       |
| `scripts/`            | shared          | Hooks and tools for the harness; see [scripts/README.md](scripts/README.md) |
| `plugins/`            | kilo + opencode | JS plugin-API files: harness-refresh, strip-blobs                           |
| `kilo/`               | kilo only       | `kilo.jsonc`, `tui.json`                                                    |
| `claude/`             | claude only     | `settings.json`, `keybindings.json`, `README.md`                            |
| `opencode/`           | opencode only   | `opencode.jsonc` — not linked out (Kilo warns on `~/.config/opencode`)      |

## Skill vs agent

Skill = harness-agnostic content. Agent = invocation binding (frontmatter + stage contract). Agents load skills, never
hold rules.

## System Python guard

**Never use system Python.** A PreToolUse hook blocks any Bash command that would invoke system Python.

```
$ python script.py
BLOCKED: System Python detected at /usr/bin/python3
Use 'scripts/crun' or activate a conda environment first.
```

**Allowed:**
- Python inside a conda environment (`CONDA_PREFIX` set)
- Python path contains `/conda/`, `/miniforge/`, `/anaconda/`, `/miniconda/`, or `/.conda/`

**How to run Python:**
```bash
# Option 1: Use crun (auto-finds project env or falls back to base)
scripts/crun python script.py

# Option 2: Activate conda env first
conda activate myenv
python script.py

# Option 3: Use project-local env (after direnv allow)
cd myproject   # direnv auto-activates .conda/dev
python script.py
```

If only system Python is available, the hook blocks and the user must install/configure conda.

## Skill tool enforcement

Skills can declare which tools they're allowed to use via frontmatter. A PreToolUse hook enforces these restrictions.

### Frontmatter schema

```yaml
---
name: verify
description: Run verification commands before claiming completion
invocation: auto
allowed-tools:      # whitelist — only these tools permitted
  - Read
  - Bash
denied-tools:       # blacklist — explicit denials (optional)
  - Edit
  - Write
---
```

- `allowed-tools`: If present, skill can ONLY use listed tools. Unlisted tools are blocked.
- `denied-tools`: Explicit denials (takes precedence if both are set).
- Neither present: No restriction, all tools allowed.

### How it works

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SessionStart                                                            │
│   └─→ creates .harness/session/loaded_skills.txt (empty)                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Read(skills/verify/SKILL.md)                                            │
│   └─→ PostToolUse appends path to loaded_skills.txt                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ /verify (Skill tool)                                                    │
│   └─→ PostToolUse appends "skill:verify" to loaded_skills.txt           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Claude attempts Edit(...)                                               │
│   └─→ PreToolUse: skill_tool_guard.py                                   │
│         1. Reads loaded_skills.txt, finds most recent skill             │
│         2. Parses verify/SKILL.md frontmatter                           │
│         3. allowed-tools: [Read, Bash] — Edit not in list               │
│         4. Exit 2 → BLOCKED with message                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### Example: read-only skill

```yaml
# skills/code-index/SKILL.md
---
name: code-index
description: Query an existing code index
invocation: manual
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---
```

When `code-index` is loaded, attempts to use `Edit`, `Write`, or `Agent` will be blocked:

```
Skill 'code-index' only allows: Read, Grep, Glob, Bash. Tool 'Edit' is not permitted.
```

### Example: research skill with web access

```yaml
# skills/research/SKILL.md
---
name: research
description: Structured research with source tracking
invocation: manual
allowed-tools:
  - Read
  - WebFetch
  - WebSearch
  - Write
---
```

Research can read, fetch web content, and write notes — but cannot run Bash commands or spawn agents.

### Sentinel file

`.harness/session/loaded_skills.txt` tracks loaded skills (one per line):

```
/Users/me/.config/harnesses/skills/verify/SKILL.md
skill:code-index
/Users/me/.config/harnesses/skills/research/SKILL.md
```

The guard reads the **last entry** to determine the currently active skill.

## Project-local conda environments

Projects use direnv + `.envrc` for automatic conda environment activation. Use the scaffold script or copy templates from
`~/.config/harnesses/conda/` into your project root.

```bash
# Scaffold a new project
~/.config/harnesses/skills/conda-project-init/conda-project-init.sh myproject [--kilo-isolated]
```

### Directory structure

```
project/
├── .envrc              # direnv config (copy from template)
├── .condarc            # project-local conda config
├── environment.yml     # environment definition (committed)
├── Makefile            # make env creates .conda/dev
├── .conda/
│   └── dev/            # project-local environment (gitignored)
├── .local/             # XDG isolation (gitignored, optional)
├── .cache/             # XDG isolation (gitignored, optional)
└── .config/
    └── kilo/           # project-local kilo config (optional)
```

### Quick start

```bash
# 1. Copy template to new project
cp ~/.config/harnesses/conda/.envrc ./
cp ~/.config/harnesses/conda/.condarc ./
cp ~/.config/harnesses/conda/Makefile ./

# 2. Create environment.yml
cat > environment.yml << 'EOF'
dependencies:
  - python>=3.12,<3.15
  - conda>=26
  - pytest
EOF

# 3. Allow direnv (one-time per project)
direnv allow

# 4. cd into project — direnv auto-activates .conda/dev
cd .   # triggers direnv, builds env on first run
```

### XDG isolation for kilo

When kilo is installed in the project's conda environment, isolate its config to prevent leakage to global settings.
Uncomment one of these sections in `.envrc`:

**Option A: Full XDG isolation** (all apps use project-local config)

```bash
export XDG_CONFIG_HOME="$PWD/.config"
export XDG_DATA_HOME="$PWD/.local/share"
export XDG_STATE_HOME="$PWD/.local/state"
export XDG_CACHE_HOME="$PWD/.cache"
mkdir -p "$XDG_CONFIG_HOME/kilo" "$XDG_DATA_HOME" "$XDG_STATE_HOME" "$XDG_CACHE_HOME"
```

**Option B: Selective kilo isolation** (only kilo uses project-local config)

```bash
export KILO_CONFIG_DIR="$PWD/.config/kilo"
mkdir -p "$KILO_CONFIG_DIR"
```

### gitignore additions

```gitignore
# Project-local conda and XDG directories
.conda/
.local/
.cache/
.config/kilo/
```

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
**Skill graph**: `llm-skills-network build --graph --check|--dependents <skill>`. **Edges**:
`llm-skills-network edges --suggest|--feedback|--compute-drift`. Overview of every script:
[scripts/README.md](scripts/README.md). **Visualizer**: `node skill_network.js 7474`.

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
