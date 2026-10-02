# Defense-in-Depth Validation

A single validation can be bypassed by other code paths, refactoring, or mocks.

**Validate at every layer data passes through. One fix = bug fixed; four layers = bug impossible.**

## The four layers

| Layer | Purpose | Example |
| --- | --- | --- |
| 1. Entry point | Reject invalid input at API boundary | `if (!dir?.trim()) throw new Error("workingDirectory required")` |
| 2. Business logic | Data makes sense for this operation | `if (!projectDir) throw new Error("projectDir required")` |
| 3. Environment guard | Block dangerous ops in specific contexts | `NODE_ENV=test` → refuse `git init` outside tmpdir |
| 4. Debug instrumentation | Forensics when other layers fail | `logger.debug("git init", { directory, cwd, stack })` |

## Applying

1. Trace the data flow — where does the bad value originate, where is it used
2. Map every checkpoint the data passes through
3. Add validation at each layer (entry → business → environment → debug)
4. Test by trying to bypass earlier layers — verify the next layer catches it

## Why all four

Each layer catches what others miss: alternate code paths bypass entry validation; mocks bypass
business-logic checks; platform edge cases need environment guards; structural misuse only shows in
debug logging. Don't stop at one validation point.
