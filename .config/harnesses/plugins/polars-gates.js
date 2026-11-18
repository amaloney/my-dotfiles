// Runs polars_gates.py after edits to Python files that import polars.
// Findings are appended to the tool result so the agent sees them without a second round trip.
// Auto-loaded from ~/.config/kilo/plugins/ (global, all projects).

import { readFile } from "node:fs/promises";

const GATES = `${process.env.HOME}/.config/harnesses/skills/polars/scripts/polars_gates.py`;
const CRUN = `${process.env.HOME}/.config/harnesses/scripts/crun`;
const EDIT_TOOLS = new Set(["edit", "write", "multiedit"]);
const MARKER = "[polars-gates]";

async function importsPolars(filePath) {
  if (!filePath.endsWith(".py") && !filePath.endsWith(".pyi")) return false;
  try {
    return (await readFile(filePath, "utf8")).includes("polars");
  } catch {
    return false;
  }
}

export const PolarsGatePlugin = async ({ $, directory }) => {
  return {
    "tool.execute.after": async (input, output) => {
      if (!EDIT_TOOLS.has(input.tool)) return;
      const filePath = input.args?.filePath ?? input.args?.path ?? "";
      if (typeof filePath !== "string" || !(await importsPolars(filePath))) return;
      try {
        const result = await $`${CRUN} python ${GATES} ${filePath}`.cwd(directory).quiet();
        const findings = String(result.stderr ?? "").trim();
        if (!findings) return;
        const existing = typeof output.output === "string" ? output.output : "";
        if (existing.includes(MARKER)) return;
        output.output = `${existing}\n\n${MARKER}\n${findings}`.trim();
      } catch {
        // gates must never break a session
      }
    },
  };
};
