-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- User Interface
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   {
      "ellisonleao/gruvbox.nvim",
      priority = 1000,
      config = true,
      opts = {
         contrast = "hard",
         palette_overrides = { dark0_hard = "#000000" },
         dim_inactive = true,
      },
   },

   {
      "nvim-lualine/lualine.nvim",
      dependencies = { "nvim-tree/nvim-web-devicons" },
      opts = function()
         local colors = {
            bg = "#303030", fg = "#808080", green = "#5faf00", blue = "#00afff",
            cyan = "#5f8787", yellow = "#d7af00", red = "#af0000", orange = "#d78700",
         }
         local theme = {
            normal = {
               a = { fg = colors.bg, bg = colors.green, gui = "bold" },
               b = { fg = colors.fg, bg = colors.bg },
               c = { fg = colors.fg, bg = colors.bg },
            },
            insert = { a = { fg = colors.bg, bg = colors.blue, gui = "bold" } },
            visual = { a = { fg = colors.bg, bg = colors.yellow, gui = "bold" } },
            replace = { a = { fg = colors.bg, bg = colors.red, gui = "bold" } },
            command = { a = { fg = colors.bg, bg = colors.orange, gui = "bold" } },
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
                  { "diff", symbols = { added = "+", modified = "!", removed = "✘" } },
               },
               lualine_c = { { "filename", path = 1, symbols = { modified = " ", readonly = "󰌾 " } } },
               lualine_x = {
                  { "diagnostics", symbols = { error = " ", warn = " ", info = " ", hint = " " } },
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

   {
      "folke/todo-comments.nvim",
      dependencies = { "nvim-lua/plenary.nvim" },
      opts = {},
   },

   {
      "ntpeters/vim-better-whitespace",
      config = function()
         vim.g.better_whitespace_enabled = 1
         vim.g.better_whitespace_ctermcolor = "darkred"
      end,
   },
}
