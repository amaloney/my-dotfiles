-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- User Experience
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   { "Pocco81/auto-save.nvim", opts = {} },

   {
      "mbbill/undotree",
      keys = { { "<leader>uT", "<cmd>UndotreeToggle<CR>", desc = "Toggle Undotree" } },
      config = function()
         vim.o.undodir = vim.fn.expand("$HOME/.config/undo")
         vim.o.undofile = true
      end,
   },

   { "echasnovski/mini.pairs", opts = {} },

   {
      "folke/which-key.nvim",
      dependencies = { "nvim-mini/mini.icons", "nvim-tree/nvim-web-devicons" },
      init = function()
         vim.o.timeout = true
         vim.o.timeoutlen = 300
      end,
      opts = {},
   },

   {
      "hat0uma/csvview.nvim",
      opts = {
         parser = { comments = { "#", "//" } },
         keymaps = {
            textobject_field_inner = { "if", mode = { "o", "x" } },
            textobject_field_outer = { "af", mode = { "o", "x" } },
            jump_next_field_end = { "<Tab>", mode = { "n", "v" } },
            jump_prev_field_end = { "<S-Tab>", mode = { "n", "v" } },
            jump_next_row = { "<Enter>", mode = { "n", "v" } },
            jump_prev_row = { "<S-Enter>", mode = { "n", "v" } },
         },
      },
      cmd = { "CsvViewEnable", "CsvViewDisable", "CsvViewToggle" },
   },

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
