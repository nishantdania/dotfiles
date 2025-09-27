return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        ruby_lsp = {
          mason = false,
          cmd = { "mise", "x", "--", "ruby-lsp" },
          on_attach = function(client)
            client.server_capabilities.documentHighlightProvider = false
          end,
        },
      },
    },
  },
}
