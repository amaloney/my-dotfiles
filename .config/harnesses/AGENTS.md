# Global Agent Instructions

Canonical for Claude Code, Kilo, OpenCode. Invariants + routing only; procedures live in skills.

Multi-agent pipeline rules (handoff contract): @~/.config/harnesses/handoff-contract.md

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
| Markdown        | `markdown`                | L    | prettier formatting                  |
| Code search     | `code-index`              | L    | semantic search; run before new code |
| Research        | `research`                | L    | papers, notes, sources               |
| Accessibility   | `accessibility`           | L    | a11y                                 |
| Verification    | `verify`                  | L    | verify claims                        |
| Build failures  | `build-watch-fix`         | L    | build-fix loop                       |
| Commits         | `git-commit`              | L    | staging, attribution                 |
| Code hygiene    | `code-hygiene`            | S    | after bug, before pytest             |
| AI code smells  | `discouraged-patterns`    | S    | RLHF noise, single-use abstractions  |

**Artifact routing**: skills declare `extensions:` + `keywords:` in SKILL.md frontmatter. Before write/edit, load
matching skill if not loaded. No match → proceed. New domains → author skill, never grow this file. Handoff:
`handoff-contract.md`.

## Session Start

1. **Skills before exploring** — task matches Skill Routing → load skill first.
2. Check local dirs first.
3. Repo config: load the repo's own instruction file if present (see Harness Specifics).
4. Git repos: check `.harness/` — load `.harness/AGENTS.md` if present. Code index tri-state: missing → offer
   `code-index/scripts/harness-refresh.sh`; stale → refresh; current → proceed.

**Anti-pattern**: "I'll explore to understand..." → load skill first.

## Locations

| Type    | Source                    | Target                                              |
| ------- | ------------------------- | --------------------------------------------------- |
| Canon   | `.config/harnesses/`      | AGENTS.md, skills/, agents/, scripts/, plugins/     |
| Symlink | (same)                    | ~/.config/harnesses/, ~/.claude/_, ~/.config/kilo/_ |
| Copy    | harnesses/{kilo,claude}/* | ~/.config/kilo/, ~/.claude/settings.json            |
| Repo    | `<repo>/.harness/`        | gitignored, regenerable                             |

Architecture: `.config/harnesses/README.md`. OpenCode prefs not linked — Kilo warns on `~/.config/opencode`.

## Harness Specifics

| Harness     | Global instruction file             | Repo instruction file | Config                                           |
| ----------- | ----------------------------------- | --------------------- | ------------------------------------------------ |
| Claude Code | `~/.claude/CLAUDE.md`               | `AGENTS.md` (native)  | `.claude/settings.json`                          |
| Kilo        | `~/.config/kilo/AGENTS.md`          | `AGENTS.md`           | `kilo.json` / `kilo.jsonc`                       |
| OpenCode    | `opencode.jsonc` instructions field | `AGENTS.md`           | `harnesses/opencode/opencode.jsonc` (not linked) |

Global files symlink to `.config/harnesses/AGENTS.md`; OpenCode uses `instructions` field. All harnesses read repo-level
`AGENTS.md` → `.harness/AGENTS.md`.
