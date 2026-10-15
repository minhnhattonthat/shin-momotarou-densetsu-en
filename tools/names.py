"""Write docs/names.tsv: approved English for every name block entry (places, characters, monsters, items,
equipment, Arts), so dialogue translators reuse the same forms.  python -X utf8 tools/names.py
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCKS = {3: 'place', 4: 'character', 6: 'monster', 8: 'item', 9: 'equipment', 10: 'art'}


def main():
    seen = set()
    rows = ['kind\tjapanese\tenglish']
    subs = {0xA0 + i: s['jp'] for i, s in
            enumerate(json.loads((ROOT / 'script' / 'b001.json').read_text(encoding='utf-8'))['strings'])}
    for n, kind in BLOCKS.items():
        d = json.loads((ROOT / 'script' / ('b%03d.json' % n)).read_text(encoding='utf-8'))
        for s in d['strings']:
            if s.get('en') is None:
                continue
            jp = re.sub(r'\{sub:([0-9A-F]{2})\}', lambda m: subs.get(int(m[1], 16), ''), s['jp'])
            jp = jp.replace('{kata}', '').replace('{hira}', '')
            if not jp.strip() or (jp, s['en']) in seen or 'Spare' in s['en']:
                continue
            seen.add((jp, s['en']))
            rows.append(f"{kind}\t{jp}\t{s['en']}")
    (ROOT / 'docs' / 'names.tsv').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    print(len(rows) - 1, 'names')


if __name__ == '__main__':
    main()
