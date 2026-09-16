---
name: python/violations
description: Fan-out detect/fix Python violations using ruff + pyproject.toml rules
invocation: manual
---

# Violations Fixer

## Detection

Use ruff with rules from `pyproject.toml`:

```bash
ruff check <path> --output-format json  # Structured output
ruff check <path>                        # Human readable
```

Rules configured in:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "ANN"]  # pyproject.toml
```

## Execution Mode

| Request                                  | Action                                           |
| ---------------------------------------- | ------------------------------------------------ |
| "orchestrate"/"fan-out"/"parallel"       | Spawn agents per rule — no `ruff --fix` shortcut |
| "fix violations" (no approach specified) | <5 auto-fixable → `ruff --fix`; else agents      |

## Protocol

1. **Detect**: `ruff check <path> --output-format json` → group by rule code
2. **Fix (sequential by rule)**: For each rule code with violations:
   ```
   Agent({ prompt: "Load [[python/style]]. Fix ONLY <rule_code> violations. Re-read before edit. <findings>" })
   ```
3. **Auto-fix safe rules**: `ruff check --fix --unsafe-fixes <path>` (only if user didn't request agents)
4. **Verify**: `ruff check <path>` — should return clean

Sequential fixes by rule code prevent overwrite conflicts.

## Common Rule Codes

| Code | Issue                        |
| ---- | ---------------------------- |
| E    | pycodestyle errors           |
| F    | pyflakes (unused, undefined) |
| B    | bugbear (common bugs)        |
| ANN  | missing type annotations     |
| SIM  | simplify                     |
| UP   | pyupgrade                    |

[[python/style]] [[python/bugs]]
