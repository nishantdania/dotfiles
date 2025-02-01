-- Open Netrw explorer
vim.keymap.set("n", "<leader>f", "<CMD>Vex<CR>")

-- Only
vim.keymap.set("n", "<leader>o", "<CMD>only<CR>")

-- Clear highlights on search when pressing <Esc> in normal mode
vim.keymap.set("n", "<Esc>", "<cmd>nohlsearch<CR>")

-- Open vertical split
vim.keymap.set("n", "<leader>\\", "<cmd>vsp<CR>")

-- Open horizontal split
vim.keymap.set("n", "<leader>-", "<cmd>sp<CR>")

-- Hide highlights
vim.keymap.set("n", "<leader>n", "<cmd>nohl<CR>")
