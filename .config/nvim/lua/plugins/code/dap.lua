local function update_sign(sign_name, new_text, new_texthl)
   local existing = vim.fn.sign_getdefined(sign_name)[1] or {}
   vim.fn.sign_define(sign_name, {
      text = new_text or existing.text,
      texthl = new_texthl or existing.texthl,
      linehl = existing.linehl,
      numhl = existing.numhl,
   })
end

local last_dap_config = nil

return {
   {
      "mfussenegger/nvim-dap",
      dependencies = {
         "igorlfs/nvim-dap-view",
         "nvim-neotest/nvim-nio",
      },
      keys = {
         { "<F2>", function() require("dap").continue() end, desc = "Debug: Start/Continue" },
         { "<F3>", function() require("dap").step_over() end, desc = "Debug: Step Over" },
         { "<F4>", function() require("dap").step_into() end, desc = "Debug: Step Into" },
         { "<F5>", function() require("dap").step_out() end, desc = "Debug: Step Out" },
         {
            "<F6>",
            function()
               local dap = require("dap")
               if dap.session() then
                  dap.restart()
               elseif last_dap_config ~= nil then
                  dap.run(last_dap_config)
               else
                  dap.continue()
               end
            end,
            desc = "Debug: Restart/Rerun",
         },
         { "<leader>b", function() require("dap").toggle_breakpoint() end, desc = "Debug: Toggle Breakpoint" },
         {
            "<leader>B",
            function()
               vim.ui.input(
                  { prompt = "Breakpoint condition" },
                  function(result) require("dap").set_breakpoint(result) end
               )
            end,
            desc = "Debug: Set Breakpoint Condition",
         },
         { "<leader>i", function() require("dap-view").hover() end, desc = "Debug: Eval var under cursor" },
      },
      config = function(_, opts)
         local dap = require("dap")

         for language_name, language_opts in pairs(opts) do
            for adapter_name, adapter_opts in pairs(language_opts.adapters or {}) do
               dap.adapters[adapter_name] = adapter_opts
            end
            dap.configurations[language_name] = language_opts.configurations
         end

         dap.listeners.on_config["store-last-config"] = function(config)
            last_dap_config = vim.deepcopy(config)
            return config
         end

         update_sign("DapBreakpoint", " ", "DiagnosticSignError")
         update_sign("DapBreakpointCondition", " ", "DiagnosticSignError")
         update_sign("DapBreakpointRejected", " ", "DiagnosticSignError")
         update_sign("DapStopped", "")
      end,
   },
   {
      "igorlfs/nvim-dap-view",
      lazy = true,
      opts = {
         winbar = { default_section = "repl" },
         windows = { terminal = { position = "right" } },
         virtual_text = { enabled = true },
      },
      config = function(_, opts)
         local dap = require("dap")
         local dapview = require("dap-view")
         dapview.setup(opts)

         dap.listeners.after.event_initialized.dapui_config = dapview.open
         dap.listeners.before.attach.dapui_config = dapview.open
         dap.listeners.before.launch.dapui_config = dapview.open
         dap.listeners.before.event_terminated.dapui_config = function() vim.notify("DAP Terminated") end
         dap.listeners.before.event_exited.dapui_config = function() vim.notify("DAP Exited") end

         vim.keymap.set("n", "<esc>", function()
            dap.disconnect()
            dapview.close(true)
         end, { desc = "Debug: Exit" })
      end,
   },
}
