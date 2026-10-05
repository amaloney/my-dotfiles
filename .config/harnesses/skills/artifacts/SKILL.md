---
name: artifacts
description: Generated output handling - images, diagrams, encoded data
invocation: auto
---

# Artifacts

Handoff: `next: done`.

- Never paste base64, data URIs, or encoded binary into chat. Write generated images/diagrams to a file; respond with
  the path only.
- Mermaid diagrams stay as text source. Never rasterize to SVG/PNG unless explicitly asked; then write to a file.

## Mermaid Style

- No dark `rect` fills or custom font colors — default theme text is dark.
- Light tints only, e.g. `rect rgb(240, 248, 255)`. Verify contrast before using any color.
