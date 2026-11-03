---
name: python
description: Routes Python tasks to focused skills
invocation: auto
extensions: [".py"]
keywords: ["python"]
---

# Python Router

Handoff: `next: verify`.

Main agent only. Stage subagents load their assigned skill only. Main does not directly edit `.py` files. Use the shared
Conda policy for all Python environments, dependencies, and execution.

## Delegation

Delegate Python implementation to the `python-implementer` agent. In the brief:

1. Search `code_index.json` for functions with similar names/purposes
2. Include relevant existing functions (name and path) in the prompt
3. Instruct to extend existing code rather than create new functions

Hooks enforce style after every edit and at subagent stop — findings feed back until fixed.

## Routing

| Work                            | Route                                                       |
| ------------------------------- | ----------------------------------------------------------- |
| Focused no-behavior, 1-file fix | `code-hygiene`, `scope: focused`; targeted check, then done |
| Bug fix                         | `debugging` → `test-driven-development`                     |
| Feature/refactor                | create → bug → hygiene → test → verify                      |
| Tests                           | `python/testing` or `python/test-gen`                       |
| Repo/tooling setup              | [[python/repo-init]] or [[python/modern-tooling]]           |
| Security review                 | [[python/security]]                                         |

## Style (hook-enforced)

Hooks run `style_gates.py` automatically:
- **edit tier**: ruff format/check, naming, private, wrapper, comment, docstring
- **stop tier**: adds reuse check against code_index + pyrefly

| Concern    | Skill                | Triggers                         |
| ---------- | -------------------- | -------------------------------- |
| Naming     | [[python/naming]]    | variables, constants, underscore |
| Structure  | [[python/structure]] | imports, layout, exceptions, org |
| Types      | (hook: pyrefly)      | annotations, `->`, Optional      |
| Lint       | (hook: ruff)         | ruff, lint, pycodestyle          |

Suppress: `# style:allow`, `# naming:allow`, `# noqa: CODE`, or `# pyrefly: ignore`.

Use `code-index` only when the existing index is populated. Never build or refresh it during a gate; missing or empty
means unavailable. Follow the user's workflow and handoff contract.
