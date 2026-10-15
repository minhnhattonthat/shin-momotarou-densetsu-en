-- Count executed PCs in [LO,HI] between frames FROM..TO; log the top ones at TO.
local cnt = {}
L.on_exec(LO, HI, function()
  if L.frame < FROM or L.frame > TO then return end
  local s = emu.getState()
  local pc = (s["cpu.k"] << 16) | s["cpu.pc"]
  cnt[pc] = (cnt[pc] or 0) + 1
end)
L.on_frame(function(f)
  if f == TO then
    local arr = {}
    for pc, n in pairs(cnt) do arr[#arr + 1] = {pc, n} end
    table.sort(arr, function(a, b) return a[1] < b[1] end)
    for _, e in ipairs(arr) do L.log(string.format("%06X %d", e[1], e[2])) end
  end
end)
