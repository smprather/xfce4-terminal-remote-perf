-- xtrp bench nvim config: fixed options, no plugins.
vim.o.title = false
vim.o.number = true
vim.o.cursorline = true
vim.cmd("syntax on")
vim.o.laststatus = 2
vim.o.statusline = "%f %m%r%=%l,%c  %P"
vim.o.swapfile = false
vim.o.shada = ""
vim.o.mouse = ""
pcall(function() vim.o.termsync = (os.getenv("XTRP_SYNC") == "1") end)

local uv = vim.uv or vim.loop
local status_path = os.getenv("XTRP_STATUS")
local go_path = os.getenv("XTRP_GO")

local function emit(event)
  if not status_path then
    return
  end
  local f = io.open(status_path, "a")
  f:write(vim.json.encode(event) .. "\n")
  f:close()
end

-- nvim-scroll workload: n steps of <C-e> + redraw, bracketed by status events.
function XtrpScroll(n)
  if go_path then -- the runner creates it once startup has settled
    vim.wait(600000, function() return uv.fs_stat(go_path) ~= nil end, 5)
  end
  local ctrl_e = vim.api.nvim_replace_termcodes("<C-e>", true, false, true)
  emit({ event = "start", t = uv.hrtime() / 1e9 })
  for _ = 1, n do
    vim.cmd("normal! " .. ctrl_e)
    vim.cmd("redraw")
  end
  emit({ event = "end", t = uv.hrtime() / 1e9, bytes = 0 })
end
