-- Set leader to Space
vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- Case-insensitive searching UNLESS \C or one or more capital letters in the search term
vim.opt.ignorecase = true
vim.opt.smartcase = true

-- Always show line numbers
vim.o.number = true

-- Tabs are 2 spaces long
vim.o.tabstop = 2
vim.o.softtabstop = 2
vim.o.shiftwidth = 2
vim.o.expandtab = true

-- Always show signcolumn,
-- else errors/warnings lead to shift in UI
vim.o.signcolumn = "yes"

-- Default split directions
vim.o.splitbelow = true
vim.o.splitright = true

-- Netrw hide banner
vim.g.netrw_banner = 0
-- Netrw small size
vim.g.netrw_winsize = 25
-- Netrw tree style list
vim.g.netrw_liststyle = 3
-- Netrw open files in current buffer
vim.g.netrw_browse_split = 4

-- Sync clipboard between OS and Neovim.
-- --  Schedule the setting after `UiEnter` because it can increase startup-time.
-- --  Remove this option if you want your OS clipboard to remain independent.
-- --  See `:help 'clipboard'`
vim.schedule(function()
	vim.opt.clipboard = "unnamedplus"
end)

-- Disable mouse
vim.opt.mouse = ""

-- Save undo history
vim.opt.undofile = true
