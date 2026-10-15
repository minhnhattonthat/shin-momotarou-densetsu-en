"""Line wrapping for English dialogue (the game does not wrap; the box auto-pauses every 3 lines).

Translators keep {n} only where the Japanese starts a new speaker line / utterance / blank line; long lines are
broken here at spaces to fit LIMIT px. A continuation line of a quote ("...) is indented by one space so it
lines up after the opening quote, as the Japanese does with a full-width space.
    from wrap import wrap_text, lines_px
"""
import re
from en import text_width

LIMIT = 224          # px per dialogue line (field box: text x=16, inner edge x~244; measured 2026-10-16)
SPLIT = re.compile(r'(\{n\})')
LEAD = re.compile(r'^((?:\{c[0-3]\})*)')


def _wrap_line(seg, limit):
    """Balanced wrap: the fewest lines greedy needs at `limit`, with the narrowest limit that keeps that count."""
    if text_width(seg) <= limit:
        return [seg]
    best = _greedy(seg, limit)
    lo = limit
    while lo > 40:
        trial = _greedy(seg, lo - 4)
        if len(trial) != len(best) or any(text_width(x) > limit for x in trial):
            break
        best, lo = trial, lo - 4
    return best


def _greedy(seg, limit):
    lead = LEAD.match(seg).group(1)
    body = seg[len(lead):]
    indent = ' ' if body.startswith('"') else ''
    words = seg.split(' ')
    out, cur = [], ''
    for w in words:
        cand = (cur + ' ' + w) if cur else w
        if not out and not cur:
            cand = w
        if cur and text_width(cand) > limit:
            out.append(cur)
            cur = indent + w
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out


def wrap_text(text, limit=LIMIT):
    parts = SPLIT.split(text)
    res = []
    for p in parts:
        if p == '{n}':
            res.append(p)
        elif p:
            res.append('{n}'.join(_wrap_line(p, limit)))
    return ''.join(res)


def lines_px(text):
    """Widths of the lines of an already wrapped text."""
    return [text_width(seg) for seg in text.split('{n}')]
