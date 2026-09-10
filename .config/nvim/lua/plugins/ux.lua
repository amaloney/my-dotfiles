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
      keys = {
         { "<leader>uT", "<cmd>UndotreeToggle<CR>", desc = "Toggle Undotree" },
      },
      config = function()
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
      cmd = { "MarkdownPreviewToggle", "MarkdownPreview", "MarkdownPreviewStop", "JinjaMarkdownPreview" },
      build = "cd app && yarn install",
      init = function()
         vim.g.mkdp_filetypes = { "markdown", "markdown.jinja" }

         vim.api.nvim_create_user_command("JinjaMarkdownPreview", function()
            local script = vim.fn.stdpath("config") .. "/scripts/jinja-render.py"
            local src = vim.fn.expand("%:p")
            local tmp = vim.fn.tempname() .. ".md"

            local result = vim.fn.system({ "python3", script, src })
            if vim.v.shell_error ~= 0 then
               vim.notify("Jinja render failed:\n" .. result, vim.log.levels.ERROR)
               return
            end

            vim.fn.writefile(vim.split(result, "\n"), tmp)
            vim.cmd("edit " .. tmp)
            vim.cmd("MarkdownPreview")
         end, { desc = "Preview Jinja-templated markdown" })
      end,
      ft = { "markdown", "markdown.jinja" },
   },
}
