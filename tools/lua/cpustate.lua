-- Log CPU registers and the stack page at frame AT (default 1); RAM dump of $7E0000-$7FFFFF to OUT if set.
--   emu.py ... --script tools/lua/cpustate.lua [--var AT=5] [--var OUT='"work/ram.bin"']
local at = AT or 1
L.on_frame(function(f)
  if f ~= at then return end
  local s = emu.getState()
  L.log(string.format("PC=%02X:%04X A=%04X X=%04X Y=%04X SP=%04X D=%04X DB=%02X P=%02X", s["cpu.k"], s["cpu.pc"],
    s["cpu.a"], s["cpu.x"], s["cpu.y"], s["cpu.sp"], s["cpu.d"], s["cpu.dbr"], s["cpu.ps"]))
  local m = emu.memType.snesMemory
  local page = s["cpu.sp"] & 0xFF00
  for row = page, page + 0xF0, 16 do
    local t = {}
    for i = 0, 15 do t[#t + 1] = string.format("%02X", emu.read(row + i, m)) end
    L.log(string.format("%04X %s", row, table.concat(t, " ")))
  end
  if OUT then L.dump_ram(OUT) end
end)
