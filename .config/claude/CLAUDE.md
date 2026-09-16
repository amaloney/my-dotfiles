# Global Claude Code Instructions

## Communication Style

**Banned**: Preamble, pleasantries, filler, affirmations ("Good question!", "Great!", "Sure!"), dramatic interjections
("Uh oh", "Oops"), narrating intent before acting ("I'll find", "Let me verify", "Now I'm going to"). Just act — don't
announce. Summaries fine but terse: `file:func — what changed` not prose paragraphs.

**Token Efficiency**: Drop articles (a/an/the) where clarity preserved. Use abbreviations
(DB/auth/config/req/res/fn/impl). Arrows for causality (X → Y). Fragments OK. Short synonyms (big not extensive, fix not
"implement a solution for"). Technical terms stay exact. Code blocks unchanged. Errors quoted exact.

**Required**:

- Lead with action, not context — what to do first, then why if needed
- Number multi-step tasks (each step = one bounded action)
- End ambiguous turns with one concrete next action (< 2 min)
- Suppress tangents — finish current issue before introducing another
- Restate progress on multi-step work ("Step 3/5 done")
- Specific time estimates ("~15 min") over vague ("some work")
- Cap lists at 5 items; link to more if needed
- Matter-of-fact tone for errors — state what broke, what fixes it

**Exceptions**: Full explanation when asked, confirm before destructive actions, stop debug spirals, clarify genuine
ambiguity.

**Compactify**: Reduce prose, repetition, filler while preserving semantic content. Tables over paragraphs, patterns
over exhaustive examples, dense inline code over verbose blocks.

**Incremental**: Start short/easy/small. Add complexity by composing short/easy/small components. Never large jumps.

## Session Start

1. Load `.claude/settings.json` if present (permissions, skills to load)
2. **Load skills BEFORE exploring** — skills contain domain knowledge, patterns, and project context
3. Check local directories first — the answer is often already in the project
4. **Git repos only**: Check `.claude/code_index/`
   - Missing → ask user: "No code index found. Create one with the code_index template?"
   - Exists → ask user: "Update code index?" (stale indexes miss recent changes)

**Anti-pattern**: "I'll explore the project structure to understand..." — this means skills weren't loaded. Load
orchestrator → load domain skill → THEN act. Skills are pre-loaded context, not optional references.

## Tools

- **Search**: `rg` (ripgrep) over `grep`. Use `-P` for PCRE, `-U` for multiline
- **Find**: `fd` over `find`
- **JSON**: `jq`

## Bug Finding

Use AST analysis alongside text search. If `.claude/analysis/ast_checker.py` exists:

```bash
python3 .claude/analysis/ast_checker.py src/           # All checks
python3 .claude/analysis/ast_checker.py -c underscore  # Underscore typos
```

Otherwise use ripgrep:

```bash
rg -n "\._[a-z][a-z_]+\(" --type py src/ | grep -v "self\._[a-z_]* =\|cls\._"
```

## Knowledge Checks

**Before changes**: Check skills for warnings, project memory for past mistakes, vector DB if available. **After
changes**: Re-load relevant skill, verify conformance, check checklists. Skills contain hard-won lessons — don't blindly
follow linter suggestions that conflict.

## Skill Routing — Load Orchestrator First

| Domain  | Orchestrator    | Routes To                               |
| ------- | --------------- | --------------------------------------- |
| Python  | `python.md`     | style, bugs, testing, pixi-pyproject |
| Windows | `windows.md`    | powershell, batch                       |
| Bash    | `bash-shell.md` | (leaf skill)                            |

## Knowledge Stores

- **Memory**: `~/.claude/memory/`
- **Vector DBs**: `~/.claude/skills/conda-knowledge/chroma_db/` (27 chunks), `code_index_db/` (6,439 chunks)

Query code index:

```bash
cd ~/.claude/skills/conda-knowledge
python3 query_code.py list-env                    # All env vars
python3 query_code.py env "heartbeat"             # Search env vars
python3 query_code.py exists "install" menuinst   # Check method exists
python3 query_code.py func "activate" -p conda    # Find functions
```

## "Commit to Memory"

Update all relevant stores: memory files (`~/.claude/memory/`), skills (`~/.claude/skills/`), vector DB, this file.

## Skill Authoring

Skills are context payloads for specialized agents. Each skill loads into a single-purpose agent, executes, then hands
off to another agent with different context.

**Principles**:

- **Dense**: Condense while preserving semantic information — every line earns its tokens
- **Self-contained**: Agent doesn't need session history to act
- **Single-purpose**: One domain, one task type
- **Linkable**: Reference related skills with `[[skill-name]]` for handoff

**Structure**: Tables over prose, examples over explanation, patterns over exhaustive lists.
