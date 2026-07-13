-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Rust Language Server Protocol
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {
   {
      "nvim-treesitter/nvim-treesitter",
      opts = { install = { "rust" } },
   },
   {
      "neovim/nvim-lspconfig",
      opts = { enable = { "rust_analyzer" } },
   },
   {
      "WhoIsSethDaniel/mason-tool-installer.nvim",
      opts = { ensure_installed = { "rust-analyzer" } },
   },
}