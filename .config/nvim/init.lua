vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

-- Prepend Mason's bin to PATH early so LSP servers are found even when pixi/conda envs are active
local mason_bin = vim.fn.stdpath("data") .. "/mason/bin"
if vim.fn.isdirectory(mason_bin) == 1 then
   vim.env.PATH = mason_bin .. ":" .. vim.env.PATH
end

-- Python provider
vim.g.python3_host_prog = vim.fn.exepath(vim.fn.has("win32") == 1 and "python" or "python3")

-- File watching for agent-modified files
vim.opt.autoread = true
vim.opt.updatetime = 100

vim.api.nvim_create_autocmd({ "FocusGained", "BufEnter", "CursorHold", "CursorHoldI", "VimResume" }, {
   callback = function()
      if vim.fn.mode() ~= "c" then
         vim.cmd("checktime")
      end
   end,
})

local watch_timer = vim.uv.new_timer()
watch_timer:start(500, 500, vim.schedule_wrap(function()
   if vim.fn.mode() ~= "c" and vim.api.nvim_get_mode().mode ~= "c" then
      pcall(vim.cmd, "checktime")
   end
end))

local last_reload_notify = {}
vim.api.nvim_create_autocmd("FileChangedShellPost", {
   callback = function(args)
      local filename = vim.fn.fnamemodify(args.file, ":t")
      local now = vim.uv.now()
      if last_reload_notify[filename] and (now - last_reload_notify[filename]) < 3000 then
         return
      end
      last_reload_notify[filename] = now
      local snacks_ok, snacks = pcall(require, "snacks")
      if snacks_ok and snacks.notify then
         snacks.notify.info("Agent updated: " .. filename, { title = "File Reloaded", icon = "󰚰", timeout = 3000 })
      else
         vim.notify("Agent updated: " .. filename, vim.log.levels.INFO)
      end
   end,
})

-- Filetypes
vim.filetype.add({
   pattern = {
      [".*%.md%.j2"] = "markdown.jinja",
      [".*%.yaml%.j2"] = "yaml.jinja",
      [".*%.yml%.j2"] = "yaml.jinja",
   },
})

-- Spelling
vim.opt.spell = true
vim.opt.spelllang = "en_us"
vim.api.nvim_create_autocmd("TermOpen", { callback = function() vim.opt_local.spell = false end })

-- Search
vim.opt.hlsearch = true
vim.opt.ignorecase = true
vim.opt.incsearch = true
vim.opt.smartcase = true
vim.opt.infercase = true
vim.keymap.set("n", "<leader>h", "<CMD>nohlsearch<CR>")

-- UI
vim.opt.cursorline = true
vim.opt.ruler = true
vim.opt.number = true
vim.opt.numberwidth = 4
vim.opt.signcolumn = "yes"
vim.opt.colorcolumn = { 121 }
vim.opt.showmatch = true
vim.opt.showtabline = 2

-- Editing
vim.opt.autoindent = true
vim.opt.breakindent = true
vim.opt.expandtab = true
vim.opt.linebreak = true
vim.opt.shiftwidth = 4
vim.opt.smarttab = true
vim.opt.smartindent = true
vim.opt.softtabstop = 0
vim.opt.tabstop = 4
vim.opt.textwidth = 120
vim.opt.swapfile = false
vim.opt.whichwrap:append("<,>,h,l,[,]")

-- Keymaps
vim.keymap.set("n", "<C-h>", "<CMD>tabp<CR>")
vim.keymap.set("n", "<C-l>", "<CMD>tabn<CR>")
vim.keymap.set("n", "<C-n>", "<CMD>tabnew<CR>")
vim.keymap.set("n", "<leader>R", "<CMD>e<CR>")
vim.keymap.set("n", "<C-t><C-h>", "<CMD>botright split | terminal<CR>", { desc = "Terminal horizontal split" })
vim.keymap.set("n", "<C-t><C-v>", "<CMD>botright vsplit | terminal<CR>", { desc = "Terminal vertical split" })
vim.keymap.set("n", "<C-t><C-t>", "<CMD>terminal<CR>", { desc = "Terminal in current window" })
vim.keymap.set("t", "<C-d>", "<C-\\><C-n>:bd!<CR>", { desc = "Close terminal" })
vim.keymap.set("t", "<Esc><Esc>", "<C-\\><C-n>", { desc = "Exit terminal mode" })

require("config.lazy")

-- Colorscheme
vim.opt.background = "dark"
vim.cmd.colorscheme("gruvbox")
vim.api.nvim_set_hl(0, "TerminalNormal", { bg = "#000000" })
vim.api.nvim_set_hl(0, "TerminalNormalNC", { bg = "#1d2021" })
vim.api.nvim_set_hl(0, "BlinkCmpSignatureHelpActiveParameter", { link = "CursorLine" })
vim.opt.foldenable = false
