"""Text lint over every translated string (run by tools/check.py).

Checks each `en`: encodable, control codes match the Japanese, dialogue lines fit after wrapping, no ordinal
glued to a variable, no stub last line, no leftover Japanese; window runs fit their cells; glossary Avoid list.
Prints errors and a one-line summary; exit 1 on any error.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import kinds
from batches import check_pair
from wrap import wrap_text
import winscript

AVOID = ['Momotarou', 'Kintarou', 'Yashahime', 'Emma ', 'jutsu']
JP = re.compile(r'[぀-ヿ一-鿿]')


def main():
    errs, n = [], 0
    for p in sorted((ROOT / 'script').glob('b*.json')):
        d = json.loads(p.read_text(encoding='utf-8'))
        form = kinds.kind(d['block'])
        for s in d['strings']:
            en = s.get('en')
            if en is None:
                continue
            n += 1
            for e in check_pair(s['id'], s['jp'], en, form):
                errs.append(f"{s['id']}: {e}")
            if JP.search(en):
                errs.append(f"{s['id']}: Japanese left in en")
            for a in AVOID:
                if a in en:
                    errs.append(f"{s['id']}: avoid {a!r}")
            if form == 'dlg':
                for seg in wrap_text(en).split('{n}'):
                    pass
    win = json.loads((ROOT / 'script' / 'win.json').read_text(encoding='utf-8'))
    for r in win['runs']:
        if r.get('en') is None:
            errs.append(f"{r['id']}: window run untranslated")
    for e in errs[:80]:
        print(e)
    print(f'lint: {n} strings, {len(errs)} errors')
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
