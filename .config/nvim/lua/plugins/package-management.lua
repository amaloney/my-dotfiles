-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Package Management for Neovim
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   -- Portable package manager for Neovim that runs everywhere Neovim runs
   {
      "mason-org/mason.nvim",
      opts = {},
   },

   -- Provides lockfile functionality to mason.nvim
   {
      "zapling/mason-lock.nvim",
      dependencies = "mason-org/mason.nvim",
      opts = {},
      event = "VeryLazy",
      cmd = "MasonLockRestore",
   },
}
