---
name: rust/recon
description: Profile Rust project - outputs .harness/code_index/profile.json
invocation: manual
---

# Rust Project Recon

Handoff: `next: done`.

Run FIRST before other Rust skills. Outputs `.harness/code_index/profile.json`.

## When to Run

- Session start in Rust repo
- After major refactor or adding a workspace member
- When profile.json missing or stale (>7 days)

## Protocol

From the repo root (needs `cargo` + `jq`):

```bash
~/.config/harnesses/skills/rust/recon/scripts/profile.sh
```

The script reads `cargo metadata` and populates project identity, workspace members, targets, features, and
toolchain fields. Then review/fill `structure`, `patterns`, `testing`, and `linting` from the scan
(shape: `scripts/profile.schema.json`).

## Validation

```bash
jq '.' .harness/code_index/profile.json
```

## Staleness Check

Profile older than 7 days is stale — re-run the script:

```bash
find .harness/code_index/profile.json -mtime +7 2>/dev/null && echo "stale"
```

## Usage by Other Skills

Skills read profile.json instead of rescanning: constants belong in `{profile.patterns.config_rs_path}`, currently
scattered in `{profile.patterns.scattered_constants}`; MSRV in `{profile.project.rust_version}` bounds which std APIs
are allowed (e.g. `LazyLock` needs 1.80).

[[rust]] [[rust/structure]] [[rust/org]]
