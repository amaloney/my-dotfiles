---
name: research
description: Structured research with source tracking, paper management, and git workflow
invocation: manual
---

# Research Skill

## Folder Structure

```
project/
  .gitignore          # exclude build/, papers/, snapshots/, *.pdf
  CHANGELOG.md        # Keep a Changelog format
  Makefile            # targets: report, graph, snapshots
  references.bib      # BibTeX bibliography
  scripts/            # build_graph.py, snapshot_source.py
  research/
    index.md
    graph.html        # interactive (generated)
    requirements/     # binary filters (hard prerequisites)
    constraints/      # probability distributions
    topics/<topic>/   # index.md, papers/, snapshots/ (gitignored)
    _meta/YYYY-MM-DD.md  # daily search logs
```

Schemas (node frontmatter, search log, BibTeX annote, decision matrix): [references/schema.md](references/schema.md) | Script templates: [scripts/](scripts/) (`build_graph.py`, `snapshot_source.py`)

## Requirements vs Constraints

| Aspect    | Requirement          | Constraint                |
| --------- | -------------------- | ------------------------- |
| Nature    | Binary (yes/no)      | Probabilistic             |
| Function  | Partitions space → S | Defines P(success) over S |
| In report | No                   | Yes                       |

## Paper Workflow

1. Search → 2. Add to frontmatter (citation, DOI, abstract) → 3. Download: `curl -sL -o papers/x.pdf url`
2. Verify: `file papers/*.pdf` → 5. Log paywalled → 6. Update search log

**Don't commit PDFs** (copyright).

## Git Workflow

Prefixes: `research:`, `docs:`, `fix:`, `chore:` Constraint changes: commit before AND after propagation.

## Rules

- Expert feedback → new research topic
- Distinguish "uses X" from "about X"
- Stop when saturated (same papers across DBs)
- Always snapshot sources during initial research
- Titles: sentence case | Acronyms: spell out first use | Lines: max 120 | DOIs: prefer `https://doi.org/`
