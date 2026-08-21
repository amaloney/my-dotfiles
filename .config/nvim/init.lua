-- Make sure to setup `mapleader` and `maplocalleader` before
-- loading lazy.nvim so that mappings are correct.
-- This is also a good place to setup other settings (vim.opt)
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

-- Python provider (cross-platform)
if vim.fn.has("win32") == 1 then
   vim.g.python3_host_prog = vim.fn.exepath("python")
else
   vim.g.python3_host_prog = vim.fn.exepath("python3")
end

-- Faster buffer refresh for agent-modified files
vim.opt.autoread = true
vim.opt.updatetime = 100

-- More aggressive file change detection
vim.api.nvim_create_autocmd({ "FocusGained", "BufEnter", "CursorHold", "CursorHoldI", "VimResume" }, {
   pattern = "*",
   callback = function()
      if vim.fn.mode() ~= "c" then
         vim.cmd("checktime")
      end
   end,
})

-- Watch for file changes using a timer (catches agent modifications faster)
local watch_timer = vim.uv.new_timer()
watch_timer:start(
   500,
   500,
   vim.schedule_wrap(function()
      if vim.fn.mode() ~= "c" and vim.api.nvim_get_mode().mode ~= "c" then
         pcall(vim.cmd, "checktime")
      end
   end)
)

-- Notify when files are reloaded (uses Snacks if available) with debounce
local last_reload_notify = {}
vim.api.nvim_create_autocmd("FileChangedShellPost", {
   pattern = "*",
   callback = function(args)
      local filename = vim.fn.fnamemodify(args.file, ":t")
      local now = vim.uv.now()
      if last_reload_notify[filename] and (now - last_reload_notify[filename]) < 3000 then
         return
      end
      last_reload_notify[filename] = now
      local snacks_ok, snacks = pcall(require, "snacks")
      if snacks_ok and snacks.notify then
         snacks.notify.info("Agent updated: " .. filename, {
            title = "File Reloaded",
            icon = "󰚰",
            timeout = 3000,
         })
      else
         vim.notify("Agent updated: " .. filename, vim.log.levels.INFO)
      end
   end,
})

-- Spelling
vim.opt.spell = true -- enable spell checking
vim.opt.spelllang = "en_us" -- using English

-- Searches
vim.opt.hlsearch = true -- highlight all matches
vim.opt.ignorecase = true -- ignore the case of letters
vim.opt.incsearch = true -- show the pattern matches while typing
vim.opt.smartcase = true -- ignore case when pattern contains lowercase letters only
vim.api.nvim_set_keymap("n", "<leader>h", "<CMD>nohlsearch<CR>", { noremap = true })

-- Keyword completions in insert-mode
vim.opt.infercase = true -- adjust the case of a match depending on the typed text

-- Brackets
vim.opt.showmatch = true -- show matching brackets

-- UI
vim.opt.cursorline = true -- highlight the current line of the cursor
vim.opt.ruler = true -- show the line and column number in the bottom right corner
vim.opt.number = true -- show the line number
vim.opt.numberwidth = 4 -- minimum number of columns to show for line numbers
vim.opt.signcolumn = "yes" -- always show the sign column
vim.opt.colorcolumn = { 121 } -- comma separated list of of columns to highlight

-- UX
vim.opt.autoindent = true -- automatically add indents
vim.opt.breakindent = true -- indents at line breaks
vim.opt.expandtab = true -- make the tab key insert spaces instead of tabs
vim.opt.linebreak = true -- breaks lines at textwidth
vim.opt.shiftwidth = 4 -- width of an indent measured in spaces
vim.opt.smarttab = true -- indent by `shiftwidth` amount of spaces
vim.opt.smartindent = true -- automatically add indents
vim.opt.softtabstop = 0 -- do not simulate tab stops
vim.opt.tabstop = 4 -- width of a tab character measured in spaces
vim.opt.textwidth = 120 -- width of a single line
vim.opt.swapfile = false -- disable swap files
vim.opt.whichwrap:append("<,>,h,l,[,]") -- handle moving the cursor between lines more naturally
vim.api.nvim_set_keymap("n", "<C-h>", "<CMD>tabp<CR>", { noremap = true }) -- move the tab focus to the left
vim.api.nvim_set_keymap("n", "<C-l>", "<CMD>tabn<CR>", { noremap = true }) -- move the tab focus to the right
vim.api.nvim_set_keymap("n", "<C-n>", "<CMD>tabnew<CR>", { noremap = true }) -- create a new tab
vim.api.nvim_set_keymap("n", "<leader>R", "<CMD>e<CR>", { noremap = true }) -- manual reload

require("config.lazy")

-- Colorscheme
vim.opt.background = "dark"
vim.cmd([[colorscheme gruvbox]])

-- Terminal background to match gruvbox hard contrast
vim.api.nvim_set_hl(0, "TerminalNormal", { bg = "#000000" })
vim.api.nvim_set_hl(0, "TerminalNormalNC", { bg = "#1d2021" })

-- blink syntax highlighting on signature
vim.api.nvim_set_hl(0, "BlinkCmpSignatureHelpActiveParameter", { link = "CursorLine" })

vim.cmd([[set nofoldenable]])

-- vim.diagnostic.config({ virtual_text = false })
-- vim.opt.clipboard = "unnamedplus"
-- vim.opt.cmdheight = 1
-- vim.opt.completeopt = { "menuone", "preview", "noinsert", "noselect" }
-- vim.opt.conceallevel = 0
-- vim.opt.fileencoding = "utf-8"
-- vim.opt.history = 10000
-- vim.opt.pumheight = 10
-- vim.opt.showmode = false
vim.opt.showtabline = 2 -- always show tab page labels
-- vim.opt.timeoutlen = 1000
-- vim.opt.wildignore = "*.o,*~,*.pyc"
-- vim.opt.wildmenu = true
-- vim.opt.wildmode = "list:longest,full"
