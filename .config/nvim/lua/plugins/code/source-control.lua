-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Source Control Plugins
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   {
      "lewis6991/gitsigns.nvim",
      event = { "BufReadPre", "BufNewFile" },
      opts = {
         current_line_blame_formatter = "<author>, <author_time:%Y-%m-%d> - <summary>",
      },
   },

   {
      "sindrets/diffview.nvim",
      cmd = "DiffviewOpen",
      opts = function()
         local actions = require("diffview.actions")
         return {
            keymaps = {
               view = {
                  { "n", "co", actions.conflict_choose("ours"), { desc = "Choose ours" } },
                  { "n", "ct", actions.conflict_choose("theirs"), { desc = "Choose theirs" } },
                  { "n", "cn", actions.conflict_choose("base"), { desc = "Choose none" } },
                  { "n", "cb", actions.conflict_choose("all"), { desc = "Choose both" } },
                  { "n", "cf", function() require("diffview").emit("focus_files") end, { desc = "Goto files" } },
               },
            },
         }
      end,
   },
}
