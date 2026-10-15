"""Read every text block of the original ROM into plain byte streams.

    from blocks import read_blocks; blocks = read_blocks(rom)  # list of dict(n, ptr, off, mode, clen, data)
A block ends where the next one (in ROM order) starts; the last one ends at the 0xFF fill after it.
"""
from comp import block_ptrs, lzss_decode_upto, huff_decode_upto


def block_bounds(rom):
    ptrs = block_ptrs(rom)
    offs = sorted(set(p & 0x3FFFFF for p in ptrs))
    res = []
    for p in ptrs:
        o = p & 0x3FFFFF
        later = [x for x in offs if x > o]
        if later:
            end = later[0]
        else:
            end = o + 1
            while rom[end:end + 8] != b'\xff' * 8:
                end += 1
        res.append((p, o, end))
    return res


def read_blocks(rom):
    res = []
    for i, (p, o, end) in enumerate(block_bounds(rom)):
        mode = rom[o]
        if mode == 0:
            data = bytes(rom[o + 1:end])
        elif mode == 1:
            data = lzss_decode_upto(rom, o + 1, end)
        else:
            data = huff_decode_upto(rom, o + 1, end)
        res.append(dict(n=i + 1, ptr=p, off=o, end=end, mode=mode, clen=end - o - 1, data=data))
    return res
