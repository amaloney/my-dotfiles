-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- LLM plugins
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
local current_cli = vim.env.AI_CLI or "kilo"

return {
   {
      "folke/sidekick.nvim",
      lazy = true,
      opts = {
         cli = {
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
            snacks_win_opts = {
               wo = {
                  winhighlight = "Normal:TerminalNormal,NormalNC:TerminalNormalNC",
               },
               -- keys = {
               --    ["<C-h>"] = { "<C-\\><C-n><C-w>h", mode = "t", expr = false },
               -- },
            },
         },
      },
      config = true,
      keys = {
         { "<leader>a", nil, desc = "AI/Claude Code" },
         { "<leader>ac", "<CMD>ClaudeCode<CR>", desc = "Toggle Claude" },
         { "<leader>af", "<CMD>ClaudeCodeFocus<CR>", desc = "Focus Claude" },
         { "<leader>ar", "<CMD>ClaudeCode --resume<CR>", desc = "Resume Claude" },
         { "<leader>aC", "<CMD>ClaudeCode --continue<CR>", desc = "Continue Claude" },
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
