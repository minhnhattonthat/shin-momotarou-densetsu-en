"""Window scripts (menus, labels): header commands + body text, run by 84:B806 (header) / 84:B983 (body).

Loaded by code as an immediate 24-bit pointer:  REP #$20  LDA #lo/hi  STA $B9  SEP #$20  LDA #bank  STA $BB
(bytes A9 lo hi 85 B9 E2 20 A9 bk 85 BB). Header commands (first byte matched against 84:B871):
  31 +1, 32 x y, 33 +3, 34 +3, 35 +2, 36, 37, 38 +3 (ptr), 39 +3, 3A +1.
Body (fixed-cell mode, $12CD |= 2; one Japanese cell = 12 px = two 6 px English cells):
  00 end, 01 newline, 18-1F XX kanji, 20 XX, 21 XX special (21 53/44/64/5A/4E/49 take one more byte:
  string / number variables with a field length), 22/23 a a (if), 24-29 a a v, 2A a a v v, 2B else / 2C endif,
  03/04 kana mode, 05-08 colour, 50-FF characters.
Text runs (consecutive characters) are what gets translated: English is padded to exactly 2 x the run's cells so
columns stay aligned.
"""
import re
import textlib as T

LOADER = re.compile(rb'\xa9(..)\x85\xb9\xe2\x20\xa9(.)\x85\xbb', re.S)
HDR = {0x31: 1, 0x32: 2, 0x33: 3, 0x34: 3, 0x35: 2, 0x36: 0, 0x37: 0, 0x38: 3, 0x39: 3, 0x3A: 1}
BODY_ARGS = {0x20: 1, 0x22: 2, 0x23: 2, 0x24: 3, 0x25: 3, 0x26: 3, 0x27: 3, 0x28: 3, 0x29: 3, 0x2A: 4}
SPECIAL_WITH_ARG = {0x53, 0x44, 0x64, 0x5A, 0x4E, 0x49}
EOL_SLACK = 8  # a run that ends its line may grow the window by this many 6 px cells (QA-checked)


def loaders(rom):
    """[(offset of lo/hi operand, offset of bank operand, target file offset)]"""
    out = []
    for m in LOADER.finditer(rom):
        lo = int.from_bytes(m.group(1), 'little')
        bank = m.group(2)[0]
        if bank >= 0xC0 or (bank < 0x40 or 0x80 <= bank < 0xC0) and lo >= 0x8000:
            addr = (bank << 16) | lo
            out.append((m.start() + 1, m.start() + 8, addr & 0x3FFFFF))
    return out


def tokens(rom, off):
    """Parse one script: (header bytes, body tokens [(kind, bytes)], end offset). kind: chr / mode / code / end."""
    i = off
    while rom[i] in HDR:
        i += 1 + HDR[rom[i]]
    hdr = bytes(rom[off:i])
    toks = []
    while True:
        b = rom[i]
        if b == 0x00:
            toks.append(('end', b'\x00'))
            return hdr, toks, i + 1
        if 0x18 <= b <= 0x1F:
            toks.append(('chr', bytes(rom[i:i + 2]))); i += 2; continue
        if b >= 0x50:
            toks.append(('chr', bytes([b]))); i += 1; continue
        if b in (0x03, 0x04):
            toks.append(('mode', bytes([b]))); i += 1; continue
        n = BODY_ARGS.get(b, 0)
        if b == 0x21:
            n = 2 if rom[i + 1] in SPECIAL_WITH_ARG else 1
        toks.append(('code', bytes(rom[i:i + 1 + n])))
        i += 1 + n


def runs(toks):
    """Group tokens into [('txt', [tokens]) | ('raw', token)]; mode codes inside a text run belong to the run."""
    out = []
    cur = None
    for k, b in toks:
        if k in ('chr', 'mode'):
            if cur is None:
                cur = []
                out.append(('txt', cur))
            cur.append((k, b))
        else:
            cur = None
            out.append(('raw', (k, b)))
    return out


