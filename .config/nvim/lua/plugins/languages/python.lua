-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Python Language Server Protocol
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
local python_exe = vim.fn.exepath("python")
return {
   {
      "neovim/nvim-lspconfig",
      opts = { enable = { "basedpyright" } },
   },
   {
      "WhoIsSethDaniel/mason-tool-installer.nvim",
      opts = { ensure_installed = { "basedpyright", "debugpy" } },
   },
   {
      "mfussenegger/nvim-dap",
      opts = function(_, opts)
         local adapters = {
            python = function(callback)
               if vim.fn.executable("debugpy") == 0 then
                  vim.notify("`debugpy` is not installed", vim.log.levels.ERROR)
                  return
               end
               callback({
                  args = { "-m", "debugpy.adapter" },
                  command = python_exe,
                  options = { source_filetype = "python" },
                  type = "executable",
               })
            end,
            debugpy_attach = {
               type = "server",
               host = "127.0.0.1",
               port = 5678,
            },
         }
         local configurations = {
            {
               name = "Launch: File",
               type = "python",
               request = "launch",
               program = "${file}",
               justMyCode = true,
               cwd = "${fileDirname}",
               console = "integratedTerminal",
            },
            {
               name = "Launch: File with Args",
               type = "python",
               request = "launch",
               program = "${file}",
               justMyCode = true,
               cwd = "${fileDirname}",
               console = "integratedTerminal",
               args = function()
                  local input = vim.fn.input("Arguments: ")
                  return vim.split(input, " ", { trimempty = true })
               end,
            },
            {
               name = "Attach: debugpy (5678)",
               type = "debugpy_attach",
               request = "attach",
               justMyCode = true,
            },
         }
         opts.python = { adapters = adapters, configurations = configurations }
      end,
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
            dap = { justMyCode = true, console = "integratedTerminal" },
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
