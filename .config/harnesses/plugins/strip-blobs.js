// Strips base64 blobs and data URIs from tool outputs and message history
// so encoded binary never floods the context window.
// Auto-loaded from ~/.config/kilo/plugins/ at startup (global, all projects).

// Long unbroken runs of base64-charset characters. 400+ chars with no
// whitespace is near-certainly encoded binary, not prose or code.
const BLOB_RUN = /[A-Za-z0-9+/]{400,}={0,2}/g;
const DATA_URI = /data:[\w/+.-]*;base64,[A-Za-z0-9+/=\r\n]+/g;

function scrub(text) {
  if (typeof text !== "string") return text;
  return text
    .replace(DATA_URI, (m) => `[data-uri elided, ${m.length} chars]`)
    .replace(BLOB_RUN, (m) => `[base64 blob elided, ${m.length} chars]`);
}

export const StripBlobsPlugin = async () => {
  return {
    // Sanitize tool results before they enter the transcript
    "tool.execute.after": async (_input, output) => {
      if (typeof output.output === "string") {
        output.output = scrub(output.output);
      }
    },
    // Sanitize full message history before each LLM call, so blobs
    // emitted as assistant text are also stripped on subsequent turns.
    // Ignored harmlessly if the runtime does not support this hook.
    "experimental.chat.messages.transform": async (_input, output) => {
      for (const message of output.messages ?? []) {
        for (const part of message.parts ?? []) {
          if (part.type === "text" && typeof part.text === "string") {
            part.text = scrub(part.text);
          }
        }
      }
    },
  };
};
