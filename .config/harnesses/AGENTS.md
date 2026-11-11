# Global Agent Instructions

Canonical for Claude Code, Kilo, OpenCode. Invariants + routing only; procedures live in skills.

Multi-agent pipeline rules: load `~/.config/harnesses/handoff-contract.md` before pipeline/orchestration work; leaf
agents do not load it.

## Communication

**Banned**: Preamble, pleasantries, filler, affirmations ("you're right/good point"), interjections, narrating intent.

**Required**: Action first, context if needed. Number steps. Progress updates ("3/5 done"). ~15 min > "some work".

**Invariants**:

- Debug first, fix second — one print statement > blind fix attempts
- User names an approach ("orchestrate", "fan-out") → execute it; no silent shortcuts
- Same action, different entry points → same result; test every entry point × every state
- Stale comments worse than none — update or remove on every change
- Never start a bash command with a comment
- Comments: short "why" only, never "what"; no comment is the default
- Scripts handed to the user: complete files, never fragments or diffs
- Ad-hoc code: write it to `.harness/scripts/<task>.py` with the Write tool, then run the file; never inline
  (`python -c`)
- Fetched web resources (webpages, articles, docs): capture via chat-provenance `save_source.py` into
  `.harness/research/` before relying on the content
- Verification (reviews, tests, plans): assume wrong, hunt; approval is failure. Not for research/generation.
- Code for humans — meaningful names, "why" comments, intentional structure
- Descriptive loop variables (`for contact in contacts`), not single letters or cryptic abbreviations
- For Python environments, dependency management, and Python task execution, use `scripts/crun <cmd>` (e.g.,
  `scripts/crun pytest`). Never use `conda run -n ...`, `conda activate`, or the global conda — a PreToolUse guard
  blocks these. If a project has `.conda/dev`, `crun` uses it; otherwise it falls back to global base. Do not use `pip`,
  `pixi`, `uv`, or another Python environment/dependency manager directly. For PyPI packages unavailable from Conda
  channels, use `conda pypi install <pkg>` (or `conda pypi install --editable .` for editable installs).
- Subagent Task prompts contain only file paths and a concise spec, at most 50 words; omit narration and request
  restatements.
- Use the read-only `scout` agent for file-finding; fan out only for independent subtasks, and use one agent for
  overlapping search scopes.
- Subagent results are at most 10 lines with `file:line` pointers; never paste code.
- Prefer `scout` agent over built-in `Explore` for file-finding (scout: 3 tools vs Explore: 20+ tools).
- Plan mode forces Explore agents (50k+ tokens each); exit plan mode early for token-sensitive tasks.
- Fork (`subagent_type: "fork"`) shares prompt cache; use for context-heavy research.
- Delegate Python implementation to `python-implementer` agent; include relevant existing functions from code_index in
  the brief — extending existing code is preferred over creating new functions.

Output style, banned phrases, abbreviation rules: `token-efficiency` skill.

## Skill Routing

Legend: O = orchestrator, L = leaf, S = stage

| Domain          | Skill                     | Type | Notes                                |
| --------------- | ------------------------- | ---- | ------------------------------------ |
| Python          | `python`                  | O    | registry in skill                    |
| Rust            | `rust`                    | O    | registry in skill                    |
| Windows         | `windows`                 | O    | powershell, batch, dotnet-testing    |
| Conda           | `conda`                   | O    | packaging, internal, anaconda-tools  |
| Python analysis | `ast-check`               | L    | AST analysis; Rust via clippy        |
| Debugging       | `debugging`               | L    | 6-phase; refs in references/         |
| Writing code    | `test-driven-development` | L    | red-green-refactor                   |
| Planning        | `writing-plans`           | L    | plans before code                    |
| Bash            | `bash-shell`              | L    | tool search, scratch files           |
| Output          | `token-efficiency`        | L    | style, compression                   |
| Artifacts       | `artifacts`               | L    | images, mermaid                      |
| Markdown        | (hook: prettier)          | -    | auto-format on edit                  |
| Code search     | `code-index`              | L    | semantic search; run before new code |
| Research        | `research`                | L    | papers, notes, sources               |
| Accessibility   | `accessibility`           | L    | a11y                                 |
| Verification    | `verify`                  | L    | verify claims                        |
| Build failures  | `build-watch-fix`         | L    | build-fix loop                       |
| Commits         | `git-commit`              | L    | staging, attribution                 |
| Code hygiene    | `code-hygiene`            | S    | after bug, before pytest             |
| AI code smells  | `discouraged-patterns`    | S    | RLHF noise, single-use abstractions  |
| CLI flags       | `cli-verification`        | S    | verify flags before completion       |

**Artifact routing**: skills declare `extensions:` + `keywords:` in SKILL.md frontmatter. Before write/edit, load
matching skill if not loaded. No match → proceed. New domains → author skill, never grow this file. Handoff:
`handoff-contract.md`.

## Skills vs Agents

**Skills** are documentation/procedures loaded into context. They load automatically:
- By file extension: edit `.py` → `python` skill loads
- By keyword: mention "pytest" → `python/testing` may load
- By agent decision: debugging task → load `debugging` skill

**Agents** (in `agents/`) are for internal delegation — users don't invoke them directly:
- `python-implementer`: main agent delegates Python implementation; searches code_index first
- `scout`: read-only file/symbol lookup

**User perspective**: Just describe what you need. Skill/agent routing is automatic. Don't say "load python-implementer"
— that's internal. Say "write a function that does X" and the agent handles routing.

## Session Start

1. **Skills before exploring** — task matches Skill Routing → load skill first.
2. Check local dirs first.
3. Repo config: load the repo's own instruction file if present (see Harness Specifics).
4. Git repos: check `.harness/` — load `.harness/AGENTS.md` if present. Code-index gates only query an existing
   populated index. Missing, empty, or unreadable index → `unavailable`; main may refresh it outside the gate. Subagents
   never install, build, or refresh indexes.

**Anti-pattern**: "I'll explore to understand..." → load skill first.

## Locations

| Type    | Source                     | Target                                                |
| ------- | -------------------------- | ----------------------------------------------------- |
| Canon   | `.config/harnesses/`       | AGENTS.md, skills/, agents/, scripts/, plugins/       |
| Symlink | (same)                     | ~/.config/harnesses/, ~/.claude/*, ~/.config/kilo/_   |
| Copy    | harnesses/kilo/\*          | ~/.config/kilo/                                       |
| Repo    | `<repo>/.harness/`         | gitignored, regenerable                               |
| Plans   | `<repo>/.harness/plans/`   | `<YYYY-MM-DD>/<name>.md`; Claude stages in `.claude/` |

Architecture: `.config/harnesses/README.md`. OpenCode prefs not linked — Kilo warns on `~/.config/opencode`.

## Harness Specifics

| Harness     | Global instruction file             | Repo instruction file | Config                                           |
| ----------- | ----------------------------------- | --------------------- | ------------------------------------------------ |
| Claude Code | `~/.claude/CLAUDE.md`               | `AGENTS.md` (native)  | `.claude/settings.json`                          |
| Kilo        | `~/.config/kilo/AGENTS.md`          | `AGENTS.md`           | `kilo.json` / `kilo.jsonc`                       |
| OpenCode    | `opencode.jsonc` instructions field | `AGENTS.md`           | `harnesses/opencode/opencode.jsonc` (not linked) |

Global files symlink to `.config/harnesses/AGENTS.md`; OpenCode uses `instructions` field. All harnesses read repo-level
`AGENTS.md` → `.harness/AGENTS.md`.
