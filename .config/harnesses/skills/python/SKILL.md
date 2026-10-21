---
name: python
description: Routes Python tasks to focused skills
invocation: auto
extensions: [".py"]
keywords: ["python"]
---

# Python Router

Handoff: `next: verify`.

Main agent only. Stage subagents load their assigned skill only. Main does not directly edit `.py` files.

| Work                            | Route                                                                                          |
| ------------------------------- | ---------------------------------------------------------------------------------------------- |
| Focused no-behavior, 1-file fix | `code-hygiene`, `scope: focused`; targeted check, then done                                    |
| Bug fix                         | `debugging` → `test-driven-development`                                                        |
| Feature/refactor                | create → bug → hygiene → test → verify                                                         |
| Types/naming/structure          | `python/style` → relevant leaf only                                                            |
| Lint cleanup                    | `python/violations`                                                                            |
| Tests                           | `python/testing`, `python/test-gen`, or `python/bdd`                                           |
| Repo/tooling setup              | Relevant [[python/repo-init]], [[python/pixi-pyproject]], or [[python/modern-tooling]]         |
| Security review                 | [[python/security]]                                                                            |

Use `code-index` only when the existing index is populated. Never build or refresh it during a gate; missing or empty means unavailable. Follow the user's workflow and handoff contract.
