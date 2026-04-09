-- Make sure to setup `mapleader` and `maplocalleader` before
-- loading lazy.nvim so that mappings are correct.
-- This is also a good place to setup other settings (vim.opt)
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

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
vim.opt.autoread = true -- update file in Neovim if it has been changed outside of Neovim
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

require("config.lazy")

-- Colorscheme
vim.opt.background = "dark"
vim.cmd([[colorscheme gruvbox]])

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
-- vim.opt.updatetime = 300
-- vim.opt.wildignore = "*.o,*~,*.pyc"
-- vim.opt.wildmenu = true
-- vim.opt.wildmode = "list:longest,full"

vim.api.nvim_set_keymap("n", "<leader>h", ":nohl<CR>", { noremap = true })
