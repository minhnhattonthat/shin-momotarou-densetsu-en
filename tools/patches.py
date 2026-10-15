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


# Window name variables (21 53 n, printer 84:BEAE): the field is n Japanese cells; each printed char decremented
# the count (DEX) and swallowed one padding space of the script. English chars are half a cell, so the count is
# kept in half cells: doubled at entry, one script pad byte swallowed per two chars, and the end padding is
# 6 px per remaining half cell (in 8 px tiles) over ceil(X/2) skipped pad bytes.
NAMEVAR_AT = 0x4F1E0  # bank 84 free space (build.RESERVED)
NAMEVAR_CODE = bytes([
    # +00 entry: JSR $BB4E (field length) ; ASL A ; RTS
    0x20, 0x4E, 0xBB, 0x0A, 0x60,
    # +05 per char: DEX ; TXA ; AND #1 ; BNE +3 ; JSR $BB39 ; RTS
    0xCA, 0x8A, 0x29, 0x01, 0xD0, 0x03, 0x20, 0x39, 0xBB, 0x60,
    # +0F end: TXA ; BEQ ret ; STA $00 ; ASL A ; CLC ; ADC $00 ; CLC ; ADC #2 ; LSR A ; LSR A ; PHA ;
    #        TXA ; INC A ; LSR A ; TAX ; PLA ; ret: RTS
    0x8A, 0xF0, 0x12, 0x85, 0x00, 0x0A, 0x18, 0x65, 0x00, 0x18, 0x69, 0x02, 0x4A, 0x4A, 0x48,
    0x8A, 0x1A, 0x4A, 0xAA, 0x68, 0x60,
])
NAMEVAR_SITES = [
    # (offset, original bytes, new bytes)
    (0x4BEB8, bytes([0x20, 0x4E, 0xBB]), None),                      # JSR entry
    (0x4BF04, bytes([0x20, 0x39, 0xBB, 0xCA]), None),                # JSR per-char ; NOP
    (0x4BF13, bytes([0x68, 0x29, 0x01, 0x85, 0x1E, 0x8A, 0xF0, 0x2C]), None),  # PLA ; JSR end ; BEQ ; TAY ; BRA
]


def _namevar(rom):
    a = NAMEVAR_AT & 0xFFFF
    entry, per, end = a, a + 5, a + 0x0F
    new = [
        bytes([0x20, entry & 0xFF, entry >> 8]),
        bytes([0x20, per & 0xFF, per >> 8, 0xEA]),
        # PLA ; JSR end ; BEQ $BF47 ; TAY ; BRA $BF24
        bytes([0x68, 0x20, end & 0xFF, end >> 8, 0xF0, 0x2E, 0xA8, 0x80]),
    ]
    assert rom[NAMEVAR_AT:NAMEVAR_AT + len(NAMEVAR_CODE)] == b'\xff' * len(NAMEVAR_CODE)
    rom[NAMEVAR_AT:NAMEVAR_AT + len(NAMEVAR_CODE)] = NAMEVAR_CODE
    for (off, old, _), nb in zip(NAMEVAR_SITES, new):
        assert rom[off:off + len(old)] == old, hex(off)
        rom[off:off + len(nb)] = nb
    rom[0x4BF1B] = 0x08  # BRA operand: $BF1C + 8 = $BF24 (LDA $1392)


def apply(rom):
    _namevar(rom)
    for off, v in FIXED_ADVANCE.items():
        assert rom[off - 1] == 0xA9, hex(off)
        rom[off] = v
    assert rom[FIXED12_HOOK:FIXED12_HOOK + 4] == bytes([0xA9, 0x0C, 0x80, 0x31])
    assert rom[FIXED12_CODE_AT:FIXED12_CODE_AT + len(FIXED12_CODE)] == b'\xff' * len(FIXED12_CODE)
    rom[FIXED12_CODE_AT:FIXED12_CODE_AT + len(FIXED12_CODE)] = FIXED12_CODE
    rom[FIXED12_HOOK:FIXED12_HOOK + 3] = bytes([0x4C, FIXED12_CODE_AT & 0xFF, (FIXED12_CODE_AT >> 8) & 0xFF])
