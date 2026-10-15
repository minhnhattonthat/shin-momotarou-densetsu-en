-- Log the call stack whenever glyph PAGE/IDX is drawn (84:A8FD, $07 page, $06 index).
--   --var PAGE=8 --var IDX=0x18 [--var MAXLOG=5]
local m = emu.memType.snesMemory
local n = 0
L.on_exec(0x84A8FD, 0x84A8FD, function()
  if n >= (MAXLOG or 5) then return end
  if emu.read(0x07, m) ~= PAGE or emu.read(0x06, m) ~= IDX then return end
  n = n + 1
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local t = {}
  for i = 1, 40 do t[#t + 1] = string.format("%02X", emu.read(sp + i, m)) end
  L.log(string.format("f%d sp=%04X B9=%02X%02X%02X stack %s", L.frame, sp, emu.read(0xBB, m), emu.read(0xBA, m),
    emu.read(0xB9, m), table.concat(t, " ")))
end)
