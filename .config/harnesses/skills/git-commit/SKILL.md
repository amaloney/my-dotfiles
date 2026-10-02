---
name: git-commit
description: Commit conventions - staging, attribution, message format
invocation: auto
---

# Git Commit

- `git add` with explicit filenames only — never `git add .` or `-A`
- Attribution: `Assisted-by: AGENT_NAME:MODEL_VERSION` (not `Co-Authored-By`)
- Commit message: backtick-quote code identifiers; pass via heredoc:

```bash
git commit -F- <<'EOF'
fix: quote variables in scratch cleanup

Use `"$file"` in rm calls.

Assisted-by: AGENT_NAME:MODEL_VERSION
EOF
```
