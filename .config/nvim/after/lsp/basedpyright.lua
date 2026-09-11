---@type vim.lsp.Config
return {
   settings = {
      python = { pythonPath = require("lib.python").get_exe() },
      basedpyright = {
         analysis = {
            typeCheckingMode = "off",
            autoSearchPaths = true,
            diagnosticMode = "openFilesOnly",
            useLibraryCodeForTypes = true,
            diagnosticSeverityOverrides = { reportUnusedParameter = false },
         },
      },
   },
}
