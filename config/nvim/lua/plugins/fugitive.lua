return {
	"tpope/vim-fugitive",
	dependencies = { "tpope/vim-rhubarb" },
	config = function() end,
	keys = {
		{ "gb", "<cmd>Git blame<cr>" },
		{ "gh", "<cmd>GBrowse<cr>" },
	},
}
