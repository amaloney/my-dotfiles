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
               formatters = {
                  "prettierd",
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
            css = { "prettierd" },
            html = { "prettierd" },
            javascript = { "prettierd" },
            javascriptreact = { "prettierd" },
            json = { "prettierd" },
            jsonc = { "prettierd" },
            lua = { "stylua" },
            markdown = { "prettierd" },
            python = { "ruff_fix", "ruff_format" },
            sh = { "shfmt" },
            toml = { "taplo" },
            typescript = { "prettierd" },
            typescriptreact = { "prettierd" },
            yaml = { "prettierd" },
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
            prettierd = { prepend_args = { "--single-quote=false", "--print-width=120" }, append_args = {} },
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
