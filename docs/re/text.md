# Text system (Shin Momotarou Densetsu, SNES HiROM, Rev 1)

ROM: 2 MB HiROM FastROM ($FFD5=$31), header "NEW MOMOTARO DENSETSU", SRAM 8 KB. File offset = addr & 0x3FFFFF.
Prior work: no SNES fan translation found (2026-10). KingMike translated the NES Momotarou Densetsu (2012).

## Blocks
- Table C7:0000 (file 0x70000): 250 x 24-bit pointers; block n = entry n-1. Data 0x702EE..0xAA5BC, then 0xFF fill
  to 0xAFFFF.
- Block = mode byte + data. 0 raw, 1 LZSS (80:BD28), 2 Huffman (80:BD98). Decoded as one stream from its start;
  string k of block n = skip k terminators (84:9DBB). Opened by 84:9D4D (block) + 84:9D91 (string index).
- LZSS: 256-byte ring zeroed, write index starts 0xEF. Flag byte MSB first, 1 = literal. Ref = offset byte
  (absolute ring index) + length nibble; one length byte serves two refs (high nibble first). Copy length nibble+2.
- Huffman: global tree, left child 80:BDEC[256], left-internal bitset 80:BEEB[32], right 80:BF0B[256],
  right-internal 80:C00A[32]. Bit 0 = left. A child whose internal bit is clear is the output byte.
- Text pointer $B1-$B3 (24-bit, carries into the bank), mode $12AA, katakana flag $12A9.

## Codes (fetch 84:9DE5 / 84:9E10, dialogue dispatch 84:A34B table A350, print 84:A5C8)
- 00 end. 01 newline. 02 XX: call string XX-A0 of block 1 (names; nested stack at $1274). 03 hiragana, 04 katakana.
- 05-08 colour ($12C6). 09 next argument (pops $1297 list: a string from a block or empty). 0A number ($12D4).
- 0B, 0C (wait), 0D, 0E, 0F (page end), 10, 12: box flow codes. 11 = name from $1569 (block 4).
- 18-1F XX kanji: (XXYY-0x1800) -> page 8+(c>>6), glyph c&63. Read by eye: `tbl/kanji.txt`.
- 50-8F page 1: space, 0-9, ?, !, 、, 。, …, ・, A-Z, ( ) 「 」 ～, ー ※ © + - / kg → ← 〈 〉 『 』 cm.
- 90-BE kana (page 2 hiragana / page 5 katakana), D0-E7 voiced (base from 84:A949 + mark page 3/6),
  F0-F9 small kana (page 4/7). 0xBE = で/デ.

## Font (bank DA)
- Page pointers DA:3800 (22 x 16-bit, page 1..22). Page = extents byte (hi nibble top row, lo bottom row) + glyphs.
- Glyph = 12 px wide, h rows, 2 bitplanes: per plane h bytes (left 8 px) + ceil(h/2) bytes (right 4 px, nibbles).
  Plane 1 = 1 px strokes, plane 0 = shadow outline. Size (h*3+1)&0x3E.
- Renderer 84:A8FD -> 84:A961 (decode into 7E:390B) -> 84:ABF1 (shift by $12C9 px and OR into line buffers
  7E:394B/397B) -> 84:AC8B advance: $12C9 += $12CC (fixed advance!), tile column $12C7. Upload via queue 80:A170.
  So the engine already renders at pixel offsets: VWF = per-glyph advance instead of $12CC.
