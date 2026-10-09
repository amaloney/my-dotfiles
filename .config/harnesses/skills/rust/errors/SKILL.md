---
name: rust/errors
description: Rust error handling - Result and ?, thiserror vs anyhow, no unwrap outside tests, context
invocation: auto
---

# Errors

Handoff: `next: done`.

Recoverable failure → `Result`. Bug / broken invariant → `panic!`. Never the reverse.

## Crate choice

| Crate kind            | Error type                                          |
| --------------------- | --------------------------------------------------- |
| Library               | `thiserror` enum per module boundary — callers match on variants |
| Binary / application  | `anyhow::Result` + `.context(...)` at each boundary |
| Both (lib + bin)      | `thiserror` in lib, `anyhow` in `main.rs`           |

Record the choice in `profile.patterns.error_crate` ([[rust/recon]]); match what the crate already uses.

## `unwrap` / `expect`

| Where                                         | Allowed?                                             |
| --------------------------------------------- | ---------------------------------------------------- |
| Tests, doctests, examples                     | Yes                                                  |
| Provably infallible (`"127.0.0.1".parse::<IpAddr>()`, regex literal) | `expect("why it cannot fail")` |
| Anything touching IO, user input, network, env | **Never** — propagate with `?`                      |

Enforced by clippy `unwrap_used` / `expect_used` ([[rust/tooling]] lint table); tests opt out with
`#[cfg_attr(test, allow(clippy::unwrap_used))]` or `allow-unwrap-in-tests = true` in `clippy.toml`.

## Propagation and context

```rust
// BAD — loses which file
let text = fs::read_to_string(&path)?;

// GOOD — context at the boundary
let text = fs::read_to_string(&path)
    .with_context(|| format!("reading config {}", path.display()))?;
```

Add context once per boundary, not at every `?`. Don't stringify errors (`map_err(|error| error.to_string())`) — it
discards the source chain. Wrap with `#[from]` / `#[source]` in `thiserror` variants.

## Multi-failure fetch pattern

One logical result with several *non-fatal* failure modes (cache miss, fallback source) → `match` into a single value,
one exit:

```rust
let data = match fetch(&url) {
    Ok(data) => Some(data),
    Err(FetchError::NotFound) => { tracing::warn!(%url, "not found"); None }
    Err(error) => return Err(error.into()),   // fatal: propagate
};
if let (Some(data), Some(cache_dir)) = (&data, cache_dir) {
    write_cache(cache_dir, data)?;
}
Ok(data)
```

## Scoped matching

Match the narrowest variant (`io::ErrorKind::NotFound`) over catch-all `Err(_) =>`. A wildcard arm silently swallows
new variants added later — reserved for aggregator boundaries where one source must never sink the whole result,
and it must log.

## Never

- `let _ = fallible();` — discards a `Result` silently. Handle, propagate, or `.ok()` with a comment saying why.
- `panic!` / `unreachable!` for input validation.
- `Box<dyn Error>` in a library's public API — use a concrete error type.

[[debugging/references/rust]]
