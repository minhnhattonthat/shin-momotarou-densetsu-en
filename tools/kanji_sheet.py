"""Sheet of kanji glyphs (fill plane only) for reading them by eye; optional guesses drawn below each glyph.

    python -X utf8 tools/kanji_sheet.py rom/smd.sfc OUT.png FIRST_PAGE NPAGES [tbl/kanji.txt]
16 glyphs per row, 4 rows per page; code = 1800 + (page-8)*64 + row*16 + col.
"""
import sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, __file__.rsplit('\\', 1)[0].rsplit('/', 1)[0])
import fontdump


def main():
    rom = open(sys.argv[1], 'rb').read()
    p0, n = int(sys.argv[3]), int(sys.argv[4])
    guess = {}
    if len(sys.argv) > 5:
        for line in open(sys.argv[5], encoding='utf-8'):
            if '\t' in line:
                k, v = line.rstrip('\n').split('\t')[:2]
                guess[int(k, 16)] = v
    Z = 4
    cw, ch = 14 * Z, (16 * Z + (30 if guess else 4))
    W, H = 16 * cw + 40, n * 4 * ch
    im = Image.new('RGB', (W, H), (30, 30, 30))
    d = ImageDraw.Draw(im)
    jf = ImageFont.truetype(r'C:\Windows\Fonts\msgothic.ttc', 24)
    lf = ImageFont.truetype(r'C:\Windows\Fonts\msgothic.ttc', 12)
    for pi in range(n):
        p = p0 + pi
        for i in range(64):
            code = 0x1800 + (p - 8) * 64 + i
            g = fontdump.glyph(rom, p, i)
            ox, oy = 40 + (i % 16) * cw, (pi * 4 + i // 16) * ch
            if i % 16 == 0:
                d.text((2, oy + 20), f'{code:04X}', font=lf, fill=(200, 200, 0))
            for y in range(16):
                for x in range(12):
                    if g[y][x] & 2:
                        d.rectangle([ox + x * Z, oy + y * Z, ox + x * Z + Z - 1, oy + y * Z + Z - 1], fill=(255, 255, 255))
            if code in guess:
                d.text((ox + 12, oy + 16 * Z), guess[code], font=jf, fill=(120, 255, 120))
    im.save(sys.argv[2])


if __name__ == '__main__':
    main()
