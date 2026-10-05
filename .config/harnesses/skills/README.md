# Skills

Harness-agnostic procedures, shared by Claude Code, Kilo, and OpenCode. Loaded on demand via the harness's skill
tool or referenced as `[[skill-name]]` links.

This file is documentation, not a skill — skills are only discovered as `<name>/SKILL.md`.

## Authoring rules

Each skill: simple, single-purpose, linkable. Complexity emerges from composition via `[[links]]`, never from the
part itself.

| Principle           | Description                              |
| ------------------- | ---------------------------------------- |
| Gini purity         | Each leaf skill handles ONE concept      |
| Orchestrator → leaf | Routers don't do work, they route        |
| Tables > prose      | Dense, scannable reference               |
| 1 example > many    | Show, don't tell                         |
| Linkable            | Use `[[skill-name]]` for composition     |
| Commands > descriptions | Runnable beats explained             |

Frontmatter requires `name` + `description` — routing matches on the description, so keep it accurate.

## Conventions

- Leaf-only reference material lives in `<name>/references/`, executables in `<name>/scripts/`.
- Single ownership: a rule table lives in exactly one skill; everyone else links (see ../README.md ownership table).
- Pattern memory (GOOD/BAD pairs a skill asks agents to save) lives in `<name>/patterns.md`.
