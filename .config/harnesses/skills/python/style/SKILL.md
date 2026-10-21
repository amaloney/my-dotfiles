---
name: python/style
description: Route Python types, names, structure, and errors
invocation: auto
---

# Style Router

Handoff: `next: bug`.

| Concern    | Skill                 | Triggers                          |
| ---------- | --------------------- | --------------------------------- |
| Types      | [[python/types]]      | annotations, `->`, Optional, Self |
| Naming     | [[python/naming]]     | variables, constants, underscore  |
| Structure  | [[python/structure]]  | imports, layout, line length      |
| Exceptions | [[python/errors]]     | try/except, error handling        |
| Files      | [[python/org]]        | config.py, utils.py, where to put |
| Lint       | [[python/violations]] | ruff, lint, pycodestyle           |

Load specific leaf for focused task. Load all for full review.

## Violation Detection

"style violations" → run the gate script — one command runs every review-time gate (ruff, cryptic abbreviations,
single-letter bindings, relative imports, underscore module functions, ast structure):

1. `bash ~/.config/harnesses/scripts/style-gates.sh <path>` — non-zero exit = violations. Paste the output into the
   stage artifact as evidence; a stage result without gate output is invalid.

The script is the enforcement mirror of [[python/naming]] and [[python/structure]] — the leaves teach the rules, the
script runs them. Suppression: `# naming:allow` on the offending line.

"orchestrate" → agents per ruff rule + one for structure ([[python/structure]] + [[python/org]])
