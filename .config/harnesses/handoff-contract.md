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

## Hooks

- Format/lint (ruff, isort) and code re-indexing fire on edit/write events — orthogonal gate, never a delegated stage.

## Energy barrier

- No new code without a code-index verdict: similarity >= threshold hands `file:symbol` refs to refactor-python; below
  threshold (or no match) hands the spec to python.
- Greenfield creation requires an explicit "no match" verdict; it is the fallback, never the default.
