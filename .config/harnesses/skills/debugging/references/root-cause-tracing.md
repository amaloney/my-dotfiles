# Root-Cause Tracing

Bugs manifest deep in the call stack; the error location is the symptom, not the cause.

**Trace backward until the original trigger, then fix at the source.**

## Process

1. Observe the symptom (exact error + location)
2. Find the immediate cause (what line directly fails)
3. Ask "what called this, with what value?" — one level up
4. Repeat until you find where the bad value originated
5. Fix at source. Never fix only at the symptom point.

## Instrumentation when manual tracing fails

Log **before** the dangerous operation, with full context:

```typescript
// TS: console.error shows in tests where loggers may be suppressed
const stack = new Error().stack;
console.error("DEBUG git init:", { directory, cwd: process.cwd(), stack });
```

```python
# Python equivalent
import traceback, sys
print(f"DEBUG init: dir={directory} cwd={os.getcwd()}", file=sys.stderr)
traceback.print_stack(file=sys.stderr)
```

Capture: `<test command> 2>&1 | grep 'DEBUG'` — find which test/caller triggers it.

## Case study: empty projectDir

- **Symptom**: `.git` created in `packages/core/` (source tree)
- **Trace**: `git init` got empty `cwd` → empty `projectDir` param → `Session.create()` passed `''` →
  test read `context.tempDir` before `beforeEach` ran → `setupCoreTest()` returns `{ tempDir: '' }` initially
- **Root cause**: top-level variable initialization reading a not-yet-set value
- **Fix at source**: made `tempDir` a getter that throws before `beforeEach`
- **Then**: defense-in-depth — validation added at all 4 layers the value passes through
  (see [defense-in-depth.md](defense-in-depth.md))

## Tips

- Log before the op, not after it fails
- Include: path/dir, cwd, env vars, stack
- Look for the pattern across traces (same test? same param?)
