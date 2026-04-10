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
         default_format_opts = {
            lsp_format = "fallback",
         },
         format_on_save = { timeout_ms = 500 },
         formatters = {
            shfmt = { prepend_args = { "-i", "4" } },
            prettierd = { prepend_args = { "--single-quote=false", "--print-width=120" } },
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
}
