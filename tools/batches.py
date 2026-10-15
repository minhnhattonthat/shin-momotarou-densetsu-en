"""Translation batches: split / check / merge / pairs / status.

    python -X utf8 tools/batches.py split            # work/tl/tNNN.tsv for every untranslated dlg string
    python -X utf8 tools/batches.py check tNNN       # validate work/tl/tNNN.out.tsv (prints OK or errors)
    python -X utf8 tools/batches.py merge tNNN [..]  # write checked English into script/*.json
    python -X utf8 tools/batches.py pairs tNNN       # work/tl/tNNN.pairs.txt for the reviewer
    python -X utf8 tools/batches.py status
Input TSV: id<TAB>form<TAB>limit<TAB>jp. Output TSV: id<TAB>en (one line per id, same order).
"""
import json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import kinds
from en import encode_en, EncodeError, text_width
from wrap import wrap_text, LIMIT

TL = ROOT / 'work' / 'tl'
TARGET_CHARS, TARGET_N = 3200, 110
# control tokens that must survive translation 1:1 ({n} and {sub:..} are free; kana mode codes are dropped)
KEEP = re.compile(r'\{(hero|arg|party|num|c[0-3]|0B|wait|0D|0E|page|10|12)\}|\[[0-9A-F]{2}\]')
DROP = {'{kata}', '{hira}'}


def load_docs():
    docs = {}
    for p in sorted((ROOT / 'script').glob('b*.json')):
        d = json.loads(p.read_text(encoding='utf-8'))
        docs[d['block']] = (p, d)
    return docs


def jp_len(jp):
    return len(re.sub(r'\{[^}]*\}|\[..\]', '', jp))


def split():
    TL.mkdir(parents=True, exist_ok=True)
    docs = load_docs()
    batches, cur, cur_chars = [], [], 0
    for n, (p, d) in sorted(docs.items()):
        if n in kinds.MIRROR or n in kinds.MANUAL or kinds.kind(n) != 'dlg':
            continue
        for s in d['strings']:
            if s.get('en') is not None or not re.sub(r'\{[^}]*\}|\[..\]|\s', '', s['jp']):
                continue
            L = jp_len(s['jp'])
            if cur and (cur_chars + L > TARGET_CHARS or len(cur) >= TARGET_N):
                batches.append(cur)
                cur, cur_chars = [], 0
            cur.append(s)
            cur_chars += L
    if cur:
        batches.append(cur)
    existing = sorted(TL.glob('t[0-9][0-9][0-9].tsv'))
    start = len(existing)
    for i, b in enumerate(batches):
        name = 't%03d' % (start + i)
        with open(TL / (name + '.tsv'), 'w', encoding='utf-8', newline='\n') as f:
            for s in b:
                f.write(f"{s['id']}\tdlg\t{LIMIT}px/line\t{s['jp']}\n")
    print(f'{len(batches)} batches written (t{start:03d}..t{start + len(batches) - 1:03d})')


NAME_SETS = {'n000': [3, 4], 'n001': [6], 'n002': [8, 10], 'n003': [9]}


def split_names():
    """Name batches for the fixed-cell windows: limit = 2 chars per Japanese cell of the block's longest name."""
    TL.mkdir(parents=True, exist_ok=True)
    docs = load_docs()
    subs = {i: s['jp'] for i, s in enumerate(docs[1][1]['strings'])}
    for name, blocks in NAME_SETS.items():
        with open(TL / (name + '.tsv'), 'w', encoding='utf-8', newline='\n') as f:
            for n in blocks:
                strs = docs[n][1]['strings']
                lim = 2 * max(kinds.jp_cells(s['jp'], subs) for s in strs)
                for s in strs:
                    if s.get('en') is None and re.sub(r'\{[^}]*\}|\[..\]|\s', '', s['jp']):
                        f.write(f"{s['id']}\tname\t{lim}ch\t{s['jp']}\n")
        print(TL / (name + '.tsv'))


def read_tsv(path):
    rows = []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        parts = line.split('\t')
        rows.append(parts)
    return rows


def check_pair(sid, jp, en, form='dlg'):
    errs = []
    if any(ord(c) > 126 for c in en if c != '…'):
        bad = sorted({c for c in en if ord(c) > 126 and c != '…'})
        errs.append(f'non-ASCII {bad}')
    if '\t' in en or '\\u' in en:
        errs.append('tab or \\u escape')
    for t in DROP:
        if t in en:
            errs.append(f'remove {t}')
    if '{sub:' in en:
        errs.append('write {sub:..} fragments out as English words')
    jp_t = Counter(m.group(0).replace('{party}', '{arg}') for m in KEEP.finditer(jp))
    en_t = Counter(m.group(0).replace('{party}', '{arg}') for m in KEEP.finditer(en))
    if jp_t != en_t:
        errs.append(f'control codes differ: jp {dict(jp_t)} en {dict(en_t)}')
    if re.search(r'\{(arg|num|hero)\}(st|nd|rd|th)\b', en):
        errs.append('ordinal suffix glued to a variable')
    try:
        encode_en(en)
    except EncodeError as e:
        errs.append(str(e))
        return errs
    if form == 'dlg':
        for seg in wrap_text(en).split('{n}'):
            if text_width(seg) > LIMIT:
                errs.append(f'line too wide after wrap ({text_width(seg)}px > {LIMIT}): {seg[:40]!r}')
    return errs


