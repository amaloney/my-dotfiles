-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Source Control Plugins
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   -- Deep buffer integration for Git
   {
      "lewis6991/gitsigns.nvim",
      event = { "BufReadPre", "BufNewFile" },
      opts = {
         signs = {
            add = { text = "│" },
            change = { text = "│" },
            delete = { text = "_" },
            topdelete = { text = "‾" },
            changedelete = { text = "~" },
            untracked = { text = "┆" },
         },
         signcolumn = true,
         numhl = false,
         linehl = false,
         word_diff = false,
         watch_gitdir = { follow_files = true },
         attach_to_untracked = true,
         current_line_blame = false,
         current_line_blame_opts = {
            virt_text = true,
            virt_text_pos = "eol",
            delay = 1000,
            ignore_whitespace = false,
            virt_text_priority = 100,
         },
         current_line_blame_formatter = "<author>, <author_time:%Y-%m-%d> - <summary>",
         sign_priority = 6,
         update_debounce = 100,
         status_formatter = nil,
         max_file_length = 40000,
         preview_config = {
            border = "single",
            style = "minimal",
            relative = "cursor",
            row = 0,
            col = 1,
         },
      },
   },

   -- Single tab page interface for easily cycling through diffs for all modified files for any git rev
   {
      "sindrets/diffview.nvim",
      cmd = "DiffviewOpen",
      opts = function()
         local actions = require("diffview.actions")
         local view = {
            { "n", "co", actions.conflict_choose("ours"), { desc = "Choose ours" } },
            { "n", "ct", actions.conflict_choose("theirs"), { desc = "Choose theirs" } },
            { "n", "cn", actions.conflict_choose("base"), { desc = "Choose none" } },
            { "n", "cb", actions.conflict_choose("all"), { desc = "Choose both" } },
            {
               "n",
               "cf",
               function()
                  require("diffview").emit("focus_files")
               end,
               { desc = "Goto files" },
            },
         }
         return { keymaps = { view = view } }
      end,
   },
}
