local function get_python_path()
   -- Check active pixi/conda environment first
   local conda_prefix = vim.env.CONDA_PREFIX
   if conda_prefix then
      local py = conda_prefix .. "/bin/python"
      if vim.fn.executable(py) == 1 then
         return vim.fn.resolve(py)
      end
   end
   -- Fall back to common venv directories in cwd
   local cwd = vim.fn.getcwd()
   for _, name in ipairs({ ".venv", "venv", ".conda", "env", ".pixi/envs/default" }) do
      local py = cwd .. "/" .. name .. "/bin/python"
      if vim.fn.executable(py) == 1 then
         return vim.fn.resolve(py)
      end
   end
   return vim.fn.exepath("python")
end

---@type vim.lsp.Config
return {
   settings = {
      python = { pythonPath = get_python_path() },
      basedpyright = {
         analysis = {
            typeCheckingMode = "off",
            autoSearchPaths = true,
            diagnosticMode = "openFilesOnly",
            useLibraryCodeForTypes = true,
            diagnosticSeverityOverrides = {
               reportUnusedParameter = false,
            },
         },
      },
   },
}
