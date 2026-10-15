-- Log the text stream pointer each time a new text is opened (849D91: $AE-$B0 -> $06, mode $12AA)
-- and the stream pointer at each char fetch when it jumps.
local m = emu.memType.snesMemory
local function rd(a) return emu.read(a, m) end
L.on_exec(0x849D91, 0x849D91, function()
  local p = rd(0xAE) | rd(0xAF) << 8 | rd(0xB0) << 16
  local s = emu.getState()
  L.log(string.format("f%d open src=%06X (off %06X) mode=%d A=%02X", L.frame, p, p & 0x3FFFFF, rd(0x12AA), s["cpu.a"] & 0xFF))
end)
local last = -1
L.on_exec(0x849E57, 0x849E57, function()
  local p = rd(0xB1) | rd(0xB2) << 8 | rd(0xB3) << 16
  if p ~= last + 1 then L.log(string.format("f%d raw-fetch %06X (off %06X)", L.frame, p, p & 0x3FFFFF)) end
  last = p
end)
