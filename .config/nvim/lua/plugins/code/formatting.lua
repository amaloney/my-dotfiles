-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Code Formatting Plugins
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
local mason_bin = vim.fn.stdpath("data") .. "/mason/bin/"

return {
   {
      "stevearc/conform.nvim",
      cmd = { "ConformInfo" },
      event = { "BufWritePre" },
      dependencies = {
         { "WhoIsSethDaniel/mason-tool-installer.nvim", opts = { ensure_installed = { "prettier", "shfmt", "stylua", "ruff", "taplo", "ty" } } },
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
         default_format_opts = { lsp_format = "fallback" },
         format_on_save = function()
            if vim.g.autoformat then
               return { timeout_ms = 500, lsp_format = "fallback" }
            end
         end,
         formatters = {
            shfmt = { prepend_args = { "-i", "4" } },
            prettier = {
               command = mason_bin .. "prettier",
               prepend_args = { "--single-quote=false", "--print-width=120", "--prose-wrap=always" },
            },
            prettier_markdown = {
               command = mason_bin .. "prettier",
               args = { "--parser", "markdown", "--prose-wrap", "always", "--print-width", "120" },
               stdin = true,
            },
            prettier_yaml = {
               command = mason_bin .. "prettier",
               args = { "--parser", "yaml" },
               stdin = true,
            },
            prettier_jsonc = {
               command = mason_bin .. "prettier",
               args = { "--parser", "json", "--trailing-comma", "none" },
               stdin = true,
            },
            taplo = {
               append_args = { "--option", "align_comments=false", "--option", "indent_string=    ", "--option", "column_width=120" },
            },
         },
      },
   },

   {
      "folke/snacks.nvim",
      opts = function()
         vim.g.autoformat = true
         ---@diagnostic disable-next-line: undefined-global
         Snacks.toggle.new({
            id = "Format on Save",
            name = "Format on Save",
            get = function() return vim.g.autoformat end,
            set = function(_) vim.g.autoformat = not vim.g.autoformat end,
         }):map("<leader>uf")
      end,
   },
}
