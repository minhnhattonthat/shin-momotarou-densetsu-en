"""Text block (de)compression for Shin Momotarou Densetsu (SNES, HiROM).

Block table: C7:0000, 250 x 24-bit pointers (block n = entry n-1). Each block: mode byte, then data.
  mode 0: raw bytes.
  mode 1: LZSS (80:BD28). 256-byte ring zero-filled, write position starts at 0xEF. Flag byte, MSB first:
          1 = literal byte; 0 = ref: offset byte (absolute ring index); lengths are nibbles shared by two refs:
          the first ref of a pair reads a byte L (len = (L>>4)+1+1), the second uses (L&15)+1+1.
  mode 2: Huffman (80:BD98) with one global tree in bank 80: left child BDEC[256], left-internal bits BEEB[32],
          right child BF0B[256], right-internal bits C00A[32]; bit 0 = left. Bits MSB first.
The game decodes a block as one stream from its start (the string index skips terminators), so a block is
compressed as a whole.
"""

TABLE = 0x070000
NBLOCKS = 250
TREE_L, TREE_LF, TREE_R, TREE_RF = 0x00BDEC, 0x00BEEB, 0x00BF0B, 0x00C00A


def block_ptrs(rom):
    return [int.from_bytes(rom[TABLE + 3 * i:TABLE + 3 * i + 3], 'little') for i in range(NBLOCKS)]


def lzss_decode(src, pos, n_out):
    """Decode n_out bytes (or until data runs out); returns (out, bytes consumed)."""
    ring = bytearray(256)
    w = 0xEF
    out = bytearray()
    flags = bits = 0
    have_len, lenbyte = False, 0
    start = pos
    while len(out) < n_out:
        if bits == 0:
            flags = src[pos]; pos += 1; bits = 8
        bit = flags & 0x80
        flags = (flags << 1) & 0xFF; bits -= 1
        b = src[pos]; pos += 1
        if bit:
            ring[w] = b; w = (w + 1) & 0xFF; out.append(b)
            continue
        r = b
        if not have_len:
            lenbyte = src[pos]; pos += 1
            n = (lenbyte >> 4) + 1
            have_len = True
        else:
            n = (lenbyte & 15) + 1
            have_len = False
        for _ in range(n + 1):
            c = ring[r]; r = (r + 1) & 0xFF
            ring[w] = c; w = (w + 1) & 0xFF
            out.append(c)
    return bytes(out), pos - start


def lzss_encode(data):
    """Greedy LZSS matching the decoder above. Match sources are ring indices (may overlap the write head)."""
    ring = bytearray(256)
    w = 0xEF
    out = bytearray()
    i = 0
    items = []  # ('L', byte) or ('R', off, n)
    # simulate ring to find matches: ring content == last 256 output bytes (+ initial zeros)
    hist = bytearray(256)  # same as ring
    while i < len(data):
        best_n, best_off = 0, 0
        maxn = min(17, len(data) - i)
        if maxn >= 2:
            for off in range(256):
                # simulate copy with overlap: source index walks ring while we write
                n = 0
                tmp = {}
                r, ww = off, w
                while n < maxn:
                    c = tmp.get(r, hist[r])
                    if c != data[i + n]:
                        break
                    tmp[ww] = c
                    r = (r + 1) & 0xFF; ww = (ww + 1) & 0xFF
                    n += 1
                if n > best_n:
                    best_n, best_off = n, off
                    if n == maxn:
                        break
        if best_n >= 3:
            items.append(('R', best_off, best_n))
            for k in range(best_n):
                hist[w] = data[i + k]; w = (w + 1) & 0xFF
            i += best_n
        else:
            items.append(('L', data[i]))
            hist[w] = data[i]; w = (w + 1) & 0xFF
            i += 1
    # emit: groups of 8 items with a flag byte; length nibble bytes are interleaved: first ref of a pair emits
    # [off, lenbyte], second ref emits [off]. The lenbyte's low nibble is patched when the second ref arrives.
    pend = None  # index in out of the pending lenbyte
    k = 0
    while k < len(items):
        group = items[k:k + 8]
        fpos = len(out); out.append(0)
        f = 0
        for j, it in enumerate(group):
            if it[0] == 'L':
                f |= 0x80 >> j
                out.append(it[1])
            else:
                out.append(it[1])
                n = it[2] - 2
                if pend is None:
                    pend = len(out); out.append(n << 4)
                else:
                    out[pend] |= n
                    pend = None
        out[fpos] = f
        k += 8
    return bytes(out)


def lzss_decode_upto(src, pos, end):
    """Decode items while the next item starts before `end` (exact block bounds)."""
    ring = bytearray(256)
    w = 0xEF
    out = bytearray()
    flags = bits = 0
    have_len, lenbyte = False, 0
    while pos < end:
        if bits == 0:
            flags = src[pos]; pos += 1; bits = 8
            if pos >= end:
                break
        bit = flags & 0x80
        flags = (flags << 1) & 0xFF; bits -= 1
        b = src[pos]; pos += 1
        if bit:
            ring[w] = b; w = (w + 1) & 0xFF; out.append(b)
            continue
        r = b
        if not have_len:
            lenbyte = src[pos]; pos += 1
            n = (lenbyte >> 4) + 1
            have_len = True
        else:
            n = (lenbyte & 15) + 1
            have_len = False
        for _ in range(n + 1):
            c = ring[r]; r = (r + 1) & 0xFF
            ring[w] = c; w = (w + 1) & 0xFF
            out.append(c)
    return bytes(out)


def huff_decode_upto(rom, pos, end):
    """Decode symbols that end within the block's last byte."""
    L, LF, R, RF = huff_tree(rom)
    out = bytearray()
    bitpos, endbit = pos * 8, end * 8
    while True:
        node, bp = 0, bitpos
        while True:
            if bp >= endbit:
                return bytes(out)
            bit = rom[bp >> 3] & (0x80 >> (bp & 7)); bp += 1
            if bit:
                nxt, internal = R[node], RF[node >> 3] & (0x80 >> (node & 7))
            else:
                nxt, internal = L[node], LF[node >> 3] & (0x80 >> (node & 7))
            node = nxt
            if not internal:
                out.append(nxt)
                break
        bitpos = bp


def huff_tree(rom):
    return (rom[TREE_L:TREE_L + 256], rom[TREE_LF:TREE_LF + 32], rom[TREE_R:TREE_R + 256], rom[TREE_RF:TREE_RF + 32])


def huff_decode(rom, pos, n_out):
    L, LF, R, RF = huff_tree(rom)
    out = bytearray()
    cur = 0
    bits = 0
    start = pos
    while len(out) < n_out:
        node = 0
        while True:
            if bits == 0:
                cur = rom[pos]; pos += 1; bits = 8
            bit = cur & 0x80; cur = (cur << 1) & 0xFF; bits -= 1
            if bit:
                nxt, internal = R[node], RF[node >> 3] & (0x80 >> (node & 7))
            else:
                nxt, internal = L[node], LF[node >> 3] & (0x80 >> (node & 7))
            node = nxt
            if not internal:
                out.append(nxt)
                break
    return bytes(out), pos - start
