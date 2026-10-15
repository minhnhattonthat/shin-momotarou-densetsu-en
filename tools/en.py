"""English encoder + pixel widths (codes from fontgen.EN_PAGE1/EN_PAGE2; control tokens as in textlib).

    from en import encode_en, text_width
"""
import re
from fontgen import EN_PAGE1, EN_PAGE2, advances
from textlib import CTRL_ENC

CODE = {}
for _i, _c in enumerate(EN_PAGE1):
    CODE.setdefault(_c, 0x50 + _i)
for _i, _c in enumerate(EN_PAGE2):
    CODE.setdefault(_c, 0x90 + _i)
ADV = advances()
TOKEN = re.compile(r'\{([^}]*)\}|\[([0-9A-F]{2})\]')
# width assumed for expansions when fitting (names come from block 1; the lint uses the real longest value)
EXPANSION_PX = {'arg': 48, 'num': 30, 'hero': 56}


class EncodeError(ValueError):
    pass


def encode_en(text):
    out = bytearray()
    i = 0
    while i < len(text):
        c = text[i]
        m = TOKEN.match(text, i) if c in '{[' else None
        if c == '{' or m:
            if not m:
                raise EncodeError(f'bad token at {i}: {text[i:i+12]!r}')
            if m[1] is not None:
                tok = m[1]
                if tok.startswith('sub:'):
                    out += bytes([0x02, int(tok[4:], 16)])
                elif tok[0] in 'kg' and len(tok) == 5:
                    out += int(tok[1:], 16).to_bytes(2, 'big')
                elif tok in CTRL_ENC:
                    out.append(CTRL_ENC[tok])
                else:
                    raise EncodeError(f'unknown control {{{tok}}}')
            else:
                out.append(int(m[2], 16))
            i = m.end()
            continue
        if c not in CODE:
            raise EncodeError(f'unencodable {c!r}')
        out.append(CODE[c])
        i += 1
    return bytes(out)


def text_width(line, sub_px=None):
    """Pixel width of one line (no {n}). sub_px: {sub index: px} for {sub:XX} names."""
    w, i = 0, 0
    while i < len(line):
        m = TOKEN.match(line, i) if line[i] in '{[' else None
        if m:
            tok = m[1] or ''
            if tok.startswith('sub:'):
                w += (sub_px or {}).get(int(tok[4:], 16), 60)
            elif tok in EXPANSION_PX:
                w += EXPANSION_PX[tok]
            elif tok[:1] in 'kg' and len(tok) == 5:
                w += 12
            i = m.end()
            continue
        w += ADV.get(line[i], 8)
        i += 1
    return w
