# Handoff Contract

Rules for multi-agent pipelines. The main agent is an orchestrator only.

## Main agent

- Never reads, writes, or pastes code. Zero implementation in main context.
- Every delegation is a Task call whose prompt contains ONLY: artifact path(s) + stage spec.
- Routes strictly by stage verdicts (`next: <stage>`); never re-enters a completed stage.

## Subagents

- Do one thing, and only one thing, then hand off.
- Input contract: file path + stage spec. Hydrate from disc — never from prompt-embedded code.
- Output contract: exactly one short result — status + artifact path + `next: <stage>`.
- Recall own skill's pattern memory (GOOD/BAD examples) at start; save new patterns on novel fixes.
- Fan-out containment: sub-subagents are owned by the subagent that spawned them and are invisible to main; only
  aggregated results return.

## Artifacts

- The file on disc is the message bus. All state travels via artifacts, not context.
- Cross-stage references are `file:symbol` pointers, never inlined code.

## Termination

Handoff edges (`next:`) form a DAG. Reference links (`[[...]]`) transfer no control and are unconstrained.

| Rank | Stage          | Skills                                                                                                                            |
| ---- | -------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 0    | route          | `python`, `windows`, `conda`                                                                                                       |
| 1    | diagnose/plan  | `debugging`, `writing-plans`, `research`, `code-index`, `python/recon`, `python/repo-init`, `python/pixi-pyproject`, `python/modern-tooling` |
| 2    | create         | `python/style`, `python/types`, `python/naming`, `python/structure`, `python/errors`, `python/org`, `python/security`, `test-driven-development`, `bash-shell`, `markdown`, `artifacts`, `accessibility`, `windows/*`, `conda/*` |
| 3    | audit          | `bug`, `ast-check`                                                                                                                 |
| 4    | hygiene        | `code-hygiene`, `python/violations`                                                                                                |
| 5    | test           | `python/testing`, `python/test-gen`, `python/conftest`, `python/mocking`, `python/property-testing`, `python/async-testing`, `python/bdd`, `windows/dotnet-testing`, `build-watch-fix` |
| 6    | verify/ship    | `verify`, `git-commit`                                                                                                             |

Rules:

1. **Ranks** — `next:` is valid iff `rank(target) > rank(source)` or target is `done`. Skipping ranks is allowed.
   Only main may start a fresh pipeline (new artifact, fresh budget); skills never hand backward.
2. **Hop budget** — artifacts carry `hops: 6` in the header; each handoff decrements. At 0 the stage emits
   `next: done` + partial state. Longest known pipeline (route→create→audit→hygiene→test→verify) fits in 6.
3. **Visited ledger** — artifacts record `visited: [<stages>]`. A stage finding itself listed refuses and emits
   `next: done` + conflict note. Mechanically enforces "never re-enters a completed stage".
4. **No-revert** — a successor preserves the predecessor's accepted work. Finding earlier-stage output wrong →
   emit `next: done` + regression note; main decides whether to launch a fresh pipeline.
5. **`next: done`** — explicit terminal verdict. `verify` and `git-commit` are universal sinks any rank may
   terminate into.

## Hooks

- Format/lint (ruff, isort) and code re-indexing fire on edit/write events — orthogonal gate, never a delegated stage.

## Energy barrier

- No new code without a code-index verdict: similarity >= threshold hands `file:symbol` refs to refactor-python; below
  threshold (or no match) hands the spec to python.
- Greenfield creation requires an explicit "no match" verdict; it is the fallback, never the default.
