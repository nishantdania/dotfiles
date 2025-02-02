return {
	"nvim-telescope/telescope.nvim",
	tag = "0.1.8",
	-- or , branch = '0.1.x',
	dependencies = {
		"nvim-lua/plenary.nvim",
		{ "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
		"BurntSushi/ripgrep",
	},
	lazy = false,
	opts = {
		pickers = {
			find_files = {
				hidden = true,
				disable_devicons = true,
			},
			git_files = {
				hidden = true,
			},
		},
		defaults = {},
		extensions = {
			fzf = {},
		},
	},
	config = function(_, opts)
		require("telescope").setup(opts)
		require("telescope").load_extension("fzf")
	end,
	keys = {
		{ "<leader><leader>", "<cmd>Telescope find_files<cr>" },
		{ "<C-f>", "<cmd>Telescope live_grep<cr>" },
	},
}
