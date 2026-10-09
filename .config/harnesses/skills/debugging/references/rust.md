# Rust Bug Patterns

Language-specific tables for [[debugging]]. Loaded only for Rust tasks.

## Feedback-loop tools

| Need                         | Command                                                  |
| ---------------------------- | -------------------------------------------------------- |
| Panic location + stack       | `RUST_BACKTRACE=1` (`full` for all frames)               |
| See test output              | `cargo test <name> -- --nocapture` / `cargo nextest run --no-capture` |
| Quick probe                  | `dbg!(&value)` (prints file:line, returns the value) — tag with `[DEBUG-` comment for cleanup |
| Structured logs              | `RUST_LOG=my_crate=debug` with `tracing`/`env_logger`    |
| Macro / derive output        | `cargo expand <module>`                                  |
| Undefined behavior in `unsafe` | `cargo +nightly miri test <name>`                      |
| Data races / memory          | `RUSTFLAGS=-Zsanitizer=thread cargo +nightly test` (also `address`) |
| Regression between commits   | `git bisect run cargo test --test <target>`              |
| Debugger                     | `rust-gdb` / `rust-lldb` on `target/debug/deps/<test-binary>` |

## Common Bugs {#common-bugs}

| Pattern                               | Bug                                                   | Fix                                         |
| ------------------------------------- | ----------------------------------------------------- | ------------------------------------------- |
| `unwrap` on `None`/`Err` {#unwrap}    | Panic on input that "can't happen"                    | Propagate with `?` ([[rust/errors]])        |
| Overflow in release {#overflow}       | Debug panics, release wraps silently                  | `checked_*` / `saturating_*`; test in `--release` too |
| Truncating `as` cast                  | `len as u32` drops high bits                          | `u32::try_from(len)?`                       |
| Clone to silence borrowck {#clone}    | Mutation lands on the copy, original unchanged        | Borrow `&mut`, or restructure ownership     |
| Iterator laziness                     | `.map(side_effect);` never runs (`unused_must_use`)   | `for` loop, or consume the iterator         |
| Shadowing surprise                    | `let value = ...;` in inner scope hides outer update  | Distinct names                              |
| Slice by byte index on UTF-8          | Panic: not a char boundary                            | `char_indices()` / `get(..)`                |
| `HashMap` iteration order             | Flaky output/tests                                    | `BTreeMap` or sort before compare           |
| Float equality / `NaN` in `sort`      | `partial_cmp().unwrap()` panics on NaN                | `total_cmp`                                 |
| Discarded `Result` {#discarded-result} | `let _ = write(...)` hides IO failure                | Handle or propagate                         |

## Concurrency

| Pattern                                      | Fix                                                     |
| -------------------------------------------- | ------------------------------------------------------- |
| `MutexGuard` held across `.await` {#guard-await} | Scope the guard in a block; or `tokio::sync::Mutex` |
| Guard held during long work / second lock    | Copy out what you need, drop the guard; consistent lock order |
| Blocking call in async (`std::fs`, `thread::sleep`) | `tokio::fs`, `tokio::time::sleep`, `spawn_blocking` |
| `Rc`/`RefCell` cycle leaks                   | `Weak` for back-references                              |
| `RefCell` double borrow → panic              | Narrow borrow scopes; don't hold `borrow()` across calls |
| Dropped `JoinHandle` hides task panic        | `.await` the handle / `JoinSet` and check the result    |

## Infinite Loops

| Pattern                               | Fix                                  |
| ------------------------------------- | ------------------------------------ |
| Status polling (only expected states) | `match` exhaustively on all terminal states + timeout |
| Graph walk without visited            | `HashSet` of visited ids             |
| Retry without bound                   | Max attempts + backoff               |

## Build / dependency

| Symptom                                       | Cause / fix                                              |
| --------------------------------------------- | -------------------------------------------------------- |
| Trait not implemented for a type that has it  | Two semver-incompatible versions of a crate: `cargo tree -d` |
| Feature works in one crate, not another       | Feature unification — check `cargo tree -e features -i <crate>` |
| Stale behavior after edits to `build.rs` inputs | Missing `cargo:rerun-if-changed`                       |
| Works locally, fails in CI                    | Toolchain drift — pin `rust-toolchain.toml`; MSRV check  |
