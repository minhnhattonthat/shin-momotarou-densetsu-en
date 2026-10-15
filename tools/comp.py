"""Text block (de)compression for Shin Momotarou Densetsu (SNES, HiROM).

Block table: C7:0000, 250 x 24-bit pointers (block n = entry n-1). Each block: mode byte, then data.
  mode 0: raw bytes.
  mode 1: LZSS (80:BD28). 256-byte ring zero-filled, write position starts at 0xEF. Flag byte, MSB first:
          1 = literal byte; 0 = ref: offset byte (absolute ring index); lengths are nibbles shared by two refs:
          the first ref of a pair reads a byte L (len = (L>>4)+2), the second uses (L&15)+2.
  mode 2: Huffman (80:BD98) with one global tree in bank 80: left child BDEC[256], left-internal bits BEEB[32],
          right child BF0B[256], right-internal bits C00A[32]; bit 0 = left. Bits MSB first.
The game decodes a block as one stream from its start (the string index skips terminators), so a block is
compressed as a whole.
"""

TABLE = 0x070000
NBLOCKS = 250
TREE_L, TREE_LF, TREE_R, TREE_RF = 0x00BDEC, 0x00BEEB, 0x00BF0B, 0x00C00A
RING0 = 0xEF


def block_ptrs(rom):
    return [int.from_bytes(rom[TABLE + 3 * i:TABLE + 3 * i + 3], 'little') for i in range(NBLOCKS)]


def lzss_encode(data):
    """Greedy LZSS for the decoder above. Only non-overlapping matches inside the last 256 output bytes, which the
    ring still holds unchanged while the copy runs (writes land on slots older than the source)."""
    items = []  # ('L', byte) or ('R', ring offset, length)
    heads = {}  # 3-byte key -> list of positions (newest last)
    i, n = 0, len(data)
    while i < n:
        best_n, best_p = 0, 0
        if i + 3 <= n:
            for p in reversed(heads.get(data[i:i + 3], ())):
                if p < i - 256:
                    break
                maxn = min(17, n - i, i - p)
                k = 3
                while k < maxn and data[p + k] == data[i + k]:
                    k += 1
                if k > best_n and k <= i - p:
                    best_n, best_p = k, p
                    if k == 17:
                        break
        step = best_n if best_n >= 3 else 1
        if best_n >= 3:
            items.append(('R', (RING0 + best_p) & 0xFF, best_n))
        else:
            items.append(('L', data[i]))
        for j in range(i, i + step):
            if j + 3 <= n:
                heads.setdefault(data[j:j + 3], []).append(j)
        i += step
    out = bytearray()
    pend = None  # index of the length byte shared with the next ref
    for k in range(0, len(items), 8):
        fpos = len(out)
        out.append(0)
        f = 0
        for j, it in enumerate(items[k:k + 8]):
            if it[0] == 'L':
                f |= 0x80 >> j
                out.append(it[1])
            else:
                out.append(it[1])
                ln = it[2] - 2
                if pend is None:
                    pend = len(out)
                    out.append(ln << 4)
                else:
                    out[pend] |= ln
                    pend = None
        out[fpos] = f
    return bytes(out)


def lzss_decode_upto(src, pos, end):
    """Decode items while the next item starts before `end` (exact block bounds)."""
    ring = bytearray(256)
    w = RING0
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
