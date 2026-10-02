---
name: python/style
description: Style router - routes to types, naming, structure, errors, org
invocation: auto
---

# Style Router

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

"style violations" → check both:

1. `ruff check <path>` → [[python/violations]]
2. `python3 .claude/analysis/ast_checker.py --check structure <path>`

"orchestrate" → agents per ruff rule + one for structure ([[python/structure]] + [[python/org]])
