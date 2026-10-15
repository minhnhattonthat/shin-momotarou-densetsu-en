-- Write bytes into WRAM once at frame AT (default 2): --var "POKES={[0x7E4075]=0x9C,[0x7E4076]=0x96}"
local m = emu.memType.snesMemory
local at = AT or 2
L.on_frame(function(f)
  if f ~= at then return end
  for a, v in pairs(POKES) do emu.write(a, v, m) end
  L.log("poked")
end)
