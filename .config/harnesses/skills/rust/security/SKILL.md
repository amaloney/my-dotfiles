---
name: rust/security
description: Rust security patterns - unsafe audit, supply chain, overflow, insecure defaults, common vulns
invocation: auto
---

# Rust Security

Handoff: `next: done`.

Memory safety is the compiler's job — until `unsafe`, FFI, or a dependency opts out. Logic vulns are unchanged.

## `unsafe`

| Rule                                   | Detail                                              |
| -------------------------------------- | --------------------------------------------------- |
| Forbid by default                      | `unsafe_code = "forbid"` in `[lints.rust]`; crates that need it use `deny` + per-item `#[allow]` |
| Every block justified                  | `// SAFETY:` comment stating the invariant upheld (clippy `undocumented_unsafe_blocks`) |
| Minimal scope                          | Wrap one operation, not the whole function         |
| Safe wrapper                           | Expose a safe API that enforces the invariant; `unsafe fn` only if the caller must uphold it (`# Safety` doc) |
| Verify                                 | `cargo +nightly miri test` on code with `unsafe`    |

## Supply chain

```bash
cargo audit                  # RustSec advisories against Cargo.lock
cargo deny check             # advisories + licenses + banned/duplicate crates + allowed sources
cargo geiger                 # unsafe usage across the dependency tree (when auditing a new dep)
```

New dependency → check maintenance, download count, `unsafe` footprint, and `build.rs` / proc-macro presence (both
run arbitrary code at build time).

## Insecure defaults

| Category          | VULNERABLE                                       | SECURE                                     |
| ----------------- | ------------------------------------------------ | ------------------------------------------ |
| Fallback secrets  | `env::var("KEY").unwrap_or("dev".into())`        | `env::var("KEY").context("KEY not set")?`  |
| Secret in logs    | `#[derive(Debug)] struct Creds { token: String }` | `secrecy::SecretString`; manual `Debug` that redacts |
| Fail-open         | `env::var("AUTH").map_or(false, ...)`            | Default to the secure branch               |
| Weak crypto       | `md5`, `sha1` crates for passwords               | `argon2` / `password-hash`                 |
| Homemade crypto   | XOR / hand-rolled AES modes                      | `ring`, `rustls`, RustCrypto AEADs         |
| TLS off           | `danger_accept_invalid_certs(true)`              | Default verification; per-host pinning only |
| Permissive files  | `.mode(0o666)` / `0o777`                         | `0o600` for secrets, `0o644` max otherwise |
| Timing leak       | `token == expected` on secrets                   | `subtle::ConstantTimeEq`                   |

## Sharp edges

| Category              | Bad                                    | Good                                     |
| --------------------- | -------------------------------------- | ---------------------------------------- |
| Integer overflow      | `len + offset` (wraps silently in release) | `checked_add(...).ok_or(...)?`       |
| Truncating casts      | `value as u32`                         | `u32::try_from(value)?`                  |
| Untrusted indexing    | `buffer[index]`                        | `buffer.get(index)`                      |
| Unbounded alloc       | `Vec::with_capacity(header.len)`       | Cap against a max before allocating      |
| Lenient deserialize   | serde struct accepts unknown fields    | `#[serde(deny_unknown_fields)]` on untrusted input |
| Panics as DoS         | `unwrap()` on request data             | Propagate → 4xx ([[rust/errors]])        |

## Common vulns

| Vuln              | VULNERABLE                                           | SECURE                                      |
| ----------------- | ---------------------------------------------------- | ------------------------------------------- |
| SQL injection     | `format!("SELECT ... WHERE id = {id}")`              | `sqlx::query!("... WHERE id = $1", id)`     |
| Command injection | `Command::new("sh").arg("-c").arg(format!("git {input}"))` | `Command::new("git").arg(input)` (no shell) |
| Path traversal    | `base.join(user_path)` (absolute `user_path` replaces `base`) | Reject absolute/`..` components, then `canonicalize` and check `starts_with(base)` |
| SSRF              | `reqwest::get(user_url)`                             | Allowlist scheme + host                     |
| Unsafe deserialize | `bincode` on untrusted bytes without size limit     | Size-limited config; schema'd formats       |

## Detection

```bash
rg -n 'unsafe\s*(\{|fn|impl)' --type rust                  # unsafe sites — each needs SAFETY:
rg -n 'unwrap_or\(\s*"[^"]*"' --type rust                   # fallback secrets/defaults
rg -n 'danger_accept_invalid|verify_hostname\(false' --type rust
rg -n 'Command::new\("(sh|bash|cmd)"\)' --type rust         # shell invocation
rg -n 'format!\(\s*"(SELECT|INSERT|UPDATE|DELETE)' --type rust
rg -n '\bas (u8|u16|u32|i32|usize)\b' --type rust            # truncating casts to review
```

[[rust/errors]] [[debugging/references/rust]]
