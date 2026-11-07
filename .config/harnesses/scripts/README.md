# Harness scripts

Hooks and tools shared by Claude Code, Kilo and OpenCode. This folder is reached as `~/.config/harnesses/scripts/`
(`install.sh` links `~/.config/harnesses` to `.config/harnesses/` in this repo), so hooks always use that path.

## At a glance

| File                                         | What it does                                                                                | Who runs it                                                   | Run by hand                                                     |
| -------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------- |
| `check-conda-python.sh`                      | Block Bash commands if Python resolves to system Python (not conda-managed)                 | Claude `PreToolUse(Bash)`                                     | (hook only)                                                     |
| `skill_tool_guard.py`                        | Enforce `allowed-tools` from skill frontmatter; blocks unauthorized tool calls              | Claude `PreToolUse`                                           | (hook only — requires stdin JSON)                               |
| `style_gates.py`                             | Two-tier Python style enforcement (edit: ruff + AST rules; stop: + reuse + pyrefly)        | Claude `PostToolUse`, `SubagentStop`, `Stop`                  | `python3 style_gates.py <file-or-dir>...`                       |
| `ast_rules.py`                               | AST-based rules: naming, private, wrapper, comment, docstring, reuse                        | imported by `style_gates.py`                                  | (library, not standalone)                                       |
| `naming_check.py`                            | Cryptic/single-letter name detection at binding sites                                       | imported by `ast_rules.py`                                    | `python3 naming_check.py <file-or-dir>...`                      |
| `docblocks.py`                               | Insert docstring skeletons via vim-doge-helper                                              | imported by `style_gates.py`                                  | (library, not standalone)                                       |
| `check-pronouns.sh`                          | Flags first-person pronouns in Claude's replies                                             | Claude `MessageDisplay`                                       | `printf 'text' \| check-pronouns.sh`                            |
| `plan-archive.sh`                            | Files plan-mode plans into `<repo>/.harness/plans/<YYYY-MM-DD>/<name>.md`                   | Claude `SessionEnd`, `SessionStart` (`--min-age 12h`)         | `plan-archive.sh --dry-run <repo>`                              |
| `llm-skills-network`, `llm_skills_network/`  | Skill graph check, skill vector index, edge suggestions                                     | Claude `SessionStart` + `PostToolUse`; Kilo plugin            | `llm-skills-network build --graph --check`                      |
| `build_skill_vectors.py`, `suggest_edges.py` | Vector building and edge logic, imported by `llm_skills_network/cli.py`                     | the CLI (do not run directly)                                 | use `llm-skills-network`                                        |
| `query_skills.py`                            | Search the skill vector index by text                                                       | nothing (manual tool)                                         | `python3 query_skills.py "write a batch script" -k 3`           |
| `skill_network.js`                           | Web page showing the skill graph and edge scores                                            | by hand                                                       | `node skill_network.js 7474`, then open `http://localhost:7474` |
| `memory`, `skill_memory/`                    | Skill memories: lessons stored per skill, ranked, voted on, linted                          | `bug`, `code-hygiene`, `debugging` skills                     | `memory --help`                                                 |
| `tests/`                                     | Tests for `skill_memory/`                                                                   | by hand                                                       | see [Tests](#tests)                                             |
| `pre-commit`                                 | Skill-graph commit gate. **Currently disabled** (all commented out)                         | `.git/hooks/pre-commit` (linked by `install.sh`)              | —                                                               |

## Hooks

Claude Code hooks are set in `../claude/settings.json`, which `install.sh` copies to `~/.claude/settings.json`. The copy
can differ locally, so after changing hooks in the repo, merge the change into the installed copy too.

- **Python style** (`style_gates.py`): two-tier enforcement
  - **edit tier** (PostToolUse): fast per-file checks — ruff format/check, naming, private, wrapper, comment, docstring
  - **stop tier** (SubagentStop/Stop): full session check — adds reuse rule against code_index + pyrefly
  - Exit 2 feeds findings back to the agent; max 3 rounds at stop tier before letting the agent stop
- **Plans** (`plan-archive.sh`): plan mode writes to `<repo>/.harness/plans/.claude/` (`plansDirectory`). When a session
  ends, each plan moves to a dated folder. A plan that was filed before replaces its earlier copy.
- **Pronouns** (`check-pronouns.sh`): flags lines with "I", "my", "Let me" and similar.
- **System Python guard** (`check-conda-python.sh`): PreToolUse hook that blocks Bash commands invoking system Python.
  All Python must run through conda environments. See [System Python guard](../README.md#system-python-guard).
- **Skill tool guard** (`skill_tool_guard.py`): PreToolUse hook that enforces `allowed-tools` from skill frontmatter. See
  [Skill tool enforcement](../README.md#skill-tool-enforcement) for the full flow.
- **Code index and skill vectors:** on session start and after edits. The code index uses
  `../skills/code-index/scripts/harness-refresh.sh`; skill vectors use
  `llm-skills-network build --skill-vectors --if-stale`. Kilo runs the same two through `../plugins/harness-refresh.js`.

All hooks exit 0 when something unexpected happens, so a broken hook never blocks a session. The one exception is a
deliberate block (exit 2) from `style_gates.py`.

## Skill graph and vectors

`llm-skills-network` is the single entry point:

```bash
llm-skills-network build --graph --check              # structure: dangling links, orphans, cycles, ranks
llm-skills-network build --graph --dependents <skill> # what breaks if <skill> changes
llm-skills-network build --skill-vectors [--rebuild]  # embed every SKILL.md (needs chromadb, sentence-transformers)
llm-skills-network edges --suggest <skill> -k 5       # skills that look related but aren't linked
llm-skills-network edges --compute-drift              # how scores on existing edges changed since the last snapshot
llm-skills-network edges --feedback <a> <b> accept|reject  # record a decision on a suggested edge
```

The graph check currently fails on three skills (`python/bdd`, `python/pixi-pyproject`). A redesign is planned in
`.harness/plans/2026-11-01/skill-network-refactor.md`, in the dotfiles repo. It covers edges in frontmatter, no model
loading in session hooks, and folding `build_skill_vectors.py`, `suggest_edges.py` and `query_skills.py` into the
package. It also re-enables `pre-commit`.

## Skill memory

`memory` picks a Python interpreter that has the needed libraries and runs `python -m skill_memory.cli`:

```bash
memory query --skill bug --text "<task>" -k 5     # memories relevant to a task
memory add --skill bug < memory.md                 # add a candidate memory (--tier local|global)
memory feedback bug/<slug> helpful|harmful         # vote; status is re-evaluated
memory lint                                        # validate every memory file
memory index --if-stale                            # embed new and changed memories
```

Memories live in `../memories/`. Status and open items: `.harness/plans/skill-memory-status.md`.

## Tests

```bash
conda run -n <env> python -m pytest .config/harnesses/scripts/tests
```

The env needs `pytest` and `PyYAML`; the store tests also need `chromadb` and `sentence-transformers`.
