"""Render the game's dialogue font pages (bank DA) to a PNG sheet for building tables.

Page p (1-based) base = DA:[3800 + 2*(p-1)]; byte 0 = rows (hi nibble top, lo nibble bottom);
then glyphs of size (h*3+1)&0x3E: two layers (plane 0, plane 1), each h bytes of left 8 px then
ceil(h/2) bytes of right 4 px (hi nibble = row r, lo nibble = row r+1).
    python -X utf8 tools/fontdump.py ROM OUT.png PAGE [COUNT]
"""
import sys, zlib, struct

FONT_BANK = 0x1A0000
PTRS = 0x1A3800


def page_info(rom, p):
    base = FONT_BANK + int.from_bytes(rom[PTRS + 2 * (p - 1):PTRS + 2 * p], 'little')
    ext = rom[base]
    top, bot = ext >> 4, ext & 15
    h = bot - top + 1
    size = (h * 3 + 1) & 0x3E
    return base + 1, top, h, size


def glyph(rom, p, i):
    """12x16 grid of pixel values 0..3."""
    base, top, h, size = page_info(rom, p)
    g = rom[base + i * size: base + (i + 1) * size]
    pix = [[0] * 12 for _ in range(16)]
    pos = 0
    for plane in range(2):
        for r in range(h):
            b = g[pos + r]
            for x in range(8):
                if b & (0x80 >> x):
                    pix[top + r][x] |= 1 << plane
        pos += h
        for r in range(h):
            b = g[pos + r // 2]
            nib = (b >> 4) if r % 2 == 0 else (b & 15)
            for x in range(4):
                if nib & (8 >> x):
                    pix[top + r][8 + x] |= 1 << plane
        pos += (h + 1) // 2
    return pix


def png(path, w, h, rows):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def main():
    rom = open(sys.argv[1], 'rb').read()
    p = int(sys.argv[3], 0)
    n = int(sys.argv[4], 0) if len(sys.argv) > 4 else 64
    cols, Z = 16, 3
    cw, ch = 14, 18
    W, H = cols * cw * Z, ((n + cols - 1) // cols) * ch * Z
    img = [[40] * W for _ in range(H)]
    shade = [0, 255, 140, 200]
    for i in range(n):
        g = glyph(rom, p, i)
        ox, oy = (i % cols) * cw + 1, (i // cols) * ch + 1
        for y in range(16):
            for x in range(12):
                v = shade[g[y][x]] if g[y][x] else 0
                for dy in range(Z):
                    for dx in range(Z):
                        img[(oy + y) * Z + dy][(ox + x) * Z + dx] = v
    png(sys.argv[2], W, H, img)


if __name__ == '__main__':
    main()
