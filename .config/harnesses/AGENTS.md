# Global Agent Instructions

Canonical for Claude Code, Kilo, OpenCode. Invariants + routing only; procedures live in skills.

Multi-agent pipeline rules (handoff contract): @~/.config/harnesses/handoff-contract.md

## Communication

**Banned**: Preamble, pleasantries, filler, affirmations, interjections, narrating intent. Act — don't announce.

**Required**: Action first, context if needed. Number steps. Progress updates ("3/5 done"). ~15 min > "some work".

**Invariants**:
- Debug first, fix second — one print statement > blind fix attempts
- User names an approach ("orchestrate", "fan-out") → execute it; no silent shortcuts
- Same action, different entry points → same result; test every entry point × every state
- Stale comments worse than none — update or remove on every change
- Never start a bash command with a comment
- Comments: short "why" only, never "what"; no comment is the default
- Scripts handed to the user: complete files, never fragments or diffs
- Verification artifacts (reviews, tests, plan checks): attempt to disprove — assume the work is wrong and hunt;
  approval is the failure mode when issues exist. Scoped to verification; not research or generation.
- Code is written for human readers — names carry meaning, comments explain why, structure communicates intent

Output style, banned phrases, abbreviation rules: `token-efficiency` skill.

## Skill Routing

| Domain             | Skill              | Routes To                                                                                        |
| ------------------ | ------------------ | ------------------------------------------------------------------------------------------------ |
| Python             | `python`           | orchestrator — registry in skill                                                                 |
| Python analysis    | `ast-check`        | (leaf) — AST bugs/security/quality/structure                                                     |
| Debugging          | `debugging`        | (leaf) — 6-phase diagnosis; language tables in references/                                       |
| Writing code       | `test-driven-development` | (leaf) — red-green-refactor; failing test first                                             |
| Planning           | `writing-plans`   | (leaf) — multi-step implementation plans before code                                         |
| Windows            | `windows`          | orchestrator — powershell, batch, dotnet-testing                                                 |
| Conda              | `conda`            | conda-packaging, conda-internal, conda-anaconda-tools                                            |
| Bash               | `bash-shell`       | (leaf) — tool search, scratch files                                                              |
| Output             | `token-efficiency` | (leaf) — style, compression, context budget                                                      |
| Diagrams/artifacts | `artifacts`        | (leaf) — images, mermaid, encoded data                                                           |
| Markdown           | `markdown`         | (leaf) — prettier formatting                                                                     |
| Code search        | `code-index`       | (leaf) — semantic search, knowledge graph, flywheel; run before writing new code                 |
| Research           | `research`         | (leaf) — papers, notes, sources                                                                  |
| Accessibility      | `accessibility`    | (leaf) — a11y                                                                                    |
| Verification       | `verify`           | (leaf) — verify claims                                                                           |
| Build failures     | `build-watch-fix`  | (leaf) — build-fix loop                                                                          |
| Commits            | `git-commit`       | (leaf) — staging, attribution, message format                                                    |
| Code hygiene       | `code-hygiene`     | (stage) — runs after `bug`, before pytest; types, naming, structure                              |

No matching domain → proceed normally. New domains: author a skill (skill authoring rules live with the skills), never
grow this file. Handoff ranks + termination rules: `handoff-contract.md` (Termination).

## Session Start

1. **Skills before exploring** — for any task matching a domain in Skill Routing, load that skill first. Pre-loaded
   context, not optional refs.
2. Check local dirs first.
3. Repo config: load the repo's own instruction file if present (see Harness Specifics).
4. Git repos: check `.harness/` — load `.harness/AGENTS.md` if present. Code index tri-state: missing → offer
   `code-index/scripts/harness-refresh.sh`; stale → refresh; current → proceed.

**Anti-pattern**: "I'll explore to understand..." → load skill first.

## Locations

- Canonical: `.config/harnesses/` (dotfiles repo) — shared `AGENTS.md`, `handoff-contract.md`, `agents/`, `skills/`, `scripts/`, `plugins/`; harness-specific prefs in `.config/harnesses/{kilo,claude,opencode}/`; architecture: `.config/harnesses/README.md`
- Symlinked to: `~/.config/harnesses/`, `~/.claude/{skills,scripts,agents,README.md,keybindings.json}`, per-skill into `~/.config/kilo/skills/`, `~/.config/kilo/{agents,plugins}`
- Copied, not linked (local divergence reconciles manually): `harnesses/kilo/{kilo.jsonc,tui.json}` → `~/.config/kilo/`, `harnesses/claude/settings.json` → `~/.claude/`
- OpenCode prefs (`harnesses/opencode/`) are not linked out — Kilo warns on `~/.config/opencode` (no fallback)
- Per-repo generated state: `<repo>/.harness/` (code index, analysis scripts; gitignored, regenerable — never commit)

## Harness Specifics

| Harness     | Global instruction file            | Repo instruction file | Config             |
| ----------- | ---------------------------------- | --------------------- | ------------------ |
| Claude Code | `~/.claude/CLAUDE.md`              | `AGENTS.md` (native)  | `.claude/settings.json` |
| Kilo        | `~/.config/kilo/AGENTS.md`         | `AGENTS.md`           | `kilo.json` / `kilo.jsonc` |
| OpenCode    | `opencode.jsonc` instructions field | `AGENTS.md`          | `harnesses/opencode/opencode.jsonc` (not linked) |

Claude Code and Kilo global instruction files are symlinks to this file (`.config/harnesses/AGENTS.md` in the dotfiles
repo); OpenCode references it via the `instructions` field. Repo-level: all three harnesses read `AGENTS.md`, which
points to `.harness/AGENTS.md` when present.
