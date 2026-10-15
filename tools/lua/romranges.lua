-- Per reading PC: min/max ROM offset (HiROM) and count between FROM..TO; logged at TO.
local from, to = FROM or 0, TO or math.huge
local r = {}
local function hook(addr, value)
  if L.frame < from or L.frame > to then return end
  local s = emu.getState()
  local pc = (s["cpu.k"] << 16) | s["cpu.pc"]
  local off = addr & 0x3FFFFF
  local e = r[pc]
  if not e then r[pc] = {off, off, 1} else
    if off < e[1] then e[1] = off end
    if off > e[2] then e[2] = off end
    e[3] = e[3] + 1
  end
end
for bank = 0xC0, 0xFF do
  emu.addMemoryCallback(L.safe(hook), emu.callbackType.read, bank << 16, (bank << 16) | 0xFFFF,
    emu.cpuType.snes, emu.memType.snesMemory)
end
for _, base in ipairs({0x00, 0x80}) do
  for bank = base, base + 0x3F do
    emu.addMemoryCallback(L.safe(hook), emu.callbackType.read, (bank << 16) | 0x8000, (bank << 16) | 0xFFFF,
      emu.cpuType.snes, emu.memType.snesMemory)
  end
end
L.on_frame(function(f)
  if f == to then
    for pc, e in pairs(r) do
      if e[3] > 64 then L.log(string.format("pc=%06X %06X-%06X n=%d", pc, e[1], e[2], e[3])) end
    end
  end
end)
