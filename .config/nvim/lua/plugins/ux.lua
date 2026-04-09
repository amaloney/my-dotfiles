-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- User Experience
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   -- Automatically save your changes in Neovim.
   {
      "Pocco81/auto-save.nvim",
      opts = {},
   },

   -- Undotree visualizes the undo history and makes it easy to browse and switch between different undo branches
   {
      "mbbill/undotree",
      config = function()
         vim.api.nvim_set_keymap("n", "<leader>ut", ":UndotreeToggle<CR>", { noremap = true })
         vim.cmd([[set undodir=$HOME/.config/undo]])
         vim.cmd([[set undofile]])
      end,
   },

   -- Minimal and fast autopairs
   {
      "echasnovski/mini.pairs",
      opts = {},
   },

   -- WhichKey helps you remember your Neovim keymaps, by showing available keybindings in a popup as you type
   {
      "folke/which-key.nvim",
      dependencies = {
         "nvim-mini/mini.icons",
         "nvim-tree/nvim-web-devicons",
      },
      init = function()
         vim.o.timeout = true
         vim.o.timeoutlen = 300
      end,
      opts = {},
   },

   -- Toggle switch for turning formatting on/off
   {
      "folke/snacks.nvim",
      opts = function()
         vim.g.autoformat = true

         Snacks.toggle
            .new({
               id = "Format on Save",
               name = "Format on Save",
               get = function()
                  return vim.g.autoformat
               end,
               set = function(_)
                  vim.g.autoformat = not vim.g.autoformat
               end,
            })
            :map("<leader>uf")
      end,
   },

   -- A comfortable CSV/TSV editing plugin for Neovim
   {
      "hat0uma/csvview.nvim",
      opts = {
         parser = { comments = { "#", "//" } },
         keymaps = {
            -- Text objects for selecting fields
            textobject_field_inner = { "if", mode = { "o", "x" } },
            textobject_field_outer = { "af", mode = { "o", "x" } },
            -- Excel-like navigation:
            -- Use <Tab> and <S-Tab> to move horizontally between fields.
            -- Use <Enter> and <S-Enter> to move vertically between rows and place the cursor at the end of the field.
            -- Note: In terminals, you may need to enable CSI-u mode to use <S-Tab> and <S-Enter>.
            jump_next_field_end = { "<Tab>", mode = { "n", "v" } },
            jump_prev_field_end = { "<S-Tab>", mode = { "n", "v" } },
            jump_next_row = { "<Enter>", mode = { "n", "v" } },
            jump_prev_row = { "<S-Enter>", mode = { "n", "v" } },
         },
      },
      cmd = { "CsvViewEnable", "CsvViewDisable", "CsvViewToggle" },
   },

   -- Preview Markdown in your modern browser with synchronized scrolling and flexible configuration
   {
      "iamcco/markdown-preview.nvim",
      cmd = { "MarkdownPreviewToggle", "MarkdownPreview", "MarkdownPreviewStop" },
      build = "cd app && yarn install",
      init = function()
         vim.g.mkdp_filetypes = { "markdown" }
      end,
      ft = { "markdown" },
   },
}
