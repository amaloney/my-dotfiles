-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Lua Language Server Protocol
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {
   {
      "neovim/nvim-lspconfig",
      opts = { enable = { "lua_ls" } },
   },
   {
      "WhoIsSethDaniel/mason-tool-installer.nvim",
      opts = { ensure_installed = { "lua-language-server" } },
   },
   {
      "folke/lazydev.nvim",
      ft = "lua",
      opts = {
         library = {
            { path = "${3rd}/luv/library", words = { "vim%.uv" } },
            { path = "luassert-types/library", words = { "assert" } },
            { path = "busted-types/library", words = { "describe" } },
         },
      },
   },
   { "LuaCATS/luassert", name = "luassert-types", lazy = true },
   { "LuaCATS/busted", name = "busted-types", lazy = true },
}
