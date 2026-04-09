-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Code Completion Plugins
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
return {

   -- Performant, batteries-included completion plugin for Neovim
   {
      "saghen/blink.cmp",
      event = "VeryLazy",
      version = "1.*",
      opts_extend = { "sources.default" },
      dependencies = {
         "nvim-mini/mini.snippets",
         "rafamadriz/friendly-snippets",
      },
      opts = {
         completion = {
            menu = { border = "rounded" },
            documentation = { auto_show = true, window = { border = "rounded" } },
         },
         sources = {
            default = { "lsp", "path", "snippets", "buffer" },
         },
         keymap = {
            ["<Tab>"] = { "select_and_accept", "fallback" },
         },
         appearance = { nerd_font_variant = "mono" },
         fuzzy = { sorts = { "exact", "score", "sort_text" }, implementation = "prefer_rust_with_warning" },
         signature = { enabled = true, window = { border = "rounded" } },
         snippets = { preset = "mini_snippets" },
      },
   },

   -- Manage and expand snippets
   {
      "nvim-mini/mini.snippets",
      version = "*",
      lazy = true,
      dependencies = { "rafamadriz/friendly-snippets" },
      opts = function(_, opts)
         local snippets, config_path = require("mini.snippets"), vim.fn.stdpath("config")
         opts.snippets = {
            snippets.gen_loader.from_file(config_path .. "/snippets/global.json"),
            snippets.gen_loader.from_lang(),
         }
      end,
   },

   -- Create annotations with one keybinding
   {
      "danymat/neogen",
      dependencies = { "nvim-mini/mini.snippets" },
      keys = {
         {
            "nf",
            function()
               require("neogen").generate()
            end,
            desc = "Generate docstring",
         },
      },
      opts = {
         snippet_engine = "mini",
         languages = {
            lua = { template = { annotation_convention = "emmylua" } },
            python = { template = { annotation_convention = "numpydoc" } },
         },
      },
   },
}
