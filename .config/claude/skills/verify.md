---
name: verify
description: Run verification commands before claiming completion. Evidence before claims.
invocation: auto
---

# Verification Before Completion

**Evidence before claims, always.**

## The Gate

1. Identify verification command
2. Execute full command fresh
3. Read complete output + check exit code
4. Verify output confirms claim
5. Only then make claim

Skip any step = lying, not verifying.

## Requirements by Task

| Task           | Must Have                        | Insufficient         |
| -------------- | -------------------------------- | -------------------- |
| Tests pass     | Actual output showing 0 failures | "should pass"        |
| Build succeeds | Build command with exit 0        | Linter passing       |
| Bug fixed      | Original symptom test passes     | Code changes assumed |
| Regression     | Red-green cycle verified         | Single passing run   |

## Red Flags — Stop

- "should", "probably", "seems to"
- Satisfaction before verification
- Trusting success reports without independent check
- Any wording implying success without running verification

## Why

Broken trust, shipped undefined functions, wasted time on false completions. Run the command. Read the output. Then
speak.
