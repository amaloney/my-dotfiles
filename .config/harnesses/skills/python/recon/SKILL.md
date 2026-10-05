---
name: python/recon
description: Profile Python project - outputs .harness/code_index/profile.json
invocation: manual
---

# Python Project Recon

Handoff: `next: done`.

Run FIRST before other Python skills. Outputs `.harness/code_index/profile.json`.

## When to Run

- Session start in Python repo
- After major refactor
- When profile.json missing or stale (>7 days)

## Protocol

From the repo root:

```bash
~/.config/harnesses/skills/python/recon/scripts/profile.sh
```

Then review/fill `.harness/code_index/profile.json`: the script populates
version, generated, and project fields; fill structure, patterns, testing, and
linting from the scan results (structure shape: `scripts/profile.schema.json`).

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

Skills read profile.json instead of rescanning: constants should be in
`{profile.patterns.config_py_path}`, currently scattered in
`{profile.patterns.scattered_constants}`.

[[python]] [[python/structure]] [[python/org]]
