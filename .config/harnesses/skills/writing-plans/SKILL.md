---
name: writing-plans
description: Write implementation plans for multi-step tasks, before touching code
invocation: auto
adapted-from: obra/superpowers v6.4.2 (MIT)
---

# Writing Plans

Handoff: `next: done`.

Plans for engineers who haven't seen the codebase. Document: files, names, signatures, spec values, tests. DRY. YAGNI.
TDD. Save: `.harness/plans/YYYY-MM-DD-<feature>.md`. Multiple subsystems → separate plans.

## Plan Header (required)

`# [Feature] Plan` — Goal (1 sentence), Architecture (2-3 sentences), Stack, Spec path. `## Global Constraints` —
version floors, naming, platforms (1 line each, exact values). `## Review Focus` — up to 5 failure modes no task tests;
add pinning tests.

## Task Right-Sizing

Task = smallest unit with test cycle + reviewer gate. Fold setup into owning task. Split where reject-one-approve-other
applies.

## Task Structure

````markdown
### Task N: [Component]

**Stage:** [create | audit | hygiene | test | verify]

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

Run: `pytest tests/path/test_file.py::test_name -v` Expected: FAIL with "function not defined"

- [ ] **Step 3: Implement `function(input: InputType) -> ResultType` in `exact/path/file.py`**

One line on approach when signature + test leave a choice; a body only for an algorithm they don't determine.

- [ ] **Step 4: Run test, verify it passes**

- [ ] **Step 5: Commit** — [[git-commit]] conventions
````

## Stage Annotations

Every task names stage: `create`, `audit`, `hygiene`, `test`, `verify`. Domain orchestrator maps skill per stage. No
annotations = incomplete → annotate from pipeline before starting.

## Step Granularity

One action + checkable result per step. Unambiguous, not complete:

- Test: name + assertions + spec values
- Code: signature + file; body left to implementer
- Verify: command + pass meaning
- Reference: Interfaces block, never repeat code

Plan > code = wrote the code. "TBD" / "handle edge cases" = decided nothing. Self-review catches both.

## Self-Review (this session, not subagent)

1. Spec coverage — gaps → add tasks
2. Step scan — one implementation per step
3. Type consistency — names match across tasks
4. Review Focus — each failure has a test
5. Proportion — plan >> spec = transcript

Fix inline.

## Execution Handoff

Save, self-review, ask user: subagent-per-task (thorough) vs native (fast). ≥3 tasks without method chosen → default
subagent, state reason.

## Context Budget

Orchestrator: plan skeleton + current task. Subagents hydrate from disc. Reviewers → `.harness/reviews/<task>.md`.
Gates: pass/fail only.