def run_cells(run):
    return sum(1 for k, b in run if k == 'chr')


def run_jp(run):
    return T.decode(b''.join(b for k, b in run))


def regions(rom):
    """Scripts grouped by end offset: {start: (end, [entry offsets], [loader sites])}."""
    by_end = {}
    for lo_site, bank_site, tgt in loaders(rom):
        try:
            _, _, end = tokens(rom, tgt)
        except IndexError:
            continue
        by_end.setdefault(end, []).append((tgt, lo_site, bank_site))
    out = {}
    for end, ents in by_end.items():
        start = min(t for t, _, _ in ents)
        out[start] = (end, ents)
    return out


def region_id(start):
    return 'w%05X' % start


def extract(rom):
    """[{id, jp, cells}] for every text run that holds something other than spaces."""
    rows = []
    for start, (end, ents) in sorted(regions(rom).items()):
        _, toks, _ = tokens(rom, start)
        for k, (kind, r) in enumerate(runs(toks)):
            if kind == 'txt':
                jp = run_jp(r)
                if jp.replace(' ', '').replace('{kata}', '').replace('{hira}', ''):
                    rows.append(dict(id='%s_%02d' % (region_id(start), k), jp=jp, cells=run_cells(r), en=None))
    return rows


def en_run(jp, cells, en, slack=0):
    """English for a run: Japanese leading spaces doubled, then the label, padded to 2 x cells.
    slack: extra chars allowed for a run that ends its line (the window grows to its longest line)."""
    # Window mode: code 50 (' ') keeps a 12 px cell, every English glyph and the narrow blank \xa0 take 6 px.
    if en.startswith('^'):  # exact text, no lead/limit: the line may grow (single-line or end-aligned windows)
        lead, label = 0, en[1:].replace(' ', '\xa0')
        slack = 10 ** 6
    else:
        lead = len(jp) - len(jp.lstrip(' '))
        label = en.replace(' ', '\xa0')
    room = 12 * cells - 12 * lead - 6 * len(label)
    if room < -6 * slack:
        raise ValueError(f'{en!r} longer than {2 * (cells - lead)} chars')
    room = max(room, 0)
    return ' ' * lead + label + ' ' * (room // 12) + '\xa0' * (room % 12 // 6)


def rebuild(rom, start, en_by_id, encode_en):
    """New bytes for the script region at `start` with English runs (untranslated runs stay Japanese)."""
    hdr, toks, end = tokens(rom, start)
    out = bytearray(rom[start:start + len(hdr)])
    rl = runs(toks)
    for k, (kind, r) in enumerate(rl):
        j = k + 1
        while j < len(rl) and rl[j][0] == 'raw' and rl[j][1][1][0] in (0x2B, 0x2C, 0x05, 0x06, 0x07, 0x08):
            j += 1
        eol = j < len(rl) and rl[j][0] == 'raw' and rl[j][1][1][0] in (0x00, 0x01)
        if kind == 'raw':
            out += r[1]
            continue
        rid = '%s_%02d' % (region_id(start), k)
        en = en_by_id.get(rid)
        jp = run_jp(r)
        if en is None and not jp.replace(' ', '').replace('{kata}', '').replace('{hira}', ''):
            en = ''  # space-only run: double it
        if en is None:
            out += b''.join(b for kk, b in r)
        else:
            out += encode_en(en_run(jp.replace('{kata}', '').replace('{hira}', ''), run_cells(r), en,
                                    EOL_SLACK if eol else 0))
    # Menu code finds per-slot data (handler pointers etc.) right after the script's 00: copy it along.
    out += rom[end:end + trailer_len(rom, start)]
    return bytes(out)


def trailer_len(rom, start):
    """Bytes after the terminator that travel with a relocated script: 3 per cursor slot (handler pointers)."""
    _, toks, end = tokens(rom, start)
    slots = sum(1 for k, b in toks if k == 'code' and b == b'\x21\x3e')
    return 3 * slots
