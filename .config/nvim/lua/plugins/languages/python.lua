-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Python Language Server Protocol
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
local last_pid
local python_exe = vim.fn.exepath("python")
return {
   {
      "neovim/nvim-lspconfig",
      opts = { enable = { "basedpyright" } },
   },
   {
      "WhoIsSethDaniel/mason-tool-installer.nvim",
      opts = { ensure_installed = { "basedpyright" } },
   },
   {
      "nvim-neotest/neotest",
      dependencies = {
         "nvim-lua/plenary.nvim",
         "nvim-neotest/nvim-nio",
         "nvim-treesitter/nvim-treesitter",
         "nvim-neotest/neotest-python",
      },
      opts = {
         ["neotest-python"] = {
            dap = { justMyCode = false, console = "integratedTerminal" },
            python = python_exe,
            -- pytest_discover_instances = true,
            args = function(_, position)
               local Path = require("plenary.path")
               local elems = vim.split(position.path, Path.path.sep)
               return (vim.tbl_contains(elems, "ui") and { "--ui" }) or {}
            end,
            is_test_file = function(file_path)
               local Path = require("plenary.path")
               if not vim.endswith(file_path, ".py") then
                  return false
               end
               local elems = vim.split(file_path, Path.path.sep)
               local file_name = elems[#elems]
               return vim.startswith(file_name, "test") and not vim.tbl_contains(elems, "node_modules")
            end,
         },
      },
   },
}
