"""Guess each kanji glyph of the game font by matching it against MS Gothic 12 px renders (recon helper).

    python -X utf8 tools/kanji_match.py rom/smd.sfc work/kanji_guess.tsv
Writes code<TAB>best<TAB>score<TAB>top5 for pages 8..22 (codes 1800+). Verify the result by eye (kanji_sheet.py).
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, __file__.rsplit('\\', 1)[0].rsplit('/', 1)[0])
import fontdump

FONT = r'C:\Windows\Fonts\msgothic.ttc'
BOLD = False  # plane 1 holds the 1 px strokes; plane 0 adds the shadow outline


def candidates():
    out = []
    for hi in range(0x88, 0xEB):
        for lo in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
            try:
                ch = bytes([hi, lo]).decode('cp932')
            except UnicodeDecodeError:
                continue
            if '\u4e00' <= ch <= '\u9fff' or ch in '々〆ヶ':
                out.append(ch)
    return out


def render(ch, font):
    im = Image.new('L', (16, 16), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    d.text((0, 0), ch, font=font, fill=255)
    a = (np.array(im) > 127).astype(np.float32)
    if BOLD:
        a = np.maximum(a, np.roll(a, 1, 1))  # the game font is bold: 2 px vertical strokes
    ys, xs = np.nonzero(a)
    if len(ys) == 0:
        return None
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def norm(a, size=14):
    """Place a bitmap centred in a size x size canvas."""
    c = np.zeros((size, size), np.float32)
    h, w = min(a.shape[0], size), min(a.shape[1], size)
    oy, ox = (size - h) // 2, (size - w) // 2
    c[oy:oy + h, ox:ox + w] = a[:h, :w]
    return c


def game_bitmap(rom, p, i):
    g = fontdump.glyph(rom, p, i)
    a = np.array([[1.0 if (v & 2) else 0.0 for v in row] for row in g], np.float32)
    ys, xs = np.nonzero(a)
    if len(ys) == 0:
        return None
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def score(a, b):
    best = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            bb = np.roll(np.roll(b, dy, 0), dx, 1)
            inter = (a * bb).sum()
            s = inter / (np.sqrt(a.sum() * bb.sum()) + 1e-6)
            best = max(best, s)
    return best


def main():
    rom = open(sys.argv[1], 'rb').read()
    font = ImageFont.truetype(FONT, 12)
    cands = []
    for ch in candidates():
        r = render(ch, font)
        if r is not None:
            cands.append((ch, norm(r)))
    chars = [c for c, _ in cands]
    stack = np.stack([b for _, b in cands])  # N x 14 x 14
    shifts = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            shifts.append(np.roll(np.roll(stack, dy, 1), dx, 2))
    sums = [s.reshape(len(chars), -1).sum(1) for s in shifts]
    out = open(sys.argv[2], 'w', encoding='utf-8', newline='\n')
    for p in range(8, 23):
        for i in range(64):
            code = 0x1800 + (p - 8) * 64 + i
            g = game_bitmap(rom, p, i)
            if g is None:
                out.write(f'{code:04X}\t\t0\t\n'); continue
            a = norm(g).reshape(-1)
            best = np.zeros(len(chars))
            for s, sm in zip(shifts, sums):
                inter = s.reshape(len(chars), -1) @ a
                best = np.maximum(best, inter / (np.sqrt(a.sum() * sm) + 1e-6))
            top = np.argsort(-best)[:5]
            out.write(f'{code:04X}\t{chars[top[0]]}\t{best[top[0]]:.3f}\t' + ''.join(chars[t] for t in top) + '\n')
    out.close()


if __name__ == '__main__':
    main()
