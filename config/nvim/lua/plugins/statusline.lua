return {
	"nvim-lualine/lualine.nvim",
	dependencies = { "nvim-tree/nvim-web-devicons" },
	config = function()
		local mode_map = {
			["NORMAL"] = "N",
			["INSERT"] = "I",
			["VISUAL"] = "V",
			["V-LINE"] = "VL",
			["V-BLOCK"] = "VB",
			["REPLACE"] = "R",
			["COMMAND"] = "C",
			["SELECT"] = "S",
			["S-LINE"] = "SL",
			["S-BLOCK"] = "SB",
			["TERMINAL"] = "T",
		}
		require("lualine").setup({
			options = {
				icons_enabled = false,
			},
			sections = {
				lualine_a = {
					{
						"mode",
						fmt = function(str)
							return mode_map[str] or str:sub(1, 2)
						end,
					},
				},
				lualine_b = { { "filename", path = 1 } },
				lualine_c = {},
				lualine_x = {},
				lualine_y = {},
				lualine_z = { "location" },
			},
		})
	end,
}
