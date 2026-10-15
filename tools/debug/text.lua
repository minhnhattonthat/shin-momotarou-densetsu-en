-- Text warp: the next text box the game opens shows block BLOCK, string INDEX instead (84:A0E5 opens a text;
-- $12B4 = block, $12B5 = string index). Use with a route that makes the game open any text box
-- (tools/debug/warp.py drives this from the field examine command).
--   --var BLOCK=20 --var INDEX=56 [--var COUNT=1] [--var DUMP_AT=frames after the open]
local m = emu.memType.snesMemory
local left = COUNT or 1
L.on_exec(0x84A0E5, 0x84A0E5, function()
  if left <= 0 then return end
  left = left - 1
  emu.write(0x12B4, BLOCK, m)
  emu.write(0x12B5, INDEX, m)
  L.log(string.format("f%d text warp -> block %d string %d", L.frame, BLOCK, INDEX))
end)