def check(name, quiet=False):
    inp = read_tsv(TL / (name + '.tsv'))
    outp = TL / (name + '.out.tsv')
    if not outp.exists():
        print(f'{name}: missing {outp.name}')
        return 1
    out = read_tsv(outp)
    errs = []
    ids_in = [r[0] for r in inp]
    ids_out = [r[0] for r in out]
    if ids_in != ids_out:
        miss = set(ids_in) - set(ids_out)
        extra = set(ids_out) - set(ids_in)
        dup = [k for k, v in Counter(ids_out).items() if v > 1]
        errs.append(f'ids differ: missing {sorted(miss)[:10]} extra {sorted(extra)[:10]} dup {dup[:10]}')
    jp = {r[0]: r[3] for r in inp}
    form = {r[0]: (r[1], r[2]) for r in inp}
    for r in out:
        if len(r) != 2:
            errs.append(f'{r[0]}: expected 2 columns, got {len(r)}')
            continue
        if r[0] in jp:
            f, lim = form[r[0]]
            for e in check_pair(r[0], jp[r[0]], r[1], f):
                errs.append(f'{r[0]}: {e}')
            if f == 'name':
                n = len(re.sub(r'\{[^}]*\}', '', r[1]))
                if n > int(lim[:-2]):
                    errs.append(f'{r[0]}: {n} chars > {lim}')
    if errs:
        for e in errs[:60]:
            print(e)
        print(f'{name}: {len(errs)} errors')
        return 1
    if not quiet:
        print(f'{name}: OK ({len(out)} entries)')
    return 0


def merge(names):
    docs = load_docs()
    by_id = {}
    for n, (p, d) in docs.items():
        for s in d['strings']:
            by_id[s['id']] = (n, s)
    touched = set()
    for name in names:
        if check(name, quiet=True):
            print(f'{name}: not merged')
            continue
        for sid, en in read_tsv(TL / (name + '.out.tsv')):
            n, s = by_id[sid]
            s['en'] = en
            touched.add(n)
        print(f'{name}: merged')
    # mirrors follow their source by index
    for dst, src in kinds.MIRROR.items():
        sd, dd = docs[src][1], docs[dst][1]
        for a, b in zip(sd['strings'], dd['strings']):
            if a.get('en') is not None and b.get('en') != a['en']:
                b['en'] = a['en']
                touched.add(dst)
    for n in touched:
        p, d = docs[n]
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
            f.write('\n')


def merge_win(path):
    """work/tl/win.out.tsv (id<TAB>en) -> script/win.json; the build enforces the cell limits."""
    p = ROOT / 'script' / 'win.json'
    doc = json.loads(p.read_text(encoding='utf-8'))
    en = dict(read_tsv(Path(path)))
    n = 0
    for r in doc['runs']:
        if r['id'] in en:
            r['en'] = en.pop(r['id'])
            n += 1
    if en:
        print('unknown ids:', sorted(en)[:10])
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'win.json: {n} runs merged')


def pairs(name):
    docs = load_docs()
    order, by_id = [], {}
    for n, (p, d) in sorted(docs.items()):
        for s in d['strings']:
            order.append(s['id'])
            by_id[s['id']] = s
    out = read_tsv(TL / (name + '.out.tsv'))
    en = dict((r[0], r[1]) for r in out)
    lines = []
    for sid, _ in out:
        lines.append(f">> {sid} | {by_id[sid]['jp']}")
        lines.append(f"   EN: {en[sid]}")
    (TL / (name + '.pairs.txt')).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(TL / (name + '.pairs.txt'))


def status():
    docs = load_docs()
    tot = done = 0
    for n, (p, d) in docs.items():
        for s in d['strings']:
            if not re.sub(r'\{[^}]*\}|\[..\]|\s', '', s['jp']):
                continue
            tot += 1
            done += s.get('en') is not None
    print(f'translated {done}/{tot} ({100 * done / max(tot, 1):.1f}%)')
    for f in sorted(TL.glob('t[0-9][0-9][0-9].tsv')):
        o = f.with_name(f.stem + '.out.tsv')
        print(f.stem, 'out' if o.exists() else '-')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'split':
        split()
    elif cmd == 'split-names':
        split_names()
    elif cmd == 'merge-win':
        merge_win(sys.argv[2] if len(sys.argv) > 2 else TL / 'win.out.tsv')
    elif cmd == 'check':
        sys.exit(max(check(n) for n in sys.argv[2:]))
    elif cmd == 'merge':
        merge(sys.argv[2:])
    elif cmd == 'pairs':
        pairs(sys.argv[2])
    elif cmd == 'status':
        status()
