"""Build the English ROM.

    python -X utf8 build.py [--marker] [--out build/smd_en.sfc] [--only 1,5,28]
Blocks with any English (or all blocks with --marker) are re-encoded, LZSS-compressed and placed in the
expanded area (file 0x200000+, banks E0-FF); untouched blocks keep their original bytes and pointers.
With no English and no --marker, the output is byte-identical to the original ROM (identity build).
"""
import argparse, json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import textlib as T
from comp import block_ptrs, lzss_encode, TABLE
from en import encode_en, text_width
import fontgen
import gfx
import kinds
import patches
import winscript
from wrap import wrap_text

ROM = ROOT / 'rom' / 'Shin Momotarou Densetsu (Japan) (Rev 1).sfc'
EXP_BASE = 0x200000
EXP_END = 0x400000


QA = {}  # id -> English, from --qa
NO_WIN = False
SKIP = set(os.environ.get('SMD_SKIP', '').split(','))  # debugging: gfx,namevar,measure,fixed12
WIN_ONLY = set()
RESERVED = (0x4F15C, 0x4F240)  # VWF width tables (fontgen.WIDTH_FREE) + patches.FIXED12_CODE
WINMAP = {}  # window region id -> CPU address in the built ROM (written next to the ROM for tools/debug)


def load_script():
    docs = {}
    for p in sorted((ROOT / 'script').glob('b*.json')):
        d = json.loads(p.read_text(encoding='utf-8'))
        for s in d['strings']:
            if s['id'] in QA:
                s['en'] = QA[s['id']]
        docs[d['block']] = d
    return docs


SEG = re.compile(r'(\{[^}]*\}|\[[0-9A-F]{2}\])')


def marker(sid, jp):
    """Keep every control token; replace the text between them with the id, then filler of a similar width."""
    parts = SEG.split(jp)
    out, first = [], True
    blk, idx = sid[1:4].lstrip('0'), sid[5:].lstrip('0') or '0'
    for p in parts:
        if not p:
            continue
        if SEG.fullmatch(p):
            out.append('' if p.startswith('[') or p in ('{kata}', '{hira}') else p)
            continue
        if first:
            out.append(f'{blk}.{idx}')
            first = False
            continue
        n = max(1, len(p))
        out.append(('Lorem ipsum dolor sit amet consectetur ' * 4)[:n * 2].rstrip())
    return ''.join(out)


def insert_windows(rom, pos):
    """Relocate every window script that has English to the expanded area and repoint its loaders."""
    doc = json.loads((ROOT / 'script' / 'win.json').read_text(encoding='utf-8'))
    en = {r['id']: r['en'] for r in doc['runs'] if r.get('en') is not None}
    en.update({k: v for k, v in QA.items() if k.startswith('w')})
    if WIN_ONLY:
        en = {k: v for k, v in en.items() if k.split('_')[0] in WIN_ONLY}
    # Scripts must stay in their own 64 KB bank (menu code reaches per-menu data through the script's bank), and
    # in the upper half when the code addresses them through a $8x bank (lower half = WRAM/IO there).
    orig = bytes(rom[:0x200000])
    regs = winscript.regions(orig)
    blobs = {}
    for start, (end, ents) in regs.items():
        rid = winscript.region_id(start)
        if any(k.startswith(rid + '_') for k in en):
            blobs[start] = winscript.rebuild(orig, start, en, encode_en)
    free = {}  # bank -> [[lo, hi)] free spans
    for start in blobs:
        free.setdefault(start >> 16, []).append([start, regs[start][0]])
    for bank in list(free):
        lo, i = bank << 16, bank << 16
        while i < lo + 0x10000:
            if orig[i] == 0xFF:
                j = i
                while j < lo + 0x10000 and orig[j] == 0xFF:
                    j += 1
                if j - i >= 32:
                    free[bank].append([i + 8, j])  # keep a few FF bytes as a guard after data
                i = j
            else:
                i += 1
        cut = []
        for s in free[bank]:
            if s[0] < RESERVED[1] and s[1] > RESERVED[0]:
                if s[0] < RESERVED[0]:
                    cut.append([s[0], RESERVED[0]])
                if s[1] > RESERVED[1] + 8:
                    cut.append([RESERVED[1] + 8, s[1]])
            else:
                cut.append(s)
        free[bank] = cut
    for start in sorted(blobs, key=lambda s: -len(blobs[s])):
        end, ents = regs[start]
        blob = blobs[start]
        upper = any(orig[bs] < 0xC0 for _, _, bs in ents)
        bank = start >> 16
        spans = sorted(free[bank], key=lambda s: s[1] - s[0])
        for s in spans:
            a = max(s[0], (bank << 16) | 0x8000) if upper else s[0]
            if s[1] - a >= len(blob):
                break
        else:
            raise SystemExit(f'window {winscript.region_id(start)}: no room in bank {bank:02X} ({len(blob)} bytes)')
        rom[a:a + len(blob)] = blob
        if a > s[0]:
            free[bank].append([s[0], a])
        s[0] = a + len(blob)
        rid = winscript.region_id(start)
        for tgt, lo_site, bank_site in ents:
            addr = (a + tgt - start) & 0xFFFF
            rom[lo_site:lo_site + 2] = addr.to_bytes(2, 'little')
            rom[bank_site] = (orig[bank_site] & 0xC0) | bank
        WINMAP[rid] = (0x80 | bank) << 16 | (a & 0xFFFF) if upper else 0xC00000 | a
    return pos


