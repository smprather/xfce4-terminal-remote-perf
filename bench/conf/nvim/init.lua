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
local clk_tck = tonumber((vim.fn.system({ "getconf", "CLK_TCK" }) or ""):match("%d+")) or 100

-- (comm, ppid, utime+stime ticks) of a pid, from /proc/<pid>/stat
local function stat(pid)
  local f = io.open("/proc/" .. pid .. "/stat")
  if not f then
    return nil
  end
  local s = f:read("*a")
  f:close()
  local comm = s:match("%((.*)%)")
  local fields = vim.split(s:match("%) (.*)$"), " ", { plain = true })
  return comm, tonumber(fields[2]), tonumber(fields[12]) + tonumber(fields[13])
end

-- CPU seconds of a process: sum of its live threads' schedstat (ns); falls back to stat ticks
local function cpu_s(pid, ticks)
  local ok, tids = pcall(vim.fn.readdir, "/proc/" .. pid .. "/task")
  local total, found = 0, false
  if ok and type(tids) == "table" then
    for _, tid in ipairs(tids) do
      local f = io.open("/proc/" .. pid .. "/task/" .. tid .. "/schedstat")
      if f then
        local ns = tonumber((f:read("*l") or ""):match("^(%d+)"))
        f:close()
        if ns then
          total, found = total + ns, true
        end
      end
    end
  end
  if found then
    return total / 1e9
  end
  return ticks / clk_tck
end

-- CPU seconds of the nearest xfce4-terminal ancestor, or nil
local function term_cpu()
  local pid = vim.fn.getpid()
  while pid and pid > 1 do
    local comm, ppid, ticks = stat(pid)
    if not comm then
      return nil
    end
    if comm:sub(1, 13) == "xfce4-termina" then
      return cpu_s(pid, ticks)
    end
    pid = ppid
  end
  return nil
end

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
  local ctrl_e = vim.api.nvim_replace_termcodes("<C-e>", true, false, true)
  local c0 = term_cpu()
  emit({ event = "start", t = uv.hrtime() / 1e9 })
  for _ = 1, n do
    vim.cmd("normal! " .. ctrl_e)
    vim.cmd("redraw")
  end
  local c1 = term_cpu()
  emit({ event = "end", t = uv.hrtime() / 1e9, bytes = 0,
         term_cpu_s = (c0 and c1) and (c1 - c0) or vim.NIL })
end
