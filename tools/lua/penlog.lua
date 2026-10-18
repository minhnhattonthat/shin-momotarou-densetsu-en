-- Log each glyph draw (84:A8FD) with the pen: $12C7 tile column, $12C9 pixel offset in the tile, $12CC advance,
-- $07 page / $06 index, between FROM..TO frames.
local m = emu.memType.snesMemory
local function rd(a) return emu.read(a, m) end
local from, to = FROM or 0, TO or math.huge
L.on_exec(0x84A8FD, 0x84A8FD, function()
  if L.frame < from or L.frame > to then return end
  L.log(string.format("f%d page=%02X idx=%02X col=%02X px=%02X adv=%02X", L.frame, rd(0x07), rd(0x06), rd(0x12C7),
    rd(0x12C9), rd(0x12CC)))
end)
