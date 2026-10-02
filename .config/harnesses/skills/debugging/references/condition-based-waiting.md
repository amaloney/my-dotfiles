# Condition-Based Waiting

`sleep`/`setTimeout`/`time.sleep()` in tests guesses at timing → passes fast machines, fails under load/CI.

**Wait for the actual condition, not a guess at how long it takes.**

## Core pattern

```typescript
// Bad: guessing
await new Promise((r) => setTimeout(r, 50));

// Good: polling the condition
await waitFor(() => getResult() !== undefined, "result available");
```

Generic poller — 10ms interval, always a timeout with a clear message:

```typescript
async function waitFor<T>(condition: () => T | undefined | null | false,
                          description: string, timeoutMs = 5000): Promise<T> {
  const start = Date.now();
  while (true) {
    const result = condition();           // fresh data every iteration
    if (result) return result;
    if (Date.now() - start > timeoutMs)
      throw new Error(`Timeout waiting for ${description} after ${timeoutMs}ms`);
    await new Promise((r) => setTimeout(r, 10));
  }
}
```

| Scenario | Pattern |
| --- | --- |
| Event | `waitFor(() => events.find(e => e.type === 'DONE'), "DONE event")` |
| State | `waitFor(() => machine.state === 'ready', "ready state")` |
| Count | `waitFor(() => items.length >= 5, "5 items")` |
| File | `waitFor(() => fs.existsSync(path), "file exists")` |

## Mistakes

- Poll < 10ms → CPU waste
- No timeout → infinite loop if condition never met
- Cache state outside the loop → stale data; call the getter inside

## When arbitrary timeout IS correct

1. First `waitFor` the triggering condition
2. Then wait a duration derived from **known** timing (e.g. tool ticks every 100ms → 200ms = 2 ticks)
3. Comment explaining WHY

Python equivalents: [[python/async-testing]] (pytest-timeout, anyio, flaky).
