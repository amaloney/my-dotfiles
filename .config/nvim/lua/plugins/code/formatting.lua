-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Code Formatting Plugins
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   -- Lightweight yet powerful formatter plugin for Neovim
   {
      "stevearc/conform.nvim",
      cmd = { "ConformInfo" },
      event = { "BufWritePre" },
      dependencies = {
         {
            "WhoIsSethDaniel/mason-tool-installer.nvim",
            opts = {
               ensure_installed = {
                  "prettier",
                  "shfmt",
                  "stylua",
                  "ruff",
                  "taplo",
                  "ty",
               },
            },
         },
      },
      opts = {
         formatters_by_ft = {
            bash = { "shfmt" },
            css = { "prettier" },
            html = { "prettier" },
            javascript = { "prettier" },
            javascriptreact = { "prettier" },
            json = { "prettier" },
            jsonc = { "prettier_jsonc" },
            lua = { "stylua" },
            markdown = { "prettier" },
            ["markdown.jinja"] = { "prettier_markdown" },
            ["yaml.jinja"] = { "prettier_yaml" },
            python = { "ruff_fix", "ruff_format" },
            sh = { "shfmt" },
            svg = { "html" },
            toml = { "taplo" },
            typescript = { "prettier" },
            typescriptreact = { "prettier" },
            yaml = { "prettier" },
         },
         default_format_opts = {
            lsp_format = "fallback",
         },
         format_on_save = function(bufnr)
            if vim.g.autoformat then
               local disable_filetypes = {}
               local lsp_format_opt
               if disable_filetypes[vim.bo[bufnr].filetype] then
                  lsp_format_opt = "never"
               else
                  lsp_format_opt = "fallback"
               end
               return {
                  timeout_ms = 500,
                  lsp_format = lsp_format_opt,
               }
            else
               return
            end
         end,
         formatters = {
            shfmt = { prepend_args = { "-i", "4" } },
            prettier = {
               command = vim.fn.stdpath("data") .. "/mason/bin/prettier",
               prepend_args = { "--single-quote=false", "--print-width=120", "--prose-wrap=always" },
            },
            prettier_markdown = {
               command = vim.fn.stdpath("data") .. "/mason/bin/prettier",
               args = { "--parser", "markdown", "--prose-wrap", "always", "--print-width", "120" },
               stdin = true,
            },
            prettier_yaml = {
               command = vim.fn.stdpath("data") .. "/mason/bin/prettier",
               args = { "--parser", "yaml" },
               stdin = true,
            },
            prettier_jsonc = {
               command = vim.fn.stdpath("data") .. "/mason/bin/prettier",
               args = { "--parser", "json", "--trailing-comma", "none" },
               stdin = true,
            },
            taplo = {
               append_args = {
                  "--option",
                  "align_comments=false",
                  "--option",
                  "indent_string=    ",
                  "--option",
                  "column_width=120",
               },
            },
         },
      },
   },

   {
      "folke/snacks.nvim",
      opts = function()
         vim.g.autoformat = true

         ---@diagnostic disable-next-line: undefined-global
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
}
