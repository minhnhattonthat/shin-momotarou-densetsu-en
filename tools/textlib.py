"""Japanese text codec for Shin Momotarou Densetsu (decode the original script; roundtrip-exact).

Byte stream (after block decompression):
  00 end | 01 newline | 02 XX sub-string (block 1, string XX-A0) | 03 hiragana mode | 04 katakana mode
  05-08 colour | 09 party name | 0A number | 0B-12 box/flow codes | 18-1F XX kanji (2 bytes)
  50-8F page 1 (digits, A-Z, punctuation) | 90-BE kana | D0-E7 voiced kana | F0-F9 small kana
Other bytes below 50 decode as [XX]. Katakana mode changes how 90-FF read.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PAGE1 = (' 0123456789?!、。…'
         '・ABCDEFGHIJKLMNO'
         'PQRSTUVWXYZ()「」～'
         'ー※©＋－／㎏→←〈〉『』㎝♪■')
HIRA = 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんで'
KATA = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンデ'
HIRA_V = 'がぎぐげござじずぜぞだぢづどばびぶべぼぱぴぷぺぽ'
KATA_V = 'ガギグゲゴザジズゼゾダヂヅドバビブベボパピプペポ'
HIRA_S = 'ぁぃぅぇぉっゃゅょゎ'
KATA_S = 'ァィゥェォッャュョヮ'

CTRL = {0x00: 'end', 0x01: 'n', 0x03: 'hira', 0x04: 'kata', 0x05: 'c0', 0x06: 'c1', 0x07: 'c2', 0x08: 'c3',
        0x09: 'arg', 0x0A: 'num', 0x0B: '0B', 0x0C: 'wait', 0x0D: '0D', 0x0E: '0E', 0x0F: 'page',
        0x10: '10', 0x11: 'hero', 0x12: '12'}
CTRL_ENC = {v: k for k, v in CTRL.items()}


def load_kanji():
    dec, enc = {}, {}
    for line in (ROOT / 'tbl' / 'kanji.txt').read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        base, chars = line.split(' ', 1)
        base = int(base, 16)
        for i, ch in enumerate(chars):
            code = base + i
            if ch == '□':
                s = '{g%04X}' % code
            elif ch in enc:
                s = ch + "'"
                while s in enc:
                    s += "'"
            else:
                s = ch
            dec[code] = s
            enc[s] = code
    return dec, enc


KDEC, KENC = load_kanji()


def _single(b, kata):
    if 0x50 <= b <= 0x8F:
        return PAGE1[b - 0x50]
    if 0x90 <= b <= 0xBE:
        return (KATA if kata else HIRA)[b - 0x90]
    if 0xD0 <= b <= 0xE7:
        return (KATA_V if kata else HIRA_V)[b - 0xD0]
    if 0xF0 <= b <= 0xF9:
        return (KATA_S if kata else HIRA_S)[b - 0xF0]
    return None


def decode(data):
    """bytes of one string (with or without its 00) -> text. Exact inverse of encode()."""
    out, i, kata = [], 0, False
    while i < len(data):
        b = data[i]
        if 0x18 <= b <= 0x1F and i + 1 < len(data):
            code = (b << 8) | data[i + 1]
            out.append(KDEC.get(code, '{k%04X}' % code))
            i += 2
            continue
        if b == 0x02 and i + 1 < len(data):
            out.append('{sub:%02X}' % data[i + 1])
            i += 2
            continue
        if b in CTRL:
            out.append('{%s}' % CTRL[b])
            if b == 0x03:
                kata = False
            elif b == 0x04:
                kata = True
            elif b in (0x09, 0x11):
                kata = False  # the game clears katakana mode after a name
            i += 1
            continue
        ch = _single(b, kata)
        if ch is None:
            out.append('[%02X]' % b)
        else:
            out.append(ch)
        i += 1
    return ''.join(out)


_REV = {}
for _i, _c in enumerate(PAGE1):
    _REV.setdefault((_c, None), 0x50 + _i)
for _tab, _base in ((HIRA, 0x90), (HIRA_V, 0xD0), (HIRA_S, 0xF0)):
    for _i, _c in enumerate(_tab):
        _REV[(_c, False)] = _base + _i
for _tab, _base in ((KATA, 0x90), (KATA_V, 0xD0), (KATA_S, 0xF0)):
    for _i, _c in enumerate(_tab):
        _REV[(_c, True)] = _base + _i


def encode(text):
    """JP text -> bytes (mode codes must already be present, as decode() writes them)."""
    out, i, kata = bytearray(), 0, False
    while i < len(text):
        c = text[i]
        if c == '{':
            j = text.index('}', i)
            tok = text[i + 1:j]
            i = j + 1
            if tok.startswith('sub:'):
                out += bytes([0x02, int(tok[4:], 16)])
            elif tok.startswith('k') and len(tok) == 5 and tok[0] == 'k':
                out += int(tok[1:], 16).to_bytes(2, 'big')
            elif tok.startswith('g') and len(tok) == 5:
                out += int(tok[1:], 16).to_bytes(2, 'big')
            else:
                b = CTRL_ENC[tok]
                out.append(b)
                if b == 0x03:
                    kata = False
                elif b == 0x04:
                    kata = True
                elif b in (0x09, 0x11):
                    kata = False
            continue
        if c == '[':
            out.append(int(text[i + 1:i + 3], 16))
            i += 4
            continue
        # kanji (possibly with trailing primes)
        k = c
        while i + len(k) < len(text) and text[i + len(k)] == "'":
            k += "'"
        if k in KENC:
            out += KENC[k].to_bytes(2, 'big')
            i += len(k)
            continue
        if (c, None) in _REV:
            out.append(_REV[(c, None)])
        else:
            out.append(_REV[(c, kata)])
        i += 1
    return bytes(out)


def split_strings(data):
    """Split a block's plain stream into strings (each without its 00) and the trailing bytes after the last 00.
    Kanji second bytes and 02 arguments never terminate a string."""
    strs, cur, i = [], bytearray(), 0
    while i < len(data):
        b = data[i]
        if (0x18 <= b <= 0x1F or b == 0x02) and i + 1 < len(data):
            cur += data[i:i + 2]
            i += 2
            continue
        if b == 0x00:
            strs.append(bytes(cur))
            cur = bytearray()
        else:
            cur.append(b)
        i += 1
    return strs, bytes(cur)
