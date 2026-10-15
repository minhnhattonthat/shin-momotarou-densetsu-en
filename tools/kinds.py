"""Per-block text kind and limits.

dlg  : dialogue/narration, proportional font, wrapped to wrap.LIMIT px per line, the box pauses every 3 lines.
name : names/labels shown in windows with the fixed 6 px English cell: limit = chars (2 per Japanese cell of the
       longest original in the block; refine per block from QA).
MIRROR: kana-only copies of kanji blocks (the game's kana display option): English is copied from the source.
"""
import re

MIRROR = {7: 6, 11: 8, 12: 9, 13: 10}
NAME_BLOCKS = {2, 3, 4, 5, 6, 8, 9, 10, 15, 19}
MANUAL = {1, 18}  # translated by the controller (dictionary fragments, name-entry grid), not batched


def jp_cells(jp, subs=None):
    """Display cells of a Japanese string (kana/kanji/page-1 char = 1 cell); {sub:XX} counts its expansion."""
    n = 0
    for m in re.finditer(r'\{([^}]*)\}|\[..\]|(.)', jp):
        if m.group(2) is not None:
            if m.group(2) != "'":
                n += 1
        elif m.group(1) and m.group(1).startswith('sub:') and subs:
            n += jp_cells(subs.get(int(m.group(1)[4:], 16) - 0xA0, ''), None)
    return n


def kind(block):
    block = MIRROR.get(block, block)
    return 'name' if block in NAME_BLOCKS else 'dlg'
