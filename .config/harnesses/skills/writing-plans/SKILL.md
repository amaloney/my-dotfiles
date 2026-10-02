---
name: writing-plans
description: Write implementation plans for multi-step tasks, before touching code
invocation: auto
adapted-from: obra/superpowers v6.4.2 (MIT)
---

# Writing Plans

Plans are written for an engineer who has not seen the codebase or the spec. They write idiomatic code
once given exact interfaces and tests; what they cannot know is what you decided — which files, names,
signatures, spec values, proving tests. Document those. DRY. YAGNI. TDD. Frequent commits.

**Save plans to:** `.harness/plans/YYYY-MM-DD-<feature>.md` (user preference overrides).

## Scope Check

Spec covers multiple independent subsystems → suggest separate plans, one per subsystem. Each plan
produces working, testable software on its own.

## Plan Header (required)

```markdown
# [Feature] Implementation Plan

**Goal:** [one sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [key technologies]
**Spec:** [path — the plan argues from the spec; executors read both]

## Global Constraints

[Project-wide requirements — version floors, naming rules, platform requirements — one line each,
exact values verbatim from the spec. Every task implicitly includes this section.]

## Review Focus

[Up to five input classes / failure modes the spec implies but no task's tests exercise, most likely
to bite first. For each line, add the pinning test to the owning task.]
```

## Task Right-Sizing

A task = smallest unit carrying its own test cycle and worth a reviewer's gate. Fold setup/config/docs
into the task whose deliverable needs them; split only where a reviewer could reject one task while
approving its neighbor. Each task ends with an independently testable deliverable.

## Task Structure

````markdown
### Task N: [Component]

**Files:**
- Create: `exact/path/file.py`
- Modify: `exact/path/existing.py:123-145`
- Test: `tests/path/test_file.py`

**Interfaces:**
- Consumes: [exact signatures from earlier tasks]
- Produces: [exact names/types later tasks rely on — the implementer sees only their own task]

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    assert function(input) == expected
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/path/test_file.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Implement `function(input: InputType) -> ResultType` in `exact/path/file.py`**

One line on approach when signature + test leave a choice; a body only for an algorithm they don't determine.

- [ ] **Step 4: Run test, verify it passes**

- [ ] **Step 5: Commit** — [[git-commit]] conventions
````

## Step Granularity

One action with a checkable result per step. A step is done when the implementer can write exactly one
reasonable thing from it — unambiguous, not complete:

- Test step: name + assertions as code, spec's exact values
- Code step: exact signature, file, spec-pinned values; implementer writes the body
- Verification step: command + the output meaning "passed"
- Reference to another task: point at its Interfaces block; never repeat its code

A plan longer than the code it describes has written the code instead. Lines deciding nothing ("TBD",
"handle edge cases", "add appropriate validation") are the opposite failure. Self-review catches both.

## Self-Review (before handoff, in this session — not a subagent)

1. **Spec coverage** — every spec section points to a task; gaps → add tasks
2. **Step scan** — every step yields exactly one reasonable implementation; no transcripts, no gaps
3. **Type consistency** — signatures/names match across tasks (`clearLayers` in Task 3, `clearFullLayers` in Task 7 = bug)
4. **Review Focus** — each implied input/failure has a task whose tests exercise it; empty section means checked-and-none, not skipped
5. **Proportion** — plan several × longer than spec = transcript; replace bodies with signatures + test names

Fix issues inline; no re-review pass.

## Execution Handoff

Save the plan, self-review, then ask the user to review and choose execution: subagent-per-task with
reviewer gates (thorough, more contexts) vs native single-session (fast, one final review). Recommend
one with a one-sentence reason from the plan (interface coupling, task count, cost of a shipped mistake).

**"Implement/execute the plan" is not an execution-method answer.** If the user says it without having
chosen a method, and the plan has ≥3 tasks: default to subagent-per-task, state that choice and the
one-sentence reason, and proceed — do not silently run native. Plans with <3 tasks may run native;
state that choice too.

## Orchestrator Context Budget

Orchestrator holds the plan skeleton + current task only; subagents hydrate from the plan file on disc.
Reviewers write verdicts to `.harness/reviews/<task>.md` — orchestrator reads verdicts, not diffs.
Gates are mechanical (lint/test exit codes): orchestrator sees pass/fail, not output, unless red.
