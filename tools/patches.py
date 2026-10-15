"""Code/data patches applied on top of the text and font (see docs/re/engine.md).

    patches.apply(rom)   # rom: bytearray, already expanded
"""

# 84:ACEE picks the glyph advance: $12CD bit 2 -> 16 px, bit 4 -> 14 px, bit 1 -> 12 px (windows/menus),
# else the per-page proportional table. English halves the fixed modes: 2 English cells per Japanese cell.
FIXED_ADVANCE = {0x4AD06: 8, 0x4AD0A: 7}

# 12 px mode: the Japanese space (code 50) keeps its 12 px cell so the windows' space padding still aligns;
# every other glyph advances 6 px. 84:AD01 (LDA #$0C; BRA $AD36) becomes JMP $F1C0:
FIXED12_HOOK = 0x4AD01
# Glyphs narrower than 6 px are centred in their cell (else "Tal k", "Mi l l et"): pad = (6 - width) // 2 is added to
# the pen (through the advance routine 84:AC8B) before drawing and the advance becomes 6 - pad.
FIXED12_CODE_AT = 0x4F240  # moved past the measure patch (build.RESERVED covers it)
WIDTH_LOOKUP = slice(0x4AD0D, 0x4AD36)  # original proportional width lookup (relative branches; A = width)
FIXED12_HEAD = bytes([
    0xA5, 0x07,        # LDA $07      page
    0xC9, 0x01,        # CMP #$01
    0xD0, 0x08,        # BNE glyph
    0xA5, 0x06,        # LDA $06      glyph index (0 = space)
    0xD0, 0x04,        # BNE glyph
    0xA9, 0x0C,        # LDA #$0C
    0x80, 0x46,        # BRA done
])                     # glyph: <width lookup copy>
FIXED12_TAIL = bytes([
    0xC9, 0x06,        # CMP #$06
    0xB0, 0x17,        # BCS six
    0x49, 0xFF, 0x1A,  # EOR #$FF ; INC A
    0x18, 0x69, 0x06,  # CLC ; ADC #6
    0x4A, 0x48,        # LSR A ; PHA     pad
    0x8D, 0xCC, 0x12,  # STA $12CC
    0x20, 0x8B, 0xAC,  # JSR $AC8B       pen += pad (the real advance: flushes a finished tile)
    0x68,              # PLA
    0x49, 0xFF, 0x1A,  # EOR #$FF ; INC A
    0x18, 0x69, 0x06,  # CLC ; ADC #6    advance = 6 - pad
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
    # +05 per char: TXA ; BEQ ret (field full: a longer name overflows instead of eating the script) ;
    #              DEX ; TXA ; AND #1 ; BNE ret ; JSR $BB39 ; ret: RTS
    0x8A, 0xF0, 0x09, 0xCA, 0x8A, 0x29, 0x01, 0xD0, 0x03, 0x20, 0x39, 0xBB, 0x60,
    # +12 end: TXA ; BEQ ret ; STA $00 ; ASL A ; CLC ; ADC $00 ; CLC ; ADC #2 ; LSR A ; LSR A ; PHA ;
    #        TXA ; INC A ; LSR A ; TAX ; PLA ; ret: RTS
    0x8A, 0xF0, 0x11, 0x85, 0x00, 0x0A, 0x18, 0x65, 0x00, 0x18, 0x69, 0x02, 0x4A, 0x4A, 0x48,
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
    entry, per, end = a, a + 5, a + 0x12
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


# Window width measure (84:BFE3): every character counted 3 units (12 px, unit = 4 px). English glyphs are 6 px:
# count 1 unit on even and 2 on odd characters (3 per pair). 84:C02C INC $09 ; BRA $C033 -> JMP to this code.
MEASURE_AT = 0x4F220
MEASURE_CODE = bytes([
    0xE6, 0x09,        # INC $09
    0xA5, 0x0A,        # LDA $0A      characters so far on this line
    0x4A,              # LSR A
    0x90, 0x02,        # BCC +2
    0xE6, 0x09,        # INC $09
    0x4C, 0x37, 0xC0,  # JMP $C037    (INC $0A ; next)
])


def _measure(rom):
    assert rom[0x4C02C:0x4C030] == bytes([0xE6, 0x09, 0x80, 0x03])
    assert rom[MEASURE_AT:MEASURE_AT + len(MEASURE_CODE)] == b'\xff' * len(MEASURE_CODE)
    rom[MEASURE_AT:MEASURE_AT + len(MEASURE_CODE)] = MEASURE_CODE
    rom[0x4C02C:0x4C02F] = bytes([0x4C, MEASURE_AT & 0xFF, (MEASURE_AT >> 8) & 0xFF])


def apply(rom, skip=()):
    if 'namevar' not in skip:
        _namevar(rom)
    if 'measure' not in skip:
        _measure(rom)
    if 'fixed12' in skip:
        return
    for off, v in FIXED_ADVANCE.items():
        assert rom[off - 1] == 0xA9, hex(off)
        rom[off] = v
    assert rom[FIXED12_HOOK:FIXED12_HOOK + 4] == bytes([0xA9, 0x0C, 0x80, 0x31])
    FIXED12_CODE = FIXED12_HEAD + bytes(rom[WIDTH_LOOKUP]) + FIXED12_TAIL
    assert len(FIXED12_CODE) == 0x57
    assert rom[FIXED12_CODE_AT:FIXED12_CODE_AT + len(FIXED12_CODE)] == b'\xff' * len(FIXED12_CODE)
    rom[FIXED12_CODE_AT:FIXED12_CODE_AT + len(FIXED12_CODE)] = FIXED12_CODE
    rom[FIXED12_HOOK:FIXED12_HOOK + 3] = bytes([0x4C, FIXED12_CODE_AT & 0xFF, (FIXED12_CODE_AT >> 8) & 0xFF])
