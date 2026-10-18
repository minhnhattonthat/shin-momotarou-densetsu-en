"""Debug warp: show any text string or window script from a cold-ish start (field savestate), no playthrough.

    python -X utf8 tools/debug/warp.py text 28 2  [--rom build/smd_en.sfc] [--frames 600] [--mash 40]
    python -X utf8 tools/debug/warp.py win w1EF1E [--rom ...]
    python -X utf8 tools/debug/warp.py scene NAME        # a savestate in work/states/NAME.mss + 300 frames
Text: opens the field menu, picks Search; the game's text open (84:A0E5) is redirected to block/string.
Win: opens the field menu; the window open (84:AFB8) is redirected to the region's address in the built ROM.
Output: work/qa/warp/<kind>_<id>/sheet.png (contact sheet of changed frames). The field state
(work/states/field_idle.mss) is made from the original ROM by tools/debug/mkstates.py.
"""
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = Path(r'H:\translation\batch\.agents\skills\translate-retro-game')
EMU = SKILL / 'scripts' / 'emu.py'
STATE = ROOT / 'work' / 'states' / 'field_idle.mss'
OPEN_MENU = '20 -;6 down;30 -;8 a;50 -'
SEARCH = OPEN_MENU + ';8 down;20 -;8 down;20 -;8 down;20 -;8 a;60 -'


def run(rom, out, route, scripts, vars_, frames, mash, shot_every=20):
    cmd = [sys.executable, '-X', 'utf8', str(EMU), str(rom), '--out', str(out), '--state-in', str(STATE),
           '--route-str', route, '--shot-every', str(shot_every)]
    if frames:
        cmd += ['--frames', str(frames)]
    if mash:
        cmd += ['--mash', str(mash), '--mash-key', 'a']
    for s in scripts:
        cmd += ['--script', str(s)]
    for k, v in vars_.items():
        cmd += ['--var', f'{k}={v}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-800:], r.stderr[-800:])
        return r.returncode
    subprocess.run([sys.executable, '-X', 'utf8', str(SKILL / 'scripts' / 'sheet.py'), str(out), '--changed', '0.01',
                    '--div', '1', '--cols', '3', '--max', '12', '--from', '120', '--crop', '0,96,256,128'],
                   capture_output=True)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('kind', choices=['text', 'win', 'scene'])
    ap.add_argument('args', nargs='+')
    ap.add_argument('--rom', default=str(ROOT / 'build' / 'smd_en.sfc'))
    ap.add_argument('--frames', type=int, default=700)
    ap.add_argument('--mash', type=int, default=60)
    a = ap.parse_args()
    if a.kind == 'text':
        blk, idx = int(a.args[0]), int(a.args[1])
        out = ROOT / 'work' / 'qa' / 'warp' / f'text_{blk:03d}_{idx:04d}'
        rc = run(a.rom, out, SEARCH, [ROOT / 'tools' / 'debug' / 'text.lua'], {'BLOCK': blk, 'INDEX': idx},
                 a.frames, a.mash)
    elif a.kind == 'win':
        wmap = json.loads(Path(a.rom).with_suffix('.winmap.json').read_text(encoding='utf-8'))
        rid = a.args[0]
        out = ROOT / 'work' / 'qa' / 'warp' / f'win_{rid}'
        rc = run(a.rom, out, OPEN_MENU + ';60 -', [ROOT / 'tools' / 'debug' / 'win.lua'], {'WIN': hex(wmap[rid])},
                 0, 0, 10)
    else:
        global STATE
        STATE = ROOT / 'work' / 'states' / (a.args[0] + '.mss')
        out = ROOT / 'work' / 'qa' / 'warp' / f'scene_{a.args[0]}'
        rc = run(a.rom, out, '300 -', [], {}, 0, 0, 30)
    print(out / 'sheet.png' if not rc else 'failed')
    return rc


if __name__ == '__main__':
    sys.exit(main())
