---
name: rust/testing
description: Rust testing core - unit/integration/doc tests, assertions, nextest, rstest fixtures
invocation: auto
---

# Rust Testing Core

Handoff: `next: verify`.

## Targeted Testing

**NEVER run the whole workspace suite** while iterating — scope to the crate and test:

```bash
cargo nextest run -p <crate> -E 'test(parse_header)'     # name filter (substring)
cargo nextest run -p <crate> -E 'binary(integration)'    # one tests/integration.rs binary
cargo test -p <crate> parse_header                       # without nextest
cargo test -p <crate> --doc                              # doctests (nextest does not run them)
```

Add `-- --nocapture` (cargo test) / `--no-capture` (nextest) to see `println!`/`dbg!` output.

## Where tests live

| Kind        | Location                                  | Sees                    |
| ----------- | ----------------------------------------- | ----------------------- |
| Unit        | `#[cfg(test)] mod tests` at end of the file | private items (`use super::*;`) |
| Integration | `tests/<area>.rs` (shared helpers: `tests/common/mod.rs`) | public API only |
| Doc         | `///` examples on `pub` items             | public API; doubles as docs |

Binaries: logic lives in `lib.rs` so integration tests can reach it ([[rust/org]]).

## Basic patterns

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_valid_header() {
        let header = Header::parse("v=2").unwrap();
        assert_eq!(header.version, 2);
    }

    #[test]
    fn rejects_empty_input() {
        let error = Header::parse("").unwrap_err();
        assert!(matches!(error, ParseError::Empty), "got {error:?}");
    }

    #[test]
    fn returns_result() -> Result<(), ParseError> {   // `?` inside tests
        assert_eq!(Header::parse("v=3")?.version, 3);
        Ok(())
    }
}
```

## Assertions

| Need                    | Use                                              |
| ----------------------- | ------------------------------------------------ |
| Equality (shows diff)   | `assert_eq!(actual, expected)` — `pretty_assertions` for big structs |
| Enum variant / shape    | `assert!(matches!(value, Pattern { .. }))`       |
| Float                   | `assert!((actual - expected).abs() < 1e-9)`      |
| Panic expected          | `#[should_panic(expected = "index out of range")]` — prefer testing a `Result` |
| Large output            | `insta::assert_snapshot!` / `assert_debug_snapshot!` |

Always pass a message on bare `assert!` so failures say what was observed.

## Fixtures and parametrization (rstest)

`rstest` is the pytest-fixture analogue — use it when a crate has repeated setup or tables of cases.

```rust
use rstest::{fixture, rstest};

#[fixture]
fn registry() -> Registry { Registry::with_defaults() }

#[rstest]
#[case("v=1", 1)]
#[case("v=42", 42)]
fn parses_versions(registry: Registry, #[case] input: &str, #[case] expected: u32) {
    assert_eq!(registry.parse(input).unwrap().version, expected);
}
```

Filesystem: `tempfile::TempDir` (dropped = deleted), never a fixed path under `/tmp`. Env vars: don't mutate
`std::env` in tests (process-global, races under the parallel runner) — inject config instead.

## Not yet covered

Mocking (`mockall`), async (`#[tokio::test]`), BDD (`cucumber`) — see the [[rust]] router's "Not yet covered" note.

[[rust/property-testing]] [[rust/test-gen]]
