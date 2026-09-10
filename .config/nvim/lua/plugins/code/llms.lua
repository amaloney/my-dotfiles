-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- LLM plugins
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
local current_cli = vim.env.AI_CLI or "kilo"

-- ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
-- Claude Code terminal layouts (snacks.nvim window options)
-- ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
-- A size of 0 means "fill the parent" in snacks, so a vertical split is full height and a
-- horizontal split is full width.
local claude_layouts = {
   vertical = { position = "right", width = 0.35, height = 0 },
   horizontal = { position = "bottom", width = 0, height = 0.4 },
}

-- Layout used the last time the Claude terminal was opened.
local claude_layout = "vertical"

local function claude_win_opts(layout)
   return vim.tbl_deep_extend("force", claude_layouts[layout] or claude_layouts.vertical, {
      wo = {
         winhighlight = "Normal:TerminalNormal,NormalNC:TerminalNormalNC",
      },
      -- keys = {
      --    ["<C-h>"] = { "<C-\\><C-n><C-w>h", mode = "t", expr = false },
      -- },
   })
end

--- Toggle the Claude Code terminal using the given layout.
---
--- If a Claude terminal already exists in a different layout it is closed and relaunched
--- with `--continue` so the conversation carries over into the new split.
---@param layout? "vertical"|"horizontal" Defaults to the last used layout.
---@param cmd_args? string Extra CLI arguments, e.g. "--resume".
local function claude_toggle(layout, cmd_args)
   layout = layout or claude_layout
   local terminal = require("claudecode.terminal")
   if layout ~= claude_layout and terminal.get_active_terminal_bufnr() then
      terminal.close()
      cmd_args = cmd_args or "--continue"
   end
   claude_layout = layout
   terminal.toggle({ snacks_win_opts = claude_win_opts(layout) }, cmd_args)
end

return {
   {
      "folke/sidekick.nvim",
      lazy = true,
      opts = {
         cli = {
            win = {
               layout = "bottom",
            },
            tools = {
               kilo = { cmd = { "sh", "-c", "kilo auth login && kilo" } },
               claude = { cmd = { "claude" } },
            },
         },
      },
      keys = {
         {
            "<leader>ks",
            function()
               vim.ui.select({ "kilo", "claude" }, {
                  prompt = "Select AI CLI",
                  format_item = function(item)
                     return item == current_cli and item .. " (current)" or item
                  end,
               }, function(choice)
                  if choice then current_cli = choice end
               end)
            end,
            desc = "Select AI CLI",
         },
         {
            "<leader>kk",
            function() require("sidekick.cli").toggle({ name = current_cli, focus = true }) end,
            desc = "Toggle Kilo CLI",
         },
         {
            "<leader>kd",
            function() require("sidekick.cli").close() end,
            desc = "Detach Kilo CLI",
         },
         {
            "<leader>kt",
            function() require("sidekick.cli").send({ name = current_cli, msg = "{this}" }) end,
            mode = { "x", "n" },
            desc = "Send This to Kilo",
         },
         {
            "<leader>kf",
            function() require("sidekick.cli").send({ name = current_cli, msg = "{file}" }) end,
            desc = "Send File to Kilo",
         },
         {
            "<leader>kv",
            function() require("sidekick.cli").send({ name = current_cli, msg = "{selection}" }) end,
            mode = { "x" },
            desc = "Send Selection to Kilo",
         },
         {
            "<leader>kp",
            function() require("sidekick.cli").prompt({ name = current_cli }) end,
            mode = { "n", "x" },
            desc = "Kilo Prompt",
         },
      },
   },
   {
      "coder/claudecode.nvim",
      dependencies = { "folke/snacks.nvim" },
      opts = {
         terminal_CMD = "~/.local/bin/claude",
         terminal = {
            -- Default layout for the plain `:ClaudeCode` command.
            snacks_win_opts = claude_win_opts(claude_layout),
         },
      },
      config = true,
      keys = {
         { "<leader>a", nil, desc = "AI/Claude Code" },
         { "<leader>ac", function() claude_toggle() end, desc = "Toggle Claude" },
         { "<leader>av", function() claude_toggle("vertical") end, desc = "Toggle Claude (vertical split)" },
         { "<leader>ah", function() claude_toggle("horizontal") end, desc = "Toggle Claude (horizontal split)" },
         { "<leader>af", "<CMD>ClaudeCodeFocus<CR>", desc = "Focus Claude" },
         { "<leader>ar", function() claude_toggle(nil, "--resume") end, desc = "Resume Claude" },
         { "<leader>aC", function() claude_toggle(nil, "--continue") end, desc = "Continue Claude" },
         { "<leader>am", "<CMD>ClaudeCodeSelectModel<CR>", desc = "Select Claude model" },
         { "<leader>ab", "<CMD>ClaudeCodeAdd %<CR>", desc = "Add current buffer" },
         { "<leader>as", "<CMD>ClaudeCodeSend<CR>", mode = "v", desc = "Send to Claude" },
         {
            "<leader>as",
            "<CMD>ClaudeCodeTreeAdd<CR>",
            desc = "Add file",
            ft = { "NvimTree", "neo-tree", "oil", "minifiles", "netrw" },
         },
         -- Diff management
         { "<leader>aa", "<CMD>ClaudeCodeDiffAccept<CR>", desc = "Accept diff" },
         { "<leader>ad", "<CMD>ClaudeCodeDiffDeny<CR>", desc = "Deny diff" },
      },
   },
}
