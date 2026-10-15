"""Code/data patches applied on top of the text and font (see docs/re/engine.md).

    patches.apply(rom)   # rom: bytearray, already expanded
"""

# 84:ACEE picks the glyph advance: $12CD bit 2 -> 16 px, bit 4 -> 14 px, bit 1 -> 12 px (windows/menus),
# else the per-page proportional table. English halves the fixed modes: 2 English cells per Japanese cell.
FIXED_ADVANCE = {0x4AD06: 8, 0x4AD0A: 7}

# 12 px mode: the Japanese space (code 50) keeps its 12 px cell so the windows' space padding still aligns;
# every other glyph advances 6 px. 84:AD01 (LDA #$0C; BRA $AD36) becomes JMP $F1C0:
FIXED12_HOOK = 0x4AD01
FIXED12_CODE_AT = 0x4F1C0  # bank 84 free space, after the width tables (build.RESERVED covers it)
FIXED12_CODE = bytes([
    0xA5, 0x07,        # LDA $07      page
    0xC9, 0x01,        # CMP #$01
    0xD0, 0x08,        # BNE six
    0xA5, 0x06,        # LDA $06      glyph index (0 = space)
    0xD0, 0x04,        # BNE six
    0xA9, 0x0C,        # LDA #$0C
    0x80, 0x02,        # BRA done
    0xA9, 0x06,        # six: LDA #$06
    0x4C, 0x36, 0xAD,  # done: JMP $AD36 (STA $12CC)
])


def apply(rom):
    for off, v in FIXED_ADVANCE.items():
        assert rom[off - 1] == 0xA9, hex(off)
        rom[off] = v
    assert rom[FIXED12_HOOK:FIXED12_HOOK + 4] == bytes([0xA9, 0x0C, 0x80, 0x31])
    assert rom[FIXED12_CODE_AT:FIXED12_CODE_AT + len(FIXED12_CODE)] == b'\xff' * len(FIXED12_CODE)
    rom[FIXED12_CODE_AT:FIXED12_CODE_AT + len(FIXED12_CODE)] = FIXED12_CODE
    rom[FIXED12_HOOK:FIXED12_HOOK + 3] = bytes([0x4C, FIXED12_CODE_AT & 0xFF, (FIXED12_CODE_AT >> 8) & 0xFF])
