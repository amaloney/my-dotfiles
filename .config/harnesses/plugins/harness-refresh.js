// Refresh .harness/code_index on session start and file edits.
// Debounced: refresh script skips if built < 10 min ago.
// Auto-loaded from ~/.config/kilo/plugins/ (global, all projects).

const REFRESH = `${process.env.HOME}/.config/harnesses/skills/code-index/scripts/harness-refresh.sh`;

let lastRun = 0;
const DEBOUNCE_MS = 600_000;

async function refresh($, directory) {
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
