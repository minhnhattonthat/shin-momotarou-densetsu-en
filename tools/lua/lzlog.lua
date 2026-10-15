-- Log every LZSS stream open (80:BCEE: source in $06-$08) with frame and caller.
local m = emu.memType.snesMemory
L.on_exec(0x80BCEE, 0x80BCEE, function()
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local ret = emu.read(sp + 3, m) << 16 | emu.read(sp + 2, m) << 8 | emu.read(sp + 1, m)
  L.log(string.format("f%d lz src=%02X%02X%02X ret=%06X", L.frame, emu.read(0x08, m), emu.read(0x07, m),
    emu.read(0x06, m), ret))
end)
