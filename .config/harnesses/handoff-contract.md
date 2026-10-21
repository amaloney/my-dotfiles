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
- Full-scope create/audit/hygiene stages run `style-gates.sh` and report command + pass/fail; do not paste full successful output. Focused scope runs one targeted check.
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
| 1    | diagnose/plan | `debugging`, `writing-plans`, `research`, `code-index`, `python/recon`, `python/repo-init`, `python/pixi-pyproject`, `python/modern-tooling`, `rust/recon`, `rust/repo-init`, `rust/tooling`                                                                                                                                              |
| 2    | create        | `python/style`, `python/types`, `python/naming`, `python/structure`, `python/errors`, `python/org`, `python/security`, `rust/style`, `rust/types`, `rust/naming`, `rust/structure`, `rust/errors`, `rust/org`, `rust/security`, `test-driven-development`, `bash-shell`, `markdown`, `artifacts`, `accessibility`, `windows/*`, `conda/*` |
| 3    | audit         | `bug`, `ast-check`                                                                                                                                                                                                                                                                                                                        |
| 4    | hygiene       | `code-hygiene`, `discouraged-patterns`, `python/violations`, `rust/violations`                                                                                                                                                                                                                                                            |
| 5    | test          | `python/testing`, `python/test-gen`, `python/conftest`, `python/mocking`, `python/property-testing`, `python/async-testing`, `python/bdd`, `rust/testing`, `rust/test-gen`, `rust/property-testing`, `windows/dotnet-testing`, `build-watch-fix`                                                                                          |
| 6    | verify/ship   | `verify`, `git-commit`                                                                                                                                                                                                                                                                                                                    |

Rules:

1. **Ranks** — `next:` valid iff `rank(target) > rank(source)` or `done`. Only main starts fresh pipelines.
2. **Hop budget** — artifacts carry `hops: 6`; each handoff decrements; at 0 emit `next: done` + partial.
3. **Visited ledger** — artifacts record `visited: [<stages>]`. Stage in list → refuse, emit `next: done` + conflict.
4. **No-revert** — preserve predecessor's work. Wrong earlier output → `next: done` + regression note.
5. **`next: done`** — terminal. `verify` and `git-commit` are universal sinks.

## Hooks

Format/lint + re-indexing fire on edit/write (orthogonal, not a stage). Hookless harnesses use `style-gates.sh`.

## Energy barrier

No new code without code-index verdict. High similarity → refactor refs; low/none → create spec. An unavailable index is not a no-match; main may proceed on the explicit user request without rebuilding it.

## Python File Edits

Main agent NEVER directly edits `.py` files. All Python edits are delegated:

- Focused no-behavior change (1–3 lines, single file): `code-hygiene`, `scope: focused`; targeted check, then done.
- Feature/refactor/behavior change: full create → bug → hygiene → test → verify pipeline.

Focused scope skips audit fan-out, full lint, and test generation. Full scope retains the mandatory pipeline.
