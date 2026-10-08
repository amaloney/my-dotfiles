// Logs user prompts, assistant outputs, and tool actions to .harness/chat-provenance/.
// Auto-loaded from ~/.config/kilo/plugins/ (global, all projects).
// Enforcement layer for the chat-provenance skill; failures are non-fatal.

const SCRIPTS = `${process.env.HOME}/.config/harnesses/skills/chat-provenance/scripts`;
const LOGGED_ASSISTANT = new Set();
const MAX_ACTION_CHARS = 600;

function env(model) {
  const base = { ...process.env, CHAT_PROVENANCE_CREATOR: "kilo" };
  if (model?.providerID && model?.modelID) {
    base.CHAT_PROVENANCE_MODEL = `${model.providerID}/${model.modelID}`;
  }
  return base;
}

async function log($, directory, flags, text, model) {
  if (!text || !text.trim()) return;
  try {
    await $`printf '%s' ${text} | python3 ${SCRIPTS}/log_entry.py ${flags}`
      .cwd(directory)
      .env(env(model))
      .quiet();
  } catch {
    // logging must never break a session
  }
}

function textOf(parts) {
  return (parts ?? [])
    .filter((p) => p.type === "text" && typeof p.text === "string")
    .map((p) => p.text)
    .join("\n");
}

function actionSummary(input, output) {
  const lines = [`tool: ${input.tool}`];
  if (output?.title) lines.push(`title: ${output.title}`);
  const args = JSON.stringify(input.args ?? {});
  lines.push(`args: ${args.slice(0, MAX_ACTION_CHARS)}`);
  return lines.join("\n");
}

export const ChatProvenancePlugin = async ({ client, $, directory }) => {
  return {
    // User prompts arrive through chat.message with full parts.
    "chat.message": async (input, output) => {
      await log(
        $,
        directory,
        ["--role", "user", "--agent", input.agent ?? "main", "--session", input.sessionID],
        textOf(output.parts),
        input.model,
      );
    },

    event: async ({ event }) => {
      // Assistant final text: message.updated with a completion timestamp.
      if (event.type === "message.updated") {
        const info = event.properties?.info;
        if (!info || info.role !== "assistant" || !info.time?.completed) return;
        if (LOGGED_ASSISTANT.has(info.id)) return;
        LOGGED_ASSISTANT.add(info.id);
        try {
          const result = await client.session.messages({ path: { id: info.sessionID } });
          const record = (result.data ?? []).find((m) => m.info?.id === info.id);
          await log(
            $,
            directory,
            [
              "--role",
              "assistant",
              "--agent",
              info.agent ?? "main",
              "--session",
              info.sessionID,
            ],
            textOf(record?.parts),
            info.model,
          );
        } catch {
          // client failures are non-fatal
        }
        return;
      }
      // Top-level sessions get a marker; subagent sessions are entries only.
      if (event.type === "session.created") {
        const info = event.properties?.info;
        if (!info || info.parentID) return;
        try {
          await $`python3 ${SCRIPTS}/session.py start --id ${info.id} --agent main`
            .cwd(directory)
            .env(env())
            .quiet();
        } catch {
          // non-fatal
        }
      }
    },

    // Work trace: one ## action entry per tool call (truncated args, no output bodies).
    "tool.execute.after": async (input, output) => {
      if (input.tool === "todoread") return;
      await log(
        $,
        directory,
        ["--role", "assistant", "--kind", "action", "--agent", "main", "--session", input.sessionID],
        actionSummary(input, output),
      );
    },
  };
};
