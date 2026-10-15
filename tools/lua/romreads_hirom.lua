-- HiROM ROM-read logger: each distinct (PC, ROM bank) reading ROM between frames FROM..TO.
--   emu.py ... --script tools/lua/romreads_hirom.lua --var FROM=1200 --var TO=1260
local from, to = FROM or 0, TO or math.huge
local seen = {}
local function hook(addr, value)
  if L.frame < from or L.frame > to then return end
  local s = emu.getState()
  local pc = (s["cpu.k"] << 16) | s["cpu.pc"]
  local key = pc * 256 + (addr >> 16)
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("f%d pc=%06X read %06X (off %06X)=%02X A=%04X X=%04X Y=%04X DB=%02X", L.frame, pc, addr,
    addr & 0x3FFFFF, value, s["cpu.a"], s["cpu.x"], s["cpu.y"], s["cpu.dbr"]))
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
