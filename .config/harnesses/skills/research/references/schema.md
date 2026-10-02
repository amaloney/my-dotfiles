# Schemas

## Node Frontmatter

```yaml
---
type: topic # or constraint
id: <unique-id>
title: Human-Readable Title
hierarchy: { parent: null, children: [] }
relationships: { related: [], depends_on: [{ id: x, reason: y }], informs: [] }
status: active # active|resolved|removed|superseded
added: YYYY-MM-DD
papers: [{ file: papers/x.pdf, doi: "10.x/x", citation: "Author (Year)" }]
sources: [{ url: x, retrieved: YYYY-MM-DD, archived: <wayback>, snapshot: snapshots/x.md, relevance: why }]
---
```

## Search Log Format (`_meta/YYYY-MM-DD.md`)

```markdown
| Source              | Topic | Useful | Notes                  |
| ------------------- | ----- | ------ | ---------------------- |
| https://doi.org/... | topic | Yes    | papers/author-year.pdf |
| https://example.com | topic | No     | Outdated               |
| https://doi.org/... | topic | —      | PAYWALLED              |
```

## BibTeX annote Field (Required)

`Keywords: tags. Constraints: increases/decreases P(C1)|informs C2|N/A. Evidence: strong|moderate|weak. Relevance: context.`

## Decision Matrix

| Option | C1   | C2  | P(success) | Evidence |
| ------ | ---- | --- | ---------- | -------- |
| A      | High | Low | Low        | Strong   |

High/Med/Low = P > 0.7 / 0.3-0.7 / < 0.3
