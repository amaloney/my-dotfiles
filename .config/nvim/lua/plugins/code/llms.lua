-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- LLM plugins
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {
   --
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
