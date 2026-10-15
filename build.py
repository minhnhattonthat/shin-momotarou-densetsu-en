"""Build the English ROM.

    python -X utf8 build.py [--marker] [--out build/smd_en.sfc] [--only 1,5,28]
Blocks with any English (or all blocks with --marker) are re-encoded, LZSS-compressed and placed in the
expanded area (file 0x200000+, banks E0-FF); untouched blocks keep their original bytes and pointers.
With no English and no --marker, the output is byte-identical to the original ROM (identity build).
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import textlib as T
from comp import block_ptrs, lzss_encode, TABLE
from en import encode_en, text_width
import fontgen
import kinds
import patches
import winscript
from wrap import wrap_text

ROM = ROOT / 'rom' / 'Shin Momotarou Densetsu (Japan) (Rev 1).sfc'
EXP_BASE = 0x200000
EXP_END = 0x400000


QA = {}  # id -> English, from --qa


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
    orig = bytes(rom[:0x200000])
    for start, (end, ents) in sorted(winscript.regions(orig).items()):
        rid = winscript.region_id(start)
        if not any(k.startswith(rid + '_') for k in en):
            continue
        blob = winscript.rebuild(orig, start, en, encode_en)
        if (pos & 0xFFFF) + len(blob) > 0x10000:  # keep a script inside one bank (16-bit body index)
            pos = (pos | 0xFFFF) + 1
        rom[pos:pos + len(blob)] = blob
        for tgt, lo_site, bank_site in ents:
            addr = 0xC00000 | (pos + tgt - start)
            rom[lo_site:lo_site + 2] = (addr & 0xFFFF).to_bytes(2, 'little')
            rom[bank_site] = addr >> 16
        pos += len(blob)
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
                en = wrap_text(s['en']) if kinds.kind(n) == 'dlg' else s['en']
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
    pos = insert_windows(rom, pos)
    fontgen.build_font(rom)
    patches.apply(rom)
    print(f'blocks re-encoded: {len(changed)}; expanded area used: {pos - EXP_BASE:#x} bytes')
    return bytes(rom)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--marker', action='store_true')
    ap.add_argument('--out', default=str(ROOT / 'build' / 'smd_en.sfc'))
    ap.add_argument('--only', default='')
    ap.add_argument('--qa', action='append', default=[], help='ID=English override (stress tests)')
    a = ap.parse_args()
    only = {int(x) for x in a.only.split(',') if x}
    QA.update(q.split('=', 1) for q in a.qa)
    data = build(a.marker, a.out, only)
    Path(a.out).parent.mkdir(exist_ok=True)
    Path(a.out).write_bytes(data)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
