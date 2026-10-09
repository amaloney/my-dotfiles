---
name: rust/naming
description: Rust naming conventions - case, abbreviations, constants, conversion and getter names
invocation: auto
---

# Naming

Handoff: `next: done`.

## Case (compiler-warned)

| Item                                   | Case                |
| -------------------------------------- | ------------------- |
| Crates, modules, fns, locals, fields   | `snake_case`        |
| Types, traits, enum variants           | `UpperCamelCase`    |
| `const`, `static`                      | `SCREAMING_SNAKE`   |
| Acronyms in types                      | `HttpClient`, not `HTTPClient` |

## Shared rules

| Rule                     | Good                    | Bad                   |
| ------------------------ | ----------------------- | --------------------- |
| No single-letter vars    | `for item in &items`    | `for i in &items`     |
| No cryptic abbreviations | `for record in records` | `for rec in records`  |
| Prefix constants         | `URL_CRATES_IO_API`     | `CRATES_IO_API_URL`   |

**Single-letter bindings are NEVER acceptable** — loops, closures, match arms, `if let`. `|x| x + 1` → `|count| count + 1`.

Exceptions with established meaning: generic type params (`T`, `E`, `K`, `V`), lifetimes (`'a`), and the `_` /
`_name` pattern for intentionally unused bindings.

| Bad    | Good                 |
| ------ | -------------------- |
| `rec`  | `record`             |
| `req`  | `request`            |
| `resp` | `response`           |
| `buf`  | `buffer`             |
| `ctx`  | `context`            |
| `cfg`  | `config`             |
| `err`  | `error`              |
| `res`  | `result` / `response` |

Allowed idioms (std/ecosystem vocabulary): `args`, `id`, `url`, `api`, `io`, `fmt`, `f` for the `fmt::Formatter`
parameter in `Display`/`Debug` impls (std convention).

**Enforcement gap — clippy does not catch this.** `clippy::many_single_char_names` only fires past a threshold.
Mandatory review-time gate on every file you create or edit:

```bash
grep -nE '\b(rec|req|resp|buf|ctx|cfg|err|res)\b' <file>
```

Clean output = pass. A review-rejected abbreviation not in the table → add it to the table and the pattern.

## API naming (Rust API Guidelines)

| Prefix / form    | Cost                    | Example                         |
| ---------------- | ----------------------- | ------------------------------- |
| `as_`            | free, borrowed → borrowed | `as_str()`, `as_bytes()`       |
| `to_`            | expensive or allocating | `to_string()`, `to_lowercase()` |
| `into_`          | consumes `self`         | `into_inner()`, `into_bytes()`  |
| getter           | no `get_` prefix        | `fn name(&self) -> &str`        |
| mutable getter   | `_mut` suffix           | `fn name_mut(&mut self)`        |
| fallible ctor    | `try_` / `TryFrom`      | `try_new()`, `TryFrom<&str>`    |
| bool             | predicate phrase        | `is_empty()`, `has_children()`  |

`get` is reserved for keyed lookups (`map.get(key)`).

## Underscore prefix

Rust has real privacy, so `_name` never means "private" — it means "intentionally unused" and silences
`unused_variables`. A `_name` that *is* used is a bug in naming; drop the underscore. Visibility is controlled by
`pub` ([[rust/structure]]).

[[rust/types]] [[debugging/references/rust]]
