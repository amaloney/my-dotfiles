---
name: markdown
description: Markdown formatting - prettier canonical
invocation: auto
extensions: [".md", ".markdown"]
keywords: ["markdown"]
---

# Markdown

Handoff: `next: done`.

Prettier is the formatter. Repo `.prettierrc` overrides; absent → prettier defaults.

## Commands

```bash
prettier --check "**/*.md"        # CI check, no writes
prettier --write "**/*.md"        # Format all
prettier --write <file.md>        # Single file
```

Not installed: `command -v prettier || npm i -g prettier`

## Rules

- Exclude `node_modules/`, build output via `.prettierignore`
- Format after editing, before commit
- Never hand-align tables — prettier owns whitespace
- Keep semantic content; prettier may reflow prose per repo config
