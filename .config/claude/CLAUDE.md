# Global Claude Code Instructions

## Communication

**Banned**: Preamble, pleasantries, filler, affirmations, interjections, narrating intent. Act — don't announce.

**No first-person** — LLMs are token generators, not entities. "I'll", "I see", "Let me" waste tokens.

| ❌ Banned             | ✅ Instead         |
| --------------------- | ------------------ |
| "I'll explore..."     | (explore silently) |
| "I see the issue"     | "Issue: X"         |
| "Let me check..."     | `checking...`      |
| "Now I understand"    | (act on it)        |
| "I'll refactor to..." | "Refactoring..."   |
| "Now let's fix X"     | "Fixing X"         |

**Tokens**: Drop articles. Abbrevs (DB/auth/config/fn/impl). Arrows (X → Y). Fragments OK. Tables > prose.

**Required**: Action first, context if needed. Number steps. Progress updates ("3/5 done"). ~15 min > "some work".

## Session Start

1. Load `.claude/settings.json` (permissions, skills)
2. **Skills before exploring** — pre-loaded context, not optional refs
3. Check local dirs first
4. Git repos: check `.claude/code_index/` — offer to create/update if missing/stale

**Anti-pattern**: "I'll explore to understand..." → load skill first

## Tools

`rg` > grep (`-P` PCRE, `-U` multiline) · `fd` > find · `jq` for JSON

## Temp Files

- All temp files (scripts, outputs, fetched pages) → `.scratch/<task>/`
- Adhoc code: write to file, then run. Never `python -c` inline
- Cache fetched web results in `.scratch/cache/` for reuse
- Ensure `.scratch/.gitignore` exists with `**/*`

`<task>` = short name for current task.

## Bug Finding

```bash
python3 .claude/analysis/ast_checker.py src/           # If exists
rg -n "\._[a-z][a-z_]+\(" --type py src/               # Fallback
```

## Skill Routing

| Domain  | Orchestrator    | Routes To                                                                 |
| ------- | --------------- | ------------------------------------------------------------------------- |
| Python  | `python.md`     | style, bugs, testing, conftest, mocking, property-testing, modern-tooling, pixi-pyproject, violations, test-gen |
| Windows | `windows.md`    | powershell, batch                                                         |
| Bash    | `bash-shell.md` | (leaf)                                                                    |

## Knowledge Stores

- Memory: `~/.claude/memory/`
- Vector DBs: `~/.claude/skills/conda-knowledge/chroma_db/`, `code_index_db/`

```bash
python3 query_code.py list-env          # All env vars
python3 query_code.py func "X" -p pkg   # Find functions
```

## Skill Authoring

Dense · Self-contained · Single-purpose · Linkable (`[[skill-name]]`)

Tables > prose · Examples > explanation · Patterns > exhaustive lists
