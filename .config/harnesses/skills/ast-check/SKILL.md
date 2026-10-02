---
name: ast-check
description: AST analysis - bug, security, quality, structure checks on Python source
invocation: auto
---

# AST Check

Run `scripts/ast_checker.py` — static analysis, no dependencies, executes not loads.

```bash
python3 ~/.config/harnesses/skills/ast-check/scripts/ast_checker.py --check bugs src/
python3 ~/.config/harnesses/skills/ast-check/scripts/ast_checker.py src/          # all checks
python3 ~/.config/harnesses/skills/ast-check/scripts/ast_checker.py --json src/   # machine-readable
```

## Checks

| Category    | Catches                                                                              |
| ----------- | ------------------------------------------------------------------------------------ |
| `bugs`      | Mutable defaults, unreachable code, bare except, undefined calls, `_func` typos      |
| `security`  | exec/eval, shell=True, yaml.load, pickle, hardcoded secrets, SQL injection           |
| `quality`   | Cyclomatic complexity >10, unused args, >6 returns, nesting >4, eager log formatting |
| `structure` | Constants after class definitions                                                    |

Individual: `-c underscore`, `-c undefined`.

## Output

Exit 1 if any error-severity issue. `--verbose` adds fix suggestions. `--json` for pipelines.
