"""Window scripts (menus, labels): header commands + body text, run by 84:B806 (header) / 84:B983 (body).

Loaded by code as an immediate 24-bit pointer:  REP #$20  LDA #lo/hi  STA $B9  SEP #$20  LDA #bank  STA $BB
(bytes A9 lo hi 85 B9 E2 20 A9 bk 85 BB). Header commands (first byte matched against 84:B871):
  31 +1, 32 x y, 33 +3, 34 +3, 35 +2, 36, 37, 38 +3 (ptr), 39 +3, 3A +1.
Body (fixed 12 px mode, $12CD |= 2): 00 end, 01 newline, 18-1F XX kanji, 20 XX (space), 21 XX special
glyph (21 4E takes one more byte), 22/23 a a (if byte at addr), 24-29 a a v, 2A a a v v, 2B / 2C markers,
50-FF characters, 03/04 kana mode, 05-08 colour.
"""
import re

LOADER = re.compile(rb'\xa9(..)\x85\xb9\xe2\x20\xa9(.)\x85\xbb', re.S)
HDR = {0x31: 1, 0x32: 2, 0x33: 3, 0x34: 3, 0x35: 2, 0x36: 0, 0x37: 0, 0x38: 3, 0x39: 3, 0x3A: 1}
BODY_ARGS = {0x02: 1, 0x20: 1, 0x22: 2, 0x23: 2, 0x24: 3, 0x25: 3, 0x26: 3, 0x27: 3, 0x28: 3, 0x29: 3, 0x2A: 4}


def loaders(rom):
    """[(site offset of the LDA #lo/hi operand, target file offset)]"""
    out = []
    for m in LOADER.finditer(rom):
        lo = int.from_bytes(m.group(1), 'little')
        bank = m.group(2)[0]
        addr = (bank << 16) | lo
        if bank & 0x40 or lo >= 0x8000:  # ROM: bank C0+ or upper half
            out.append((m.start() + 1, m.start() + 8, addr & 0x3FFFFF))
    return out


def parse(rom, off, maxlen=2000):
    """Returns (header bytes, list of body tokens (kind, bytes), end offset). kind: 'txt' run or 'code'."""
    i = off
    while rom[i] in HDR:
        i += 1 + HDR[rom[i]]
    hdr = bytes(rom[off:i])
    toks = []
    start = i
    while True:
        if i - start > maxlen:
            raise ValueError('no end')
        b = rom[i]
        if b == 0x00:
            toks.append(('end', b'\x00'))
            i += 1
            break
        if 0x18 <= b <= 0x1F:
            toks.append(('chr', bytes(rom[i:i + 2]))); i += 2; continue
        if b >= 0x50:
            toks.append(('chr', bytes([b]))); i += 1; continue
        n = BODY_ARGS.get(b, 0)
        if b == 0x21:
            n = 2 if rom[i + 1] == 0x4E else 1
        toks.append(('code', bytes(rom[i:i + 1 + n])))
        i += 1 + n
    return hdr, toks, i
