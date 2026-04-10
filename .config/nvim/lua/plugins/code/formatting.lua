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
               },
            },
         },
      },
      keys = {
         {
            "<leader>F",
            function()
               require("conform").format({ async = true })
            end,
            desc = "Format Code",
            mode = { "n", "x" },
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
         format_on_save = function()
            if vim.g.autoformat then
               return {
                  timeout_ms = 5000,
                  lsp_format = "fallback",
               }
            else
               return
            end
         end,
      },
      formatters = {
         shfmt = { prepend_args = { "-i", "4" } },
         prettierd = { prepend_args = { "--single-quote=false" } },
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
}
