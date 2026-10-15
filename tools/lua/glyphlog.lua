-- Log every glyph draw (84:A8FD: $07 page, $06 index) between FROM..TO frames.
local m = emu.memType.snesMemory
local from, to = FROM or 0, TO or math.huge
L.on_exec(0x84A8FD, 0x84A8FD, function()
  if L.frame < from or L.frame > to then return end
  L.log(string.format("f%d page=%02X idx=%02X 12CD=%02X B9=%02X%02X%02X", L.frame, emu.read(0x07, m), emu.read(0x06, m),
    emu.read(0x12CD, m), emu.read(0xBB, m), emu.read(0xBA, m), emu.read(0xB9, m)))
end)
