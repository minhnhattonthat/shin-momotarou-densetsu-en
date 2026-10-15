-- Window warp: the next window script the game opens (84:AFB8, pointer in $B9-$BB) is replaced by WIN
-- (24-bit CPU address of a window script in the built ROM).   --var WIN=0xE01234 [--var COUNT=1]
local m = emu.memType.snesMemory
local left = COUNT or 1
L.on_exec(0x84AFB8, 0x84AFB8, function()
  if left <= 0 then return end
  left = left - 1
  emu.write(0xB9, WIN & 0xFF, m)
  emu.write(0xBA, (WIN >> 8) & 0xFF, m)
  emu.write(0xBB, (WIN >> 16) & 0xFF, m)
  L.log(string.format("f%d window warp -> %06X", L.frame, WIN))
end)
