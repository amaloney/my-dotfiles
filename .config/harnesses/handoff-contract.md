# Handoff Contract

Rules for multi-agent pipelines. The main agent is an orchestrator only.

## Main agent

- Never reads, writes, or pastes code.
- Every delegation is a Task call whose prompt contains ONLY: artifact path(s) + stage spec.
- Routes strictly by stage verdicts (`next: <stage>`).

## Subagents

- Do one thing, then hand off.
- Input contract: file path + stage spec. Hydrate from disc — never from prompt-embedded code.
- Output contract: exactly one short result — status + artifact path + `next: <stage>`.
- Research/explore subagents return only concise findings with `file:line` pointers; no pasted code, narration, or broad
  file summaries.
- Full-scope create/audit/hygiene stages run `style_gates.py` and report command + pass/fail; do not paste full
  successful output. Focused scope runs one targeted check.
- Read own pattern memory only when relevant; save novel patterns only.
- Fan-out: sub-subagents invisible to main; only aggregates return.

## Artifacts

- The file on disc is the message bus.
- Cross-stage references are `file:symbol` pointers, never inlined code.

## Termination

Handoff edges (`next:`) form a DAG. Reference links (`[[...]]`) transfer no control and are unconstrained.

| Rank | Stage         | Skills                                                                                                                                                                                                                                                                                                                                    |
| ---- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0    | route         | `python`, `rust`, `windows`, `conda`                                                                                                                                                                                                                                                                                                      |
| 1    | diagnose/plan | `debugging`, `writing-plans`, `research`, `code-index`, `python/repo-init`, `python/pixi-migration-reference`, `python/modern-tooling`, `rust/recon`, `rust/repo-init`, `rust/tooling`                                                                                                                                    |
| 2    | create        | `python/naming`, `python/structure`, `python/security`, `rust/style`, `rust/types`, `rust/naming`, `rust/structure`, `rust/errors`, `rust/org`, `rust/security`, `test-driven-development`, `bash-shell`, `artifacts`, `accessibility`, `windows/*`, `conda/*` |
| 3    | audit         | `bug`, `ast-check`                                                                                                                                                                                                                                                                                                                        |
| 4    | hygiene       | `code-hygiene`, `discouraged-patterns`, `rust/violations`                                                                                                                                                                                                                                                                                 |
| 5    | test          | `python/testing`, `python/test-gen`, `python/conftest`, `python/mocking`, `python/property-testing`, `python/async-testing`, `rust/testing`, `rust/test-gen`, `rust/property-testing`, `windows/dotnet-testing`, `build-watch-fix`                                                                                          |
| 6    | verify/ship   | `verify`, `git-commit`                                                                                                                                                                                                                                                                                                                    |

Rules:

1. **Ranks** — `next:` valid iff `rank(target) > rank(source)` or `done`. Only main starts fresh pipelines.
2. **Hop budget** — artifacts carry `hops: 6`; each handoff decrements; at 0 emit `next: done` + partial.
3. **Visited ledger** — artifacts record `visited: [<stages>]`. Stage in list → refuse, emit `next: done` + conflict.
4. **No-revert** — preserve predecessor's work. Wrong earlier output → `next: done` + regression note.
5. **`next: done`** — terminal. `verify` and `git-commit` are universal sinks.

## Hooks

Format/lint + re-indexing fire on edit/write (orthogonal, not a stage). Hookless harnesses use `style_gates.py`.

## Energy barrier

No new code without code-index verdict:

1. **Duplicate check**: Run `find_duplicates()` for exact name matches. Existing name → refactor or reuse.
2. **Similarity check**: Search for similar functionality. High similarity (≥0.8) → refactor refs.
3. **No match**: Create spec only after both checks pass.

An unavailable index is not a no-match; main may proceed on explicit user request without rebuilding it.

**TYPE_CHECKING imports are exempt from "unused import" cleanup.** They exist to prevent circular imports.

## Python File Edits

Enforced by `style_gates.py` hooks:

- **edit tier** (PostToolUse): `style_gates.py --event edit` runs ruff + AST rules (naming, private, wrapper, comment,
  docstring) on each edited file. Findings feed back as hook errors and are fixed in the same turn.
- **stop tier** (SubagentStop/Stop): `style_gates.py --event stop` runs the full suite on all files edited in the
  session, adding the reuse check (against code_index) and pyrefly. Max 3 rounds before letting the agent stop.

Delegate Python implementation to `python-implementer` agent. In the brief, include relevant existing functions from
code_index — extending existing code is preferred over creating new functions.

Focused scope skips audit fan-out, full lint, and test generation. Full scope retains the mandatory pipeline.