def build(marker_mode=False, out_path=None, only=None):
    rom = bytearray(ROM.read_bytes())
    docs = load_script()
    changed = {}
    for n, d in docs.items():
        if only and n not in only:
            continue
        has_en = any(s.get('en') is not None for s in d['strings'])
        if not (has_en or marker_mode):
            continue
        plain = bytearray()
        for s in d['strings']:
            if marker_mode and s.get('en') is None:
                txt = marker(s['id'], s['jp'])
                plain += encode_en(txt)
            elif s.get('en') is not None:
                # names print in 12 px window mode, where code 50 keeps a full Japanese cell: use the 6 px blank
                en = wrap_text(s['en']) if kinds.kind(n) == 'dlg' else s['en'].replace(' ', '\xa0')
                plain += encode_en(en)
            else:
                plain += T.encode(s['jp'])
            plain.append(0)
        changed[n] = bytes(plain)
    if not changed:
        return bytes(rom)
    # expand to 4 MB HiROM
    rom += b'\xff' * (EXP_END - len(rom))
    rom[0xFFD7] = 0x0C
    pos = EXP_BASE
    for n in sorted(changed):
        comp = lzss_encode(changed[n])
        blob = b'\x01' + comp + b'\x00\x00'  # 2 pad bytes: the decoder may peek past the last item
        if pos + len(blob) > EXP_END:
            raise SystemExit('expanded area full')
        rom[pos:pos + len(blob)] = blob
        ptr = 0xC00000 | pos
        rom[TABLE + 3 * (n - 1):TABLE + 3 * n] = ptr.to_bytes(3, 'little')
        pos += len(blob)
    if not NO_WIN:
        pos = insert_windows(rom, pos)
    if 'gfx' not in SKIP:
        pos = gfx.apply(rom, pos)
    fontgen.build_font(rom)
    patches.apply(rom, SKIP)
    print(f'blocks re-encoded: {len(changed)}; expanded area used: {pos - EXP_BASE:#x} bytes')
    return bytes(rom)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--marker', action='store_true')
    ap.add_argument('--out', default=str(ROOT / 'build' / 'smd_en.sfc'))
    ap.add_argument('--only', default='')
    ap.add_argument('--qa', action='append', default=[], help='ID=English override (stress tests)')
    ap.add_argument('--no-win', action='store_true', help='leave window scripts Japanese (debugging)')
    ap.add_argument('--win-only', default='', help='comma list of window regions to translate (debugging)')
    a = ap.parse_args()
    global NO_WIN, WIN_ONLY
    NO_WIN = a.no_win
    WIN_ONLY = set(x for x in a.win_only.split(',') if x)
    only = {int(x) for x in a.only.split(',') if x}
    QA.update(q.split('=', 1) for q in a.qa)
    data = build(a.marker, a.out, only)
    Path(a.out).parent.mkdir(exist_ok=True)
    Path(a.out).write_bytes(data)
    Path(a.out).with_suffix('.winmap.json').write_text(json.dumps(WINMAP, indent=1), encoding='utf-8')
    print('wrote', a.out)


if __name__ == '__main__':
    main()
