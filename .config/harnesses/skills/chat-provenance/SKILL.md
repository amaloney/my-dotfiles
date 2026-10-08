---
name: chat-provenance
description: Verbatim provenance logging of user chats and agent/subagent outputs into .harness/chat-provenance/YYYY-MM-DD.md, plus capture of fetched web resources into .harness/research/ — append-only daily logs with # HH:MM headings, entry kinds, hash chain, session manifests. Answers "how we got here".
invocation: auto
---

# Chat Provenance

Handoff: `next: done`.

Records **verbatim** user input, agent output (including subagents), tool actions, decisions, and
session summaries into an append-only, per-repo daily log at `.harness/chat-provenance/YYYY-MM-DD.md`,
and captures fetched web resources into `.harness/research/YYYY-MM-DD/<slug>.md`. Grounded in
library and information science: ISO 15489 recordkeeping (records fixed at creation, corrections are
new entries), archival finding aids (descriptions derived from records, never the reverse), Dublin
Core bibliographic control (capture frontmatter + research `index.md`), and PROV-inspired relational
metadata (entry = content, `agent:`/`attr:` = attribution, `seq`/`prev` = ordering and fixity).

## Records vs descriptions (design rule)

The daily log is the **record** — verbatim, append-only, hash-chained. Everything else is a
**description** and must be regenerable from the log: session manifests (`sessions/`), `index.md`,
rendered narratives. Session summaries are the exception that proves the rule: a summary written at
session end contains information the log cannot regenerate, so the summary itself is appended to the
log as a `## summary` record with `basis: context-window | log-replay` and `derived_from:` metadata.

**Fonds boundary (documented dissent)**: state is repo-local by decision. Archival theory says the
fonds belongs to the creator — the user, whose activity spans repos; per-repo logs fragment it.
Repo-local was chosen to match the existing `.harness/` custody architecture. Consequence accepted:
a multi-repo session leaves one linked slice per repo, joined only by a shared `--session` id if the
caller supplies one. A future global registry (`~/.harness/provenance/`) would be the archivally
correct fix.

## Entry kinds

`user` · `assistant` · `action` (tool calls, redaction events) · `decision` (chose/rejected/because)
· `source` (web capture links) · `summary` (session summaries, dual-basis) · `session` (start/end
markers). Kind is the `## <kind>` heading; `--role user|assistant` remains the speaker axis.

## Entry format (v2)

```markdown
# 14:20

## user

agent: main | session: a1b2c3 | seq: 42 | attr: rmaloney | model: provider/model | at: main@1a2b3c4 | prev: sha256:…

````markdown
<verbatim content>
````
```

`seq` is per-day monotonic; `attr` is the human creator (`CHAT_PROVENANCE_USER`, else OS user);
`model` from `--model`/`CHAT_PROVENANCE_MODEL`; `at` is branch@commit at write time; `prev` hashes
the previous entry block (first entry hashes the frontmatter + first time heading) — a tamper-evident
chain. `event: <iso>` is added when event time differs from log time.

## Enforcement (logging is not agent-optional)

- **Kilo**: `~/.config/kilo/plugins/chat-provenance.js` logs user prompts (`chat.message`), assistant
  finals (`message.updated` with `time.completed`), tool actions (`tool.execute.after`), and session
  markers (`session.created`).
- **Claude Code**: `claude-hook.py` registered in `~/.claude/settings.json` for `UserPromptSubmit`,
  `Stop`, `SubagentStop`; dedupes repeated Stop fires via message id.

When acting manually (hooks absent), follow the trigger rules below.

## Trigger rules

1. **User message received** → log verbatim before acting (`--role user`).
2. **Final response** → log verbatim (`--role assistant`).
3. **Subagent, before returning** → log with `--agent <type> --task <task-id>`.
4. **Fetched web resource** → `save_source.py` before relying on it.
5. **Never edit or delete prior entries.** Corrections are new entries.
6. **Never log secrets.** Scripts redact common key patterns; every redaction emits its own
   `## action` entry (pattern class only) so the intervention is part of the record.

## Scripts (stdlib-only; content on stdin, never argv)

- `log_entry.py --role … [--kind …] [--agent …] [--session …] [--task …] [--model …] [--event-time …]`
- `save_source.py --source-url <url> [--type …] [--title …]` (stdin) or `--url <url>` (fetch).
  Captures get Dublin Core frontmatter + body `digest: sha256:…`; dedupe by body digest (`cached:`);
  differing content gets `-2`, `-3` suffixes; each capture appends a `## source` entry (with digest)
  and a research `index.md` row.
- `session.py start [--goal …] [--id …]` → marker entry + prints session id.
  `session.py end <id> --outcome … [--summary …] [--basis context-window|log-replay]` → appends
  `## summary` record + close marker. `session.py summarize <id> --replay` → summary drafted from
  log entries (covers crashed sessions). `session.py rebuild` → regenerates `sessions/` manifests +
  `index.md` from the logs; manifests carry ISAD(G)-minimal description (reference, level, title,
  dates, extent, creator, contributing agents, admin history, scope, arrangement, access, related,
  appraisal, description control). Never hand-edit manifests or index.
- `render.py [date] [--session id]` → readable narrative on stdout (prompts quoted, long assistant
  entries collapsed with pointers, decisions/actions/sources grouped).
- `verify.py [date|all]` → recomputes the hash chain and seq order; exit 1 on the first break.

## Concurrency

All writers hold an exclusive `fcntl.flock` on `.harness/chat-provenance/.lock` for the whole
scan+append (lockdir fallback on non-POSIX). Daily log writes are true appends (`open("a")`);
derived files (manifests, indexes) use tempfile + `os.replace`. Concurrent main/subagent writers
queue, never interleave or clobber.

## Failure modes

- Outside a git repo → scripts exit 1 with a clear message; **skip logging, never crash the session**.
- Empty stdin → exit 2; do not retry with fabricated content.
- Fetch error/timeout (`save_source.py --url`) → exit 1, no partial writes; note it and continue.
- Lock contention → flock blocks; writers queue.
- Git state capture (`at:`) fails (no commits, detached, slow) → field omitted, entry still written.

## Rules

- Verbatim means verbatim: no summarizing, truncating, or "cleaning up" logged text.
- One entry per event — do not batch multiple turns into one call.
- Redaction patterns live in `scripts/shared.py` (`SECRET_PATTERNS`); extend there, not inline.
- `basis:` honesty: only label a summary `context-window` if the agent wrote it from live context.
- Legacy entries (no `seq`/`prev`) are tolerated by `verify.py`/`render.py`; the chain starts at the
  first v2 entry in each file.
- PDF/paper workflows belong to the `research` skill (`snapshot_source.py`); `save_source.py` is
  session-scoped capture — different intent, no overlap.

Tests: `pixi run -e dev pytest` (suite in `tests/`, wired via pyproject `testpaths`).
