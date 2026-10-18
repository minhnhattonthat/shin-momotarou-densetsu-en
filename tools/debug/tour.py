"""Text tour: show strings in the field text box via the text warp, several in parallel, and assemble pages.

    python -X utf8 tools/debug/tour.py [--per-block 1] [--blocks 20-250] [--jobs 4] [--rom build/smd_en.sfc]
Picks the longest English string(s) of each dialogue block (the worst case for wrapping), runs
tools/debug/warp.py-style emulator runs and writes work/qa/tour/page_NNN.png (8 strings per page, 4 box
frames each, labelled with the id). Look at every page.
"""
import argparse, json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import kinds

SKILL = Path(r'H:\translation\batch\.agents\skills\translate-retro-game')
EMU = SKILL / 'scripts' / 'emu.py'
STATE = ROOT / 'work' / 'states' / 'field_idle.mss'
ROUTE = '20 -;6 down;30 -;8 a;50 -;8 down;20 -;8 down;20 -;8 down;20 -;8 a;60 -'
OUT = ROOT / 'work' / 'qa' / 'tour'


def pick(blocks, per):
    out = []
    for p in sorted((ROOT / 'script').glob('b*.json')):
        d = json.loads(p.read_text(encoding='utf-8'))
        n = d['block']
        if n not in blocks or kinds.kind(n) != 'dlg' or n in kinds.MIRROR:
            continue
        cand = [(len(s['en'] or ''), i, s['id']) for i, s in enumerate(d['strings']) if s.get('en')]
        for _, i, sid in sorted(cand, reverse=True)[:per]:
            out.append((n, i, sid))
    return out


def run(rom, n, i, sid):
    out = OUT / sid
    if (out / 'final.png').exists():
        return out
    cmd = [sys.executable, '-X', 'utf8', str(EMU), str(rom), '--out', str(out), '--state-in', str(STATE),
           '--route-str', ROUTE, '--frames', '900', '--mash', '70', '--mash-key', 'a', '--shot-every', '35',
           '--script', str(ROOT / 'tools' / 'debug' / 'text.lua'), '--var', f'BLOCK={n}', '--var', f'INDEX={i}']
    subprocess.run(cmd, capture_output=True)
    return out


def strip(d, sid):
    """Up to 4 distinct box crops (y 128-224) after the warp, in time order."""
    frames = sorted(d.glob('f*.png'))[6:]
    crops, last = [], None
    for f in frames:
        im = Image.open(f).convert('RGB').crop((0, 128, 256, 224))
        b = im.tobytes()
        if last is not None and b == last:
            continue
        last = b
        crops.append(im)
    crops = crops[::max(1, len(crops) // 4)][:4]
    row = Image.new('RGB', (256 * 4, 96 + 12), (40, 0, 40))
    for k, im in enumerate(crops):
        row.paste(im, (k * 256, 12))
    ImageDraw.Draw(row).text((2, 0), sid, fill=(255, 255, 0))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-block', type=int, default=1)
    ap.add_argument('--blocks', default='1-250')
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--rom', default=str(ROOT / 'build' / 'smd_en.sfc'))
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.blocks.split('-'))
    items = pick(set(range(lo, hi + 1)), a.per_block)
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        dirs = list(ex.map(lambda t: run(a.rom, *t), items))
    rows = [strip(d, t[2]) for d, t in zip(dirs, items)]
    for p in range(0, len(rows), 8):
        page = Image.new('RGB', (1024, 108 * 8), (0, 0, 0))
        for k, r in enumerate(rows[p:p + 8]):
            page.paste(r, (0, k * 108))
        page.save(OUT / ('page_%03d.png' % (p // 8)))
    print(f'{len(items)} strings, {(len(rows) + 7) // 8} pages in {OUT}')


if __name__ == '__main__':
    main()
