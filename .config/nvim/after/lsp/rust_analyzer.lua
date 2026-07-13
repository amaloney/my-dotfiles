-- Complete `println!` instead of `println!(<CURSOR>)`
local capabilities = vim.lsp.protocol.make_client_capabilities()
capabilities.textDocument.completion.completionItem.snippetSupport = false

---@type vim.lsp.Config
return {
   capabilities = capabilities,
}