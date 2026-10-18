-- Log the window measure result (84:BFE3 -> $138F max units per line (4 px), $138D max chars, $138E 2 x lines)
-- and each line's units ($09 at 84:C04C) with the script pointer $B9-$BB. CHARS=1: also each counted byte.
local m = emu.memType.snesMemory
local function rd(a) return emu.read(a, m) end
L.on_exec(0x84C04C, 0x84C04C, function()
  L.log(string.format("f%d line units=%d chars=%d", L.frame, rd(0x09), rd(0x0A)))
end)
L.on_exec(0x84B9AC, 0x84B9AC, function()
  L.log(string.format("f%d win %02X%02X%02X max units=%d chars=%d lines2=%d", L.frame, rd(0xBB), rd(0xBA), rd(0xB9),
    rd(0x138F), rd(0x138D), rd(0x138E)))
end)
-- line end padding (84:C172): renderer units $1394 vs measured max $138F, tile column $030B
L.on_exec(0x84C172, 0x84C172, function()
  L.log(string.format("f%d pad: drawn units=%d max=%d col=%d", L.frame, rd(0x1394), rd(0x138F), rd(0x030B)))
end)
if CHARS then
  for _, pc in ipairs({0x84C02C, 0x84C030, 0x84C037}) do
    L.on_exec(pc, pc, function()
      L.log(string.format("  %06X byte=%02X%02X units=%d", pc, rd(0x1391), rd(0x1390), rd(0x09)))
    end)
  end
end
