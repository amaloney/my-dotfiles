// Refresh .harness/code_index on session start and file edits.
// Also rebuilds skill vectors when a SKILL.md changed (script self-filters).
// Debounced: refresh script skips if built < 10 min ago.
// Auto-loaded from ~/.config/kilo/plugins/ (global, all projects).

const REFRESH = `${process.env.HOME}/.config/harnesses/skills/code-index/scripts/harness-refresh.sh`;
const SKILL_VECTORS = `${process.env.HOME}/.config/harnesses/scripts/skill-vectors-refresh.sh`;

let lastRun = 0;
const DEBOUNCE_MS = 600_000;

async function refresh($, directory) {
  // skill-vectors self-filters (find-only unless a SKILL.md changed); run ungated
  try {
    await $`${SKILL_VECTORS}`.quiet();
  } catch {
    // refresh failures are non-fatal
  }
  if (Date.now() - lastRun < DEBOUNCE_MS) return;
  lastRun = Date.now();
  try {
    await $`${REFRESH} ${directory}`.quiet();
  } catch {
    // refresh failures are non-fatal
  }
}

export const HarnessRefreshPlugin = async ({ $, directory }) => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.created" || event.type === "file.edited") {
        await refresh($, directory);
      }
    },
  };
};
