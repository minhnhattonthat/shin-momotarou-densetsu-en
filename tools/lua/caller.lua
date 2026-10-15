-- Log distinct callers (JSL return address on stack) of routine at CALLEE between FROM..TO.
--   emu.py ... --script tools/lua/caller.lua --var CALLEE=0x80A170 --var FROM=3430 --var TO=3440 [--var JSR=1]
local from, to = FROM or 0, TO or math.huge
local seen = {}
L.on_exec(CALLEE, CALLEE, function()
  if L.frame < from or L.frame > to then return end
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local m = emu.memType.snesMemory
  local lo, hi = emu.read(sp + 1, m), emu.read(sp + 2, m)
  local bank = JSR and s["cpu.k"] or emu.read(sp + 3, m)
  local ret = (bank << 16) | (hi << 8) | lo
  local key = ret
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("f%d ret=%06X A=%04X X=%04X Y=%04X DB=%02X D=%04X", L.frame, ret, s["cpu.a"], s["cpu.x"],
    s["cpu.y"], s["cpu.dbr"], s["cpu.d"]))
end)
