-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Language Server Protocol
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
local on_attach = function(_, bufnr)
   local map = function(mode, keys, func, desc)
      vim.keymap.set(mode, keys, func, { buffer = bufnr, desc = "LSP: " .. desc })
   end

   map("n", "<leader>cr", vim.lsp.buf.rename, "Rename Variable")
   map({ "n", "x" }, "<leader>ca", vim.lsp.buf.code_action, "Code Action")
   map("n", "K", vim.lsp.buf.hover, "Hover Documentation")
   map("i", "<C-h>", vim.lsp.buf.signature_help, "Signature Help")
end

return {
   {
      "neovim/nvim-lspconfig",
      event = { "BufReadPost", "BufWritePost", "BufNewFile" },
      dependencies = { { "j-hui/fidget.nvim", opts = {} } },
      opts_extend = { "enable", "attach" },
      config = function(_, opts)
         local servers = vim.list.unique(vim.list_extend(opts.attach or {}, opts.enable or {}))
         for _, server in pairs(servers) do
            vim.lsp.config(server, { on_attach = on_attach })
         end
         -- https://www.reddit.com/r/neovim/comments/1l7pz1l
         vim.schedule(function()
            vim.lsp.enable(opts.enable or {})
         end)
      end,
   },

   -- Otter.nvim provides lsp features, including code completion, for code embedded in other documents
   {
      "jmbuhr/otter.nvim",
      keys = {
         {
            "<leader>co",
            function()
               require("otter").activate()
            end,
            desc = "Activate otter",
         },
      },
      dependencies = { "nvim-treesitter/nvim-treesitter" },
      opts = {},
   },
}
