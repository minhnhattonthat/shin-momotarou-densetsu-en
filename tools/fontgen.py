"""English font pages + VWF width tables for the game's own proportional renderer.

Page 1 (codes 50-8F) and page 2 (codes 90-CF) are rebuilt from font_en.py and placed in bank DA free space;
the per-page width tables (84:AD3C list -> (limit, width) pairs) are rebuilt in bank 84 free space.
    from fontgen import EN_PAGE1, EN_PAGE2, build_font
"""
from font_en import glyphs, outline

# 64 codes each. Digits, A-Z and space keep their original codes (the game builds numbers from 50-5A).
EN_PAGE1 = (' 0123456789?!,.…'
            "'ABCDEFGHIJKLMNO"
            'PQRSTUVWXYZ()":~'
            '-;/+&%*#=<>[]@$^')
EN_PAGE2 = 'abcdefghijklmnopqrstuvwxyz'  # 90-A9; page 2 holds up to 47 glyphs (90-BE)

ROW0, ROW1 = 2, 14          # glyph rows stored (extents byte 0x2E): 13 rows
H = ROW1 - ROW0 + 1
SIZE = (H * 3 + 1) & 0x3E   # bytes per glyph (2 planes x (H + ceil(H/2)))

FONT_FREE = 0x1A2202        # bank DA free space (to 0x1A37FF)
FONT_PTRS = 0x1A3800        # page pointer table, 16-bit, page n at +2(n-1)
WIDTH_LIST = 0x04AD3C       # (page, ptr16) triples, 00-terminated, then default ptr
WIDTH_FREE = 0x04F15C       # bank 84 free space (to 0x4FFFF)


def _glyph_bytes(bits16):
    """bits16: 16 rows of 12-bit ink (bit 11 = leftmost). Returns the page glyph bytes."""
    ink = bits16
    # outline over 12 px: 8-neighbour dilation minus ink
    sh = []
    for y in range(16):
        acc = 0
        for dy in (-1, 0, 1):
            if 0 <= y + dy < 16:
                r = ink[y + dy]
                acc |= r | (r << 1) | (r >> 1)
        sh.append(acc & 0xFFF & ~ink[y])
    plane0 = [ink[y] | sh[y] for y in range(16)]   # ink and shadow
    plane1 = ink                                    # ink only
    data = bytearray()
    for plane in (plane0, plane1):
        rows = plane[ROW0:ROW1 + 1]
        data += bytes((r >> 4) & 0xFF for r in rows)
        for k in range(0, H, 2):
            a = rows[k] & 0xF
            b = rows[k + 1] & 0xF if k + 1 < H else 0
            data.append((a << 4) | b)
    assert len(data) == SIZE, len(data)
    return bytes(data)


def _cell(ch, g):
    """(advance, 16 rows of 12-bit ink) for one character."""
    w, bits = g[ch]
    rows = [(b << 4) & 0xFFF for b in bits]  # font_en rows are 8-bit with bit 7 = column 0
    for y in range(16):
        assert not (rows[y] and (y < ROW0 + 1 or y > ROW1 - 1)), (ch, y)
    return w + 1, rows


def build_page(chars, n):
    g = glyphs()
    if '…' not in g:
        g['…'] = (7, [0] * 11 + [0b01010100] + [0] * 4)
    data = bytearray([(ROW0 << 4) | ROW1])
    widths = []
    for i in range(n):
        ch = chars[i] if i < len(chars) else ' '
        adv, rows = _cell(ch, g)
        data += _glyph_bytes(rows)
        widths.append(adv)
    return bytes(data), widths


def width_table(widths):
    """(limit, width) pairs: glyph idx < limit -> width; merges runs; ends with FF."""
    out = bytearray()
    for i, w in enumerate(widths):
        if out and out[-1] == w:
            out[-2] = i + 1
        else:
            out += bytes([i + 1, w])
    out[-2] = 0xFF
    return bytes(out)


def build_font(rom):
    """Write new pages 1/2 and their width tables into rom (bytearray). Returns {char: advance} for both pages."""
    p1, w1 = build_page(EN_PAGE1, 64)
    p2, w2 = build_page(EN_PAGE2, 47)
    a1 = FONT_FREE
    a2 = a1 + len(p1)
    assert a2 + len(p2) <= 0x1A3800
    rom[a1:a1 + len(p1)] = p1
    rom[a2:a2 + len(p2)] = p2
    rom[FONT_PTRS:FONT_PTRS + 2] = (a1 & 0xFFFF).to_bytes(2, 'little')
    rom[FONT_PTRS + 2:FONT_PTRS + 4] = (a2 & 0xFFFF).to_bytes(2, 'little')
    t1, t2 = width_table(w1), width_table(w2)
    rom[WIDTH_FREE:WIDTH_FREE + len(t1)] = t1
    rom[WIDTH_FREE + len(t1):WIDTH_FREE + len(t1) + len(t2)] = t2
    i = WIDTH_LIST
    while rom[i]:
        if rom[i] == 1:
            rom[i + 1:i + 3] = (WIDTH_FREE & 0xFFFF | 0x8000).to_bytes(2, 'little')
        elif rom[i] == 2:
            rom[i + 1:i + 3] = ((WIDTH_FREE + len(t1)) & 0xFFFF | 0x8000).to_bytes(2, 'little')
        i += 3
    adv = {}
    for chars, ws in ((EN_PAGE1, w1), (EN_PAGE2, w2)):
        for c, w in zip(chars, ws):
            adv.setdefault(c, w)
    return adv


def advances():
    _, w1 = build_page(EN_PAGE1, 64)
    _, w2 = build_page(EN_PAGE2, 47)
    adv = {}
    for chars, ws in ((EN_PAGE1, w1), (EN_PAGE2, w2)):
        for c, w in zip(chars, ws):
            adv.setdefault(c, w)
    return adv
