---
name: token-efficiency
description: Token optimization - output style, context management, compression triggers
invocation: auto
---

# Token Efficiency

## Output Style (Elements of Style)

| Rule                  | Example                                        |
| --------------------- | ---------------------------------------------- |
| Active voice          | "X broke" not "was broken by X"                |
| Positive form         | "ignored" not "did not consider"               |
| Omit needless words   | Cut "in order to", "the fact that", "actually" |
| Specific > vague      | "auth.py:42" not "the file"                    |
| Emphatic words at end | "The fix: connection pooling"                  |

**No first-person** — "Fixing X" not "I'll fix X". LLMs aren't entities.

## Context Budget

| Utilization | Action                              |
| ----------- | ----------------------------------- |
| 60%+        | Consider partitioning to sub-agents |
| 70%+        | Trigger compaction/summarization    |
| 80%+        | Mask old tool outputs               |

**Allocate**: tool outputs 35%, history 30%, retrieved docs 20%, buffer 15%

## Observation Masking

After 3+ turns, replace verbose tool output with:

```
[Obs:{ref_id} elided. Key: {summary}. Retrievable.]
```

**Never mask**: current task outputs, last turn, active debugging errors

## Compaction Rules

1. Tool outputs first (consume 80%+ of tokens)
2. Old conversation turns second
3. Retrieved docs third
4. **Never** system prompt, tool definitions, schemas

Target: 50-70% reduction, <5% quality loss

## Structured Summaries

```markdown
## Intent

[Task goal]

## Files Modified

- path/file.py: what changed

## Decisions

- Key choice and why

## Next

1. Immediate action
```

## KV-Cache Optimization

Order prompts for cache stability:

1. System prompt (immutable)
2. Tool definitions (stable)
3. Templates/few-shot (reusable)
4. History (grows but shares prefix)
5. Current query (dynamic, always last)

**Gotcha**: Single whitespace change invalidates entire downstream cache

## Measure

Track **tokens-per-task** not tokens-per-request. If agent re-reads files it already processed → compression too
aggressive.

| Signal              | Problem            |
| ------------------- | ------------------ |
| Re-fetching         | Lost critical info |
| Repetition          | Attention degraded |
| Missed instructions | Context too full   |

## Partitioning

When task > 60% window: split to sub-agents with isolated contexts. Break-even requires 3+ subtasks (coordination
overhead is real).

[[context-fundamentals]] [[memory-systems]]
