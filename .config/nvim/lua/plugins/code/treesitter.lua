-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Treesitter
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   -- Provides a way to use tree-sitter in Neovim and provides functionality based on it
   {
      "nvim-treesitter/nvim-treesitter",
      event = { "BufReadPost", "BufWritePost", "BufNewFile", "VeryLazy" },
      branch = "main",
      dependencies = {
         { "nvim-treesitter/nvim-treesitter-textobjects", branch = "main" },
         { "nvim-treesitter/nvim-treesitter-context", opts = { max_lines = 10 } },
         { "williamboman/mason.nvim", opts = { install = { "tree-sitter-cli" } } },
      },
      build = function()
         if vim.fn.exepath("tree-sitter") == "" then
            return
         end
         require("nvim-treesitter").update()
      end,
      opts_extend = { "install" },
      opts = {
         highlight = { enable = true },
         indent = { enable = true },
         ensure_installed = {
            "bash",
            "css",
            "diff",
            "html",
            "javascript",
            "json",
            "latex",
            "lua",
            "luadoc",
            "markdown",
            "markdown_inline",
            "norg",
            "python",
            "regex",
            "scss",
            "svelte",
            "toml",
            "tsx",
            "typescript",
            "typst",
            "vim",
            "vimdoc",
            "yaml",
         },
      },
   },
}
