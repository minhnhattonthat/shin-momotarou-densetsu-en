-- At each exec of PC (between FROM..TO, at most N times) log SP and the 24 stack bytes above it (call chain).
--   emu.py ... --script tools/lua/stackat.lua --var PC=0x849D91 [--var FROM=340 --var TO=420 --var N=3]
local from, to, left = FROM or 0, TO or math.huge, N or 3
L.on_exec(PC, PC, function()
  if L.frame < from or L.frame > to or left <= 0 then return end
  left = left - 1
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local t = {}
  for i = 1, 24 do t[#t + 1] = string.format("%02X", emu.read(sp + i, emu.memType.snesMemory)) end
  L.log(string.format("f%d SP=%04X A=%04X X=%04X Y=%04X: %s", L.frame, sp, s["cpu.a"], s["cpu.x"], s["cpu.y"],
    table.concat(t, " ")))
end)
