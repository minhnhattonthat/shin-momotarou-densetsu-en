"""Consistency pass over script/*.json English: apply the controller's term rulings (regex -> replacement).

    python -X utf8 tools/consistency.py [--dry]
Rules are data here so the pass is repeatable after later merges.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = [
    (r'\bOni (?:Path|Way|Art)\b(?!s)', 'Oni Arts'),          # 鬼道
    (r'\bLady Karura\b', 'Lord Karura'),
    (r'\bRumble, rumble\b', 'Gwarari, gwarari'),           # Raijin's ぐゎらり
    (r'\bBlue Meteorite\b', 'Blue Meteor'),                # 青き隕星
    (r'\bLightning Sage\b', 'Bolt Sage'),                  # 稲妻仙人
    (r"\bMomotaro's Old Man\b", "Momotaro's Grandpa"),
    (r"\bMomotaro's Old Woman\b", "Momotaro's Grandma"),
]


def main():
    dry = '--dry' in sys.argv
    total = 0
    for p in sorted((ROOT / 'script').glob('b*.json')):
        d = json.loads(p.read_text(encoding='utf-8'))
        changed = False
        for s in d['strings']:
            en = s.get('en')
            if not en:
                continue
            new = en
            for pat, rep in RULES:
                new = re.sub(pat, rep, new)
            if new != en:
                total += 1
                if dry:
                    print(s['id'], en[:60], '->', new[:60])
                s['en'] = new
                changed = True
        if changed and not dry:
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
                f.write('\n')
    print(f'consistency: {total} strings changed' + (' (dry run)' if dry else ''))


if __name__ == '__main__':
    main()
