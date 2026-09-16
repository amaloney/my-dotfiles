# Memory Index

## Project

- [IESO 78886 Login Flow](project_ieso-78886-login-flow.md) — Current blockers: (anaconda3) prompt bug, pre-uninstall
  failures

## Feedback (Workflow/Principles)

- [No First-Person](feedback_no-first-person.md) — NEVER use I/me/my/mine/Let me — zero tolerance, repeatedly violated
- [Check Skills First](feedback_check-skills-first.md) — Read skill files before changes to catch documented gotchas
- [Debug Before Fix](feedback_debug-before-fix.md) — Don't guess at fixes; echo/print actual values first
- [Keep Code Simple](feedback_keep-code-simple.md) — Don't rename standard variables or add indirection layers
- [Comments Sync](feedback_comments-sync.md) — Always update comments when refactoring code
- [Line Limit](feedback_line-limit.md) — Keep code lines under 120 characters
- [Documentation Semantics](feedback_documentation-semantics.md) — "What not to do" comments must accurately describe
  actual behavior
- [Tiny Inconsistencies Anger Customers](feedback_tiny-inconsistencies-anger-customers.md) — UI differences between
  entry points erode trust
- [Respect Explicit Approach](feedback_respect-explicit-approach.md) — Execute requested approach; don't shortcut
- [Extend Not Create](feedback_extend-not-create.md) — Prefer extending existing code over creating new
- [Check Index First](feedback_check-index-first.md) — Query code_index before writing Python
- [No Clever Sugar](feedback_no-clever-sugar.md) — Explicit code over obscuring syntactic sugar
- [Python Pipeline](feedback_python-pipeline.md) — Generate → violations → bugs → test-gen flow
- [Complexity from Composition](feedback_complexity-from-composition.md) — Simple parts, complex wholes
- [PowerShell vs Batch Deletion](feedback_powershell-vs-batch-deletion.md) — Use PowerShell for file deletion; batch
  RMDIR fails silently
- [Full Path to PowerShell](feedback_full-path-to-powershell.md) — Installers have limited PATH; use %SystemRoot%\...
- [Anaconda Whoami Command](feedback_anaconda-whoami-command.md) — Use `--at anaconda.com`; no `--json` flag exists
- [Constructor Extra Files Timing](feedback_constructor-extra-files-timing.md) — extra_files can be overwritten; copy in
  post-install.bat

## Technical Reference

Now consolidated in skills:

- `conda-anaconda-tools.md` — auth, client, audit, linter, menuinst, constructor, env-log
