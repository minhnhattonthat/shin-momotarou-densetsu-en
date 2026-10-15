"""Release: build, fix the SNES checksum on a copy, make + verify the BPS, write README, zip (patch + README).

    python -X utf8 tools/release.py [--version 1.0]
Writes release/shin-momotarou-densetsu_en.zip. Never publishes anything.
"""
import argparse, hashlib, subprocess, sys, zipfile, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(r'H:\translation\batch\.claude\skills\translate-retro-game\scripts')
ORIG = ROOT / 'rom' / 'Shin Momotarou Densetsu (Japan) (Rev 1).sfc'
OUT = ROOT / 'release'


def hashes(p):
    d = Path(p).read_bytes()
    return dict(size=len(d), crc32='%08X' % zlib.crc32(d), md5=hashlib.md5(d).hexdigest(), sha1=hashlib.sha1(d).hexdigest())


def run(*a):
    subprocess.run([sys.executable, '-X', 'utf8', *map(str, a)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', default='1.0')
    v = ap.parse_args().version
    OUT.mkdir(exist_ok=True)
    run(ROOT / 'build.py')
    final = OUT / 'smd_en_release.sfc'
    run(SKILL / 'bps.py', 'snes-checksum', ROOT / 'build' / 'smd_en.sfc', '--out', final)
    bps = OUT / f'Shin_Momotarou_Densetsu_EN_v{v}.bps'
    run(SKILL / 'bps.py', 'make', ORIG, final, bps)
    o, p, b = hashes(ORIG), hashes(final), hashes(bps)
    readme = (ROOT / 'docs' / 'README.release.txt').read_text(encoding='utf-8').format(
        version=v, o=o, p=p, bps=bps.name)
    (OUT / 'README.txt').write_text(readme, encoding='utf-8', newline='\r\n')
    z = OUT / 'shin-momotarou-densetsu_en.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(bps, bps.name)
        zf.write(OUT / 'README.txt', 'README.txt')
    print('patched ROM', p)
    print('patch', bps.name, 'sha1', b['sha1'], 'size', b['size'])
    print('wrote', z)


if __name__ == '__main__':
    main()
