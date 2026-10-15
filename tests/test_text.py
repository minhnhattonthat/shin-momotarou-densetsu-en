"""Extraction roundtrip and compression tests against the original ROM."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import textlib as T
from blocks import read_blocks
from comp import lzss_encode, lzss_decode_upto

ROM = (ROOT / 'rom' / 'Shin Momotarou Densetsu (Japan) (Rev 1).sfc').read_bytes()
BLOCKS = read_blocks(ROM)


def test_rom_hash():
    import hashlib
    assert hashlib.sha1(ROM).hexdigest() == 'a9e0b5e6b0479871792f8b44f032b71fdb8f12b4'


def test_roundtrip_every_string():
    for b in BLOCKS:
        strs, tail = T.split_strings(b['data'])
        assert b'\x00'.join(strs) + (b'\x00' if strs else b'') + tail == b['data']
        for s in strs:
            assert T.encode(T.decode(s)) == s


def test_script_matches_rom():
    for b in BLOCKS:
        doc = json.loads((ROOT / 'script' / ('b%03d.json' % b['n'])).read_text(encoding='utf-8'))
        strs, _ = T.split_strings(b['data'])
        assert [e['jp'] for e in doc['strings']] == [T.decode(s) for s in strs], b['n']


def test_blocks_cover_text_range():
    # blocks tile 0x702EE..end of the last block with no gaps
    spans = sorted((b['off'], b['end']) for b in BLOCKS)
    for (s0, e0), (s1, e1) in zip(spans, spans[1:]):
        assert e0 == s1 or (s0 == s1 and e0 == e1)
    assert spans[0][0] == 0x702EE


def test_lzss_roundtrip():
    for b in BLOCKS:
        enc = lzss_encode(b['data'])
        assert lzss_decode_upto(enc, 0, len(enc)) == b['data']
