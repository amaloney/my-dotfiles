---
name: build-watch-fix
description: Build/CI failure loop - error-signature fixes on top of the debugging methodology
invocation: manual
---

# Build-Watch-Fix

Handoff: `next: verify`.

Trigger: build/CI/watch output failing. The build output **is** the feedback loop — [[debugging]] Phase 1 is free.
Follow [[debugging]] Phases 2-6; this skill adds only build-specific content.

## Failure → Fix Mapping

Match error signature before hypothesising:

| Pattern                  | Fix Strategy                           |
| ------------------------ | -------------------------------------- |
| `ModuleNotFoundError: X` | Add X to meta.yaml requirements        |
| `UnsatisfiableError`     | Add missing dep to resolver queue      |
| `sha256 mismatch`        | Fetch correct hash, update meta.yaml   |
| `Hunk FAILED`            | Regenerate patch from upstream         |
| `overlinking`            | Add lib to run_exports or requirements |
| Build timeout            | Increase resource limits               |

No table match → full [[debugging]] methodology (hypothesise first, don't guess-fix).

## Bounds

- 3 fix attempts per failure → stop, report to user
- Error signature unchanged after a fix → wrong hypothesis; re-enter [[debugging]] Phase 3, don't retry the same fix

## Orchestration

"orchestrate" → one agent per unique error signature; coordinator aggregates. Each agent owns its signature's full
debug cycle.

[[python]] [[conda-packaging]]
