---
name: research
description: Structured research with source tracking, paper management, and git workflow
invocation: user
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

## Node Frontmatter

```yaml
---
type: topic  # or constraint
id: <unique-id>
title: Human-Readable Title
hierarchy: { parent: null, children: [] }
relationships: { related: [], depends_on: [{id: x, reason: y}], informs: [] }
status: active  # active|resolved|removed|superseded
added: YYYY-MM-DD
papers: [{file: papers/x.pdf, doi: "10.x/x", citation: "Author (Year)"}]
sources: [{url: x, retrieved: YYYY-MM-DD, archived: <wayback>, snapshot: snapshots/x.md, relevance: why}]
---
```

## Requirements vs Constraints

| Aspect | Requirement | Constraint |
|--------|-------------|------------|
| Nature | Binary (yes/no) | Probabilistic |
| Function | Partitions space → S | Defines P(success) over S |
| In report | No | Yes |

## Search Log Format (`_meta/YYYY-MM-DD.md`)

```markdown
| Source | Topic | Useful | Notes |
|--------|-------|--------|-------|
| https://doi.org/... | topic | Yes | papers/author-year.pdf |
| https://example.com | topic | No | Outdated |
| https://doi.org/... | topic | — | PAYWALLED |
```

## Paper Workflow

1. Search → 2. Add to frontmatter (citation, DOI, abstract) → 3. Download: `curl -sL -o papers/x.pdf url`
4. Verify: `file papers/*.pdf` → 5. Log paywalled → 6. Update search log

**Don't commit PDFs** (copyright).

## BibTeX annote Field (Required)

`Keywords: tags. Constraints: increases/decreases P(C1)|informs C2|N/A. Evidence: strong|moderate|weak. Relevance: context.`

## Decision Matrix

| Option | C1 | C2 | P(success) | Evidence |
|--------|----|----|------------|----------|
| A | High | Low | Low | Strong |

High/Med/Low = P > 0.7 / 0.3-0.7 / < 0.3

## Git Workflow

Prefixes: `research:`, `docs:`, `fix:`, `chore:`
Constraint changes: commit before AND after propagation.

## Rules

- Expert feedback → new research topic
- Distinguish "uses X" from "about X"
- Stop when saturated (same papers across DBs)
- Always snapshot sources during initial research
- Titles: sentence case | Acronyms: spell out first use | Lines: max 120 | DOIs: prefer `https://doi.org/`
