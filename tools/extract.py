"""Dump every text block of the original ROM to script/bNNN.json (one entry per string).

    python -X utf8 tools/extract.py [--force]
Never overwrites an existing file without --force (English lives in these files).
Entry: id (bNNN_SSSS), jp, en (null until translated), notes. Block meta: n, mode, ptr.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from blocks import read_blocks
import textlib as T

ROOT = Path(__file__).resolve().parent.parent
ROM = ROOT / 'rom' / 'Shin Momotarou Densetsu (Japan) (Rev 1).sfc'


def main():
    force = '--force' in sys.argv
    refresh = '--refresh-jp' in sys.argv  # re-decode jp after a table fix, keep en
    rom = ROM.read_bytes()
    out = ROOT / 'script'
    out.mkdir(exist_ok=True)
    wrote = skipped = 0
    for b in read_blocks(rom):
        strs, tail = T.split_strings(b['data'])
        path = out / ('b%03d.json' % b['n'])
        if path.exists() and refresh:
            doc = json.loads(path.read_text(encoding='utf-8'))
            for e, s in zip(doc['strings'], strs):
                e['jp'] = T.decode(s)
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(doc, f, ensure_ascii=False, indent=1)
                f.write('\n')
            wrote += 1
            continue
        if path.exists() and not force:
            skipped += 1
            continue
        doc = dict(block=b['n'], mode=b['mode'], ptr='%06X' % b['ptr'], tail=T.decode(tail),
                   strings=[dict(id='b%03d_%04d' % (b['n'], i), jp=T.decode(s), en=None) for i, s in enumerate(strs)])
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
            f.write('\n')
        wrote += 1
    print(f'wrote {wrote}, kept {skipped} existing')
    win = out / 'win.json'
    if force or not win.exists():
        import winscript
        rows = winscript.extract(rom)
        with open(win, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(dict(note='window-script text runs: en <= 2*cells chars, padded by the build',
                           runs=rows), f, ensure_ascii=False, indent=1)
            f.write('\n')
        print(f'win.json: {len(rows)} runs')


if __name__ == '__main__':
    main()
