-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- User Interface
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   -- A port of gruvbox community theme to lua with treesitter and semantic highlights support
   {
      "ellisonleao/gruvbox.nvim",
      priority = 1000,
      config = true,
      opts = {},
   },

   -- A blazing fast and easy to configure Neovim statusline written in Lua
   {
      "nvim-lualine/lualine.nvim",
      dependencies = { "nvim-tree/nvim-web-devicons" },
   },

   -- Highlight and search for todo comments
   {
      "folke/todo-comments.nvim",
      dependencies = { "nvim-lua/plenary.nvim" },
      opts = {
         signs = true,
         sign_priority = 8,
         keywords = {
            FIX = {
               icon = " ",
               color = "error",
               alt = { "FIXME", "BUG", "FIXIT", "ISSUE" },
            },
            TODO = { icon = " ", color = "info" },
            HACK = { icon = " ", color = "warning" },
            WARN = { icon = " ", color = "warning", alt = { "WARNING", "XXX" } },
            PERF = { icon = " ", alt = { "OPTIM", "PERFORMANCE", "OPTIMIZE" } },
            NOTE = { icon = " ", color = "hint", alt = { "INFO" } },
            TEST = { icon = "⏲ ", color = "test", alt = { "TESTING", "PASSED", "FAILED" } },
         },
         gui_style = {
            fg = "NONE",
            bg = "BOLD",
         },
         merge_keywords = true,
         highlight = {
            multiline = true,
            multiline_pattern = "^.",
            multiline_context = 10,
            before = "",
            keyword = "wide",
            after = "fg",
            pattern = [[.*<(KEYWORDS)\s*:]],
            comments_only = true,
            max_line_len = 400,
            exclude = {},
         },
         colors = {
            error = { "DiagnosticError", "ErrorMsg", "#DC2626" },
            warning = { "DiagnosticWarn", "WarningMsg", "#FBBF24" },
            info = { "DiagnosticInfo", "#2563EB" },
            hint = { "DiagnosticHint", "#10B981" },
            default = { "Identifier", "#7C3AED" },
            test = { "Identifier", "#FF00FF" },
         },
         search = {
            command = "rg",
            args = {
               "--color=never",
               "--no-heading",
               "--with-filename",
               "--line-number",
               "--column",
            },
            pattern = [[\b(KEYWORDS):]],
         },
      },
   },

   -- Causes all trailing whitespace characters to be highlighted
   {
      "ntpeters/vim-better-whitespace",
      config = function()
         vim.cmd([[let g:better_whitespace_enabled = 1]])
         vim.cmd([[let g:better_whitespace_ctermcolor = "darkred"]])
      end,
   },
}
