---
name: rust/org
description: Rust file organization - config.rs constants, lib.rs + thin main.rs, path and cache conventions
invocation: auto
---

# Organization

Handoff: `next: done`.

## Crate shape

Binaries: logic in `src/lib.rs` (+ modules), `src/main.rs` only parses args, sets up logging, calls into the lib,
and maps errors to an exit code. This makes the logic testable from `tests/` without spawning the binary.

## Constants

| Scope                                          | Location                             |
| ---------------------------------------------- | ------------------------------------ |
| Shared by 2+ modules, or project-wide setting  | `src/config.rs` (`pub(crate) const`) |
| Used by exactly one module                     | Top of that module (after `use`)     |
| Inside a function body                         | **NEVER** — unless truly local to that fn |

`config.rs` holds only constants, statics, and settings types with cross-module reach — not a dumping ground. Shared
helper functions go in a named module for their concept, not `utils.rs`.

`const` for values computable at compile time; `static` + `std::sync::LazyLock` (MSRV 1.80) for computed values
(regexes, parsed defaults). No `lazy_static!` / `once_cell` in new code on MSRV ≥1.80.

## Path-valued constants

`const` can't hold a `PathBuf`; store `&str` and convert at the boundary, or use `LazyLock<PathBuf>`:

```rust
pub(crate) const METADATA_DIR: &str = "metadata";
pub(crate) static CACHE_ROOT: LazyLock<PathBuf> = LazyLock::new(|| Path::new(METADATA_DIR).join("cache"));
```

Compose with `Path::join`, never string concatenation or `format!("{dir}/{file}")`.

## Cache directory convention

Fetchers take `cache_dir: Option<&Path>`; `None` maps to a source-specific default under the project's metadata dir
(`CACHE_ROOT.join("crates-io")`). User-level caches use the `dirs` crate (`dirs::cache_dir()`), never hardcoded
`~/.cache`. Tests pass a `tempfile::TempDir` path.

## Colors

Theme colors (e.g. Gruvbox) are named constants in `config.rs` (`const GRUVBOX_RED: Color = Color::Rgb(...)`). No
hex literals at use sites.

[[rust/structure]] [[rust/naming]]
