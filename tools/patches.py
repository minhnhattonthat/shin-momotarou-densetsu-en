"""Code/data patches applied on top of the text and font (see docs/re/engine.md).

    patches.apply(rom)   # rom: bytearray, already expanded
"""

# 84:ACEE picks the glyph advance: $12CD bit 2 -> 16 px, bit 4 -> 14 px, bit 1 -> 12 px (windows/menus),
# else the per-page proportional table. English halves the fixed modes: 2 English cells per Japanese cell.
FIXED_ADVANCE = {0x4AD02: 6, 0x4AD06: 8, 0x4AD0A: 7}


def apply(rom):
    for off, v in FIXED_ADVANCE.items():
        assert rom[off - 1] == 0xA9, hex(off)
        rom[off] = v
