-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- User Interface
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   -- A port of gruvbox community theme to lua with treesitter and semantic highlights support
   {
      "ellisonleao/gruvbox.nvim",
      priority = 1000,
      config = true,
      opts = {
         contrast = "hard",
         palette_overrides = {
            dark0_hard = "#000000",
         },
         dim_inactive = true,
      },
   },

   -- A blazing fast and easy to configure Neovim statusline written in Lua
   {
      "nvim-lualine/lualine.nvim",
      dependencies = { "nvim-tree/nvim-web-devicons" },
      opts = function()
         local colors = {
            bg = "#303030",
            fg = "#808080",
            green = "#5faf00",
            blue = "#00afff",
            cyan = "#5f8787",
            yellow = "#d7af00",
            red = "#af0000",
            orange = "#d78700",
         }

         local theme = {
            normal = {
               a = { fg = colors.bg, bg = colors.green, gui = "bold" },
               b = { fg = colors.fg, bg = colors.bg },
               c = { fg = colors.fg, bg = colors.bg },
            },
            insert = {
               a = { fg = colors.bg, bg = colors.blue, gui = "bold" },
            },
            visual = {
               a = { fg = colors.bg, bg = colors.yellow, gui = "bold" },
            },
            replace = {
               a = { fg = colors.bg, bg = colors.red, gui = "bold" },
            },
            command = {
               a = { fg = colors.bg, bg = colors.orange, gui = "bold" },
            },
            inactive = {
               a = { fg = colors.fg, bg = colors.bg },
               b = { fg = colors.fg, bg = colors.bg },
               c = { fg = colors.fg, bg = colors.bg },
            },
         }

         return {
            options = {
               theme = theme,
               component_separators = { left = "╱", right = "╱" },
               section_separators = { left = "", right = "" },
               globalstatus = true,
            },
            sections = {
               lualine_a = { "mode" },
               lualine_b = {
                  { "branch", icon = "" },
                  {
                     "diff",
                     symbols = { added = "+", modified = "!", removed = "✘" },
                  },
               },
               lualine_c = {
                  { "filename", path = 1, symbols = { modified = " ", readonly = "󰌾 " } },
               },
               lualine_x = {
                  {
                     "diagnostics",
                     sources = { "nvim_diagnostic" },
                     symbols = { error = " ", warn = " ", info = " ", hint = " " },
                  },
                  "filetype",
               },
               lualine_y = { "progress" },
               lualine_z = { "location" },
            },
            inactive_sections = {
               lualine_a = {},
               lualine_b = {},
               lualine_c = { { "filename", path = 1 } },
               lualine_x = { "location" },
               lualine_y = {},
               lualine_z = {},
            },
         }
      end,
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
