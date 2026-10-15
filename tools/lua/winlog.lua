-- Log window opens (84:AFB8 / 84:AFD5 / 84:B7FB / 84:B806) with the script pointer $B9-$BB, and text opens (84:A0E5).
local m = emu.memType.snesMemory
local function ptr() return emu.read(0xBB, m) << 16 | emu.read(0xBA, m) << 8 | emu.read(0xB9, m) end
for _, a in ipairs({0x84AFB8, 0x84AFD5, 0x84B7FB, 0x84B806}) do
  L.on_exec(a, a, function() L.log(string.format("f%d win@%06X B9=%06X", L.frame, a, ptr())) end)
end
L.on_exec(0x84A0E5, 0x84A0E5, function()
  L.log(string.format("f%d text block=%d idx=%d", L.frame, emu.read(0x12B4, m), emu.read(0x12B5, m)))
end)
