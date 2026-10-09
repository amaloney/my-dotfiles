---
name: rust/types
description: Rust signature rules - borrowing, ownership, newtypes, Option, impl Trait vs dyn
invocation: auto
---

# Types and Signatures

Handoff: `next: done`.

The compiler enforces annotations; the rules here are about choosing the *right* types.

## Parameters: borrow the most general form

| Rule                   | Use                                   | Avoid                     |
| ---------------------- | ------------------------------------- | ------------------------- |
| String input           | `&str`                                | `&String`, `String` (unless storing) |
| Slice input            | `&[T]`                                | `&Vec<T>`                 |
| Path input             | `&Path` or `impl AsRef<Path>`         | `&str`, `&PathBuf`        |
| Taking ownership       | `T` / `impl Into<String>` when stored | `&T` then `.clone()` inside |
| Callbacks              | `impl Fn(T) -> U`                     | `Box<dyn Fn>` (unless stored heterogeneously) |

## Returns

- Paths are `PathBuf`, never `String` — params, returns, and constants alike (mirrors [[rust/org]]).
- **Single return shape.** Fallible → `Result<T, E>`; absent-but-valid → `Option<T>`. Never a sentinel (`-1`, `""`,
  empty `Vec` meaning "failed"). Never `Option` to mean "failed" — the caller loses why. Error design: [[rust/errors]].
- Return owned values (`String`, `Vec<T>`) unless returning a view into `self` (`&str` tied to `&self`).
- A tuple for "result + metadata" (`(data, rate_limit)`) is one coherent type when both are always produced; past
  two fields, name it with a struct.

## Newtypes over primitives

Two values with the same primitive type and different meanings get distinct types:
`struct UserId(u64);` vs `struct OrderId(u64);`. Swapped arguments become compile errors. Derive only what is needed
(`Debug, Clone, Copy, PartialEq, Eq, Hash`); don't `impl Deref` to the inner type — that erases the distinction.

## Clones

`.clone()` to satisfy the borrow checker is a smell — restructure ownership first (borrow, split the borrow, move,
`std::mem::take`). Acceptable: `Copy`-cheap types, `Arc`/`Rc` handle clones (write `Arc::clone(&handle)` so the
cost is visible), and genuinely needing two owners.

## Generics vs trait objects

| Situation                                | Use              |
| ---------------------------------------- | ---------------- |
| One concrete type per call site          | `impl Trait` / generics |
| Heterogeneous collection, plugin registry | `Box<dyn Trait>` |
| Public API, compile-time cost matters    | `dyn` to cut monomorphization |

Don't add a trait with a single implementor "for testability" — that is [[rust/structure]]'s sugar gate at type level.

## Lifetimes

Elide wherever the compiler allows. A named lifetime needs a reason a reader can see (two inputs, one output tied to
one of them). Structs holding references (`struct Parser<'a>`) only when the borrow is short-lived and measured;
otherwise own the data.

[[rust/naming]] [[debugging/references/rust]]
