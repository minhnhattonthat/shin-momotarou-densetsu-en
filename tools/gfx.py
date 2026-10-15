"""Graphics text: redraw the kanji icons of the status/number font (graphics resource 1, LZSS, VRAM $4480).

Graphics resource table C3:0000 (file 0x30000), 8-byte entries: VRAM word (2), size (2), 24-bit pointer, type
(03/04 = LZSS like the text, 05 = ?). Entry 1 = the number/icon font: 96 2bpp tiles, 8x16 cells (top tile n, bottom
n+16): set A (status bar) 0-15/16-31, set B (windows) 32-47/48-63, set C 8x8 small 64-79.
Icons are single cells, so they become two-letter tags (flagged abbreviations): 段 Lv, 体 HP, 技 SP, 両 ry,
呪 Cu (curse), 毒 Po (poison), マヒ Pa (paralysis).
    gfx.apply(rom, pos) -> new pos (writes the recompressed resource at pos in the expanded area)
"""
from comp import lzss_decode_upto, lzss_encode

GFX_TABLE = 0x30000

L3x7 = {
    'L': ['1..', '1..', '1..', '1..', '1..', '1..', '111'],
    'v': ['...', '...', '1.1', '1.1', '1.1', '1.1', '.1.'],
    'H': ['1.1', '1.1', '1.1', '111', '1.1', '1.1', '1.1'],
    'P': ['11.', '1.1', '1.1', '11.', '1..', '1..', '1..'],
    'S': ['.11', '1..', '1..', '.1.', '..1', '..1', '11.'],
    'r': ['...', '...', '1.1', '11.', '1..', '1..', '1..'],
    'y': ['...', '...', '1.1', '1.1', '.11', '..1', '11.'],
    'C': ['.11', '1..', '1..', '1..', '1..', '1..', '.11'],
    'u': ['...', '...', '1.1', '1.1', '1.1', '1.1', '.11'],
    'o': ['...', '...', '.1.', '1.1', '1.1', '1.1', '.1.'],
    'a': ['...', '...', '.1.', '..1', '.11', '1.1', '.11'],
}
# (top tile, bottom tile or None, tag)
ICONS = [(11, 27, 'Lv'), (12, 28, 'HP'), (13, 29, 'SP'),
         (43, 59, 'ry'), (44, 60, 'Cu'), (45, 61, 'Po'), (46, 62, 'Pa'),
         (75, None, 'Lv'), (76, None, 'HP'), (77, None, 'SP')]


def _get(data, t):
    b = data[t * 16:t * 16 + 16]
    return [[((b[2 * y] >> (7 - x)) & 1) | (((b[2 * y + 1] >> (7 - x)) & 1) << 1) for x in range(8)] for y in range(8)]


def _put(data, t, px):
    for y in range(8):
        p0 = p1 = 0
        for x in range(8):
            v = px[y][x]
            p0 |= (v & 1) << (7 - x)
            p1 |= ((v >> 1) & 1) << (7 - x)
        data[t * 16 + 2 * y] = p0
        data[t * 16 + 2 * y + 1] = p1


def _draw(data, top, bottom, tag):
    rows = _get(data, top) + (_get(data, bottom) if bottom is not None else [])
    flat = [v for r in rows for v in r]
    bg = max(set(flat), key=flat.count)
    h = len(rows)
    cell = [[bg] * 8 for _ in range(h)]
    y0 = 5 if h == 16 else 0
    for k, ch in enumerate(tag):
        g = L3x7[ch]
        for y, line in enumerate(g):
            for x, c in enumerate(line):
                if c == '1' and y0 + y < h:
                    cell[y0 + y][k * 4 + x] = 3
    _put(data, top, cell[:8])
    if bottom is not None:
        _put(data, bottom, cell[8:])


def entry(rom, i):
    e = GFX_TABLE + 8 * i
    return int.from_bytes(rom[e:e + 2], 'little'), int.from_bytes(rom[e + 2:e + 4], 'little'), \
        int.from_bytes(rom[e + 4:e + 7], 'little'), rom[e + 7]


def apply(rom, pos):
    vram, size, ptr, typ = entry(rom, 1)
    assert typ == 3, typ
    src = ptr & 0x3FFFFF
    data = bytearray(lzss_decode_upto(bytes(rom[:0x200000]) + bytes(64), src, 0x200000))[:size]
    assert len(data) == size, (len(data), size)
    for top, bottom, tag in ICONS:
        _draw(data, top, bottom, tag)
    comp = lzss_encode(bytes(data))
    rom[pos:pos + len(comp)] = comp
    e = GFX_TABLE + 8 + 4
    rom[e:e + 3] = (0xC00000 | pos).to_bytes(3, 'little')
    return pos + len(comp) + 2
