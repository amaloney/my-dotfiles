# Claude Code configuration

Claude-specific pieces of the harness setup.

Shared architecture: [../README.md](../README.md) · Skill authoring: [../skills/README.md](../skills/README.md) ·
Code-index theory + CLI: [../skills/code-index/scripts/README.md](../skills/code-index/scripts/README.md)

## Files

- `settings.json` → `~/.claude/settings.json` (copied by install.sh, not linked — local divergence reconciles manually)
- `keybindings.json` → `~/.claude/keybindings.json`

## Hooks (settings.json)

- `SessionStart` + `PostToolUse(Edit|Write)`: `harness-refresh.sh` — keeps the repo's `.harness/code_index/` fresh.
  Kilo achieves the same via `../plugins/harness-refresh.js`; both exist by design (different mechanism per harness).
- `MessageDisplay`: `check-pronouns.sh`.

## Links into shared config

`~/.claude/CLAUDE.md` → `../AGENTS.md`, and `~/.claude/{skills,scripts,agents}` → the shared dirs here.
The handoff contract reaches Claude via the `@`-import line in `../AGENTS.md`.
