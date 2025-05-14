return {
	"nvim-treesitter/nvim-treesitter",
	build = ":TSUpdate",
	config = function()
		local configs = require("nvim-treesitter.configs")

		configs.setup({
			ensure_installed = {
				"ruby",
				"javascript",
				"typescript",
				"tsx",
				"html",
				"css",
				"embedded_template",
				"lua",
				"diff",
				"svelte",
			},
			sync_install = true,
			highlight = {
				enable = true,
				additional_vim_regex_highlighting = { "ruby" },
			},
			indent = {
				enable = true,
				disable = { "ruby" },
			},
		})
	end,
}
