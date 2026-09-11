local M = {}

function M.get_exe()
   local conda_prefix = vim.env.CONDA_PREFIX
   if conda_prefix then
      local py = conda_prefix .. "/bin/python"
      if vim.fn.executable(py) == 1 then
         return vim.fn.resolve(py)
      end
   end
   local cwd = vim.fn.getcwd()
   if vim.fn.filereadable(cwd .. "/pixi.toml") == 1 then
      local pixi_envs = vim.fn.glob(cwd .. "/.pixi/envs/*/bin/python", false, true)
      if #pixi_envs > 0 then
         return vim.fn.resolve(pixi_envs[1])
      end
   end
   for _, name in ipairs({ ".venv", "venv", ".conda", "env", ".pixi/envs/default" }) do
      local py = cwd .. "/" .. name .. "/bin/python"
      if vim.fn.executable(py) == 1 then
         return vim.fn.resolve(py)
      end
   end
   return vim.fn.exepath("python")
end

return M
