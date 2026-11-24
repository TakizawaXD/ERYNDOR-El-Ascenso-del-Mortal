"""Silhouette features for the regional enemy variants (applied after the palette swap in variants.py).

Every 64x64 frame is searched for the head: the topmost pixel of the creature's own body colours inside a band around
the body centre (so a raised axe or a slash never counts). Features are drawn relative to that point, with a black
outline like the original art, and only where the frame is empty (never over the body).

  horns     big curved horns              crest     row of spikes / mohawk / ghost plume
  crystals  ice spikes on the shoulders   flames    flickering fire on the head (changes every frame)
  hat       corsair tricorn               spikes    thorns along the back of a slime
  eyes      glowing eye colour (recolour of the eye pixels)
"""
import numpy as np

BLACK = (0, 0, 0, 255)


def _c(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def head_top(f, body_cols, band=9, cx=32):
    a = f[:, :, 3] > 0
    if not a.any():
        return None
    rgb = f[:, :, :3]
    m = np.zeros(a.shape, bool)
    for c in body_cols:
        m |= np.all(rgb == c[:3], axis=2)
    m &= a
    m[:, :max(0, cx - band)] = False
    m[:, cx + band:] = False
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        return None
    y0 = ys.min()
    row = xs[ys <= y0 + 2]
    # width of the head a few rows down
    hrow = xs[(ys >= y0 + 2) & (ys <= y0 + 5)]
    l, r = (hrow.min(), hrow.max()) if len(hrow) else (row.min(), row.max())
    return int(y0), int((row.min() + row.max()) // 2), int(l), int(r)


class Layer:
    def __init__(self):
        self.a = np.zeros((64, 64, 4), np.uint8)

    def px(self, x, y, c):
        if 0 <= x < 64 and 0 <= y < 64:
            self.a[y, x] = c

    def stamp(self, f):
        """outline the feature in black and paint it only on empty pixels of the frame"""
        m = self.a[:, :, 3] > 0
        o = np.zeros_like(m)
        o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        o &= ~m
        free = f[:, :, 3] == 0
        out = f.copy()
        out[m & free] = self.a[m & free]
        out[o & free] = BLACK
        return out


def horns(L, y0, cx, l, r, cols, size=1):
    light, mid, dark = cols
    for side, x in ((-1, l), (1, r)):
        pts = [(x, y0 + 1), (x + side, y0), (x + side * 2, y0 - 1), (x + side * 2, y0 - 2), (x + side * 2, y0 - 3)]
        if size > 1: pts += [(x + side * 3, y0 - 3), (x + side * 3, y0 - 4), (x + side * 2, y0 - 5)]
        for i, (px, py) in enumerate(pts):
            L.px(px, py, light if i >= len(pts) - 2 else mid)
            if i < 3: L.px(px - side, py, dark)


def crest(L, y0, cx, l, r, cols, n=3, h=3, i=0):
    light, mid, dark = cols
    for k in range(n):
        x = cx - (n // 2) * 2 + k * 2
        hh = h - abs(k - n // 2)
        for j in range(1, hh + 1):
            L.px(x, y0 - j, light if j == hh else mid)
        L.px(x + 1, y0 - 1, dark)


def flames(L, y0, cx, l, r, cols, i=0):
    hot, mid, dark = cols
    rng = np.random.default_rng(i * 7 + 3)
    for x in range(l, r + 1):
        h = int(rng.integers(1, 4)) + (1 if abs(x - cx) < 2 else 0)
        for j in range(1, h + 1):
            L.px(x, y0 - j + 1, hot if j == h else mid if j > 1 else dark)


def crystals(f, L, y0, cx, l, r, cols):
    light, mid, dark = cols
    a = f[:, :, 3] > 0
    y = min(63, y0 + 7)
    xs = np.nonzero(a[y])[0]
    if len(xs) == 0:
        return
    for side, x in ((-1, xs.min()), (1, xs.max())):
        for k, h in enumerate((3, 4, 2)):
            px = x - side * k * 2
            ty = y - 1
            while ty > 0 and a[ty, px] and ty > y - 6:
                ty -= 1
            for j in range(h):
                L.px(px, ty - j, light if j == h - 1 else mid)


def hat(L, y0, cx, l, r, cols):
    light, mid, dark = cols
    for x in range(l - 2, r + 3):
        L.px(x, y0, mid)
    for x in range(l, r + 1):
        L.px(x, y0 - 1, dark); L.px(x, y0 - 2, mid if (x - l) % 5 else light)
    L.px(l - 3, y0 - 1, mid); L.px(r + 3, y0 - 1, mid)


def spikes(f, L, cols):
    light, mid, dark = cols
    a = f[:, :, 3] > 0
    xs = np.nonzero(a.any(axis=0))[0]
    if len(xs) == 0:
        return
    for x in range(xs.min() + 2, xs.max() - 1, 4):
        ys = np.nonzero(a[:, x])[0]
        if len(ys) == 0: continue
        y = ys.min()
        L.px(x, y - 1, mid); L.px(x, y - 2, light)


def eyes(f, mapping):
    out = f.copy()
    rgb = out[:, :, :3]
    for src, dst in mapping.items():
        m = np.all(rgb == src[:3], axis=2) & (out[:, :, 3] > 0)
        out[m, :3] = dst[:3]
    return out


def apply(frame, spec, body_cols, idx):
    """spec: dict(kind -> colours) for one variant"""
    f = frame
    if 'eyes' in spec:
        f = eyes(f, spec['eyes'])
    top = head_top(f, body_cols)
    if top is None:
        return f
    y0, cx, l, r = top
    L = Layer()
    for kind, cols in spec.items():
        if kind == 'horns': horns(L, y0, cx, l, r, cols, size=spec.get('_size', 1))
        elif kind == 'crest': crest(L, y0, cx, l, r, cols, n=spec.get('_n', 3), h=spec.get('_h', 3))
        elif kind == 'flames': flames(L, y0, cx, l, r, cols, idx)
        elif kind == 'crystals': crystals(f, L, y0, cx, l, r, cols)
        elif kind == 'hat': hat(L, y0, cx, l, r, cols)
        elif kind == 'spikes': spikes(f, L, cols)
    return L.stamp(f)


# colours as (light, mid, dark)
def C3(a, b, c):
    return (_c(a), _c(b), _c(c))


FEATURES = {
    'OrcDesert':    {'crest': C3('#f0e0b0', '#c8a870', '#6a4a28'), '_n': 5, '_h': 3, 'eyes': {_c('#7b0808'): _c('#ffd040')}},
    'OrcFrost':     {'horns': C3('#ffffff', '#c8e6f4', '#6a8aa8'), 'crystals': C3('#ffffff', '#8ad8f0', '#2a6a90'), 'eyes': {_c('#7b0808'): _c('#9ef0ff')}},
    'OrcCorsair':   {'hat': C3('#d8b040', '#2a2030', '#140e18'), 'eyes': {_c('#7b0808'): _c('#ffe060')}},
    'OrcBerserker': {'horns': C3('#f4e6c8', '#b89a70', '#5a4028'), '_size': 2, 'eyes': {_c('#7b0808'): _c('#ff3020')}},
    'DemonAsh':     {'flames': C3('#fff2a0', '#ff9a20', '#c03010'), 'eyes': {_c('#d79970'): _c('#fff060')}},
    'DemonWraith':  {'flames': C3('#e8fbff', '#7ad0ff', '#2a5aa0'), 'eyes': {_c('#d79970'): _c('#c8f8ff')}},
    'BloodToxic':   {'spikes': C3('#f0ff90', '#8cc83a', '#2e5a1a')},
    'BloodMagma':   {'flames': C3('#fff2a0', '#ffa020', '#c02a10')},
    'KnightFallen': {'crest': C3('#e0fffc', '#7ad8d0', '#2a7070'), '_n': 1, '_h': 5, 'eyes': {_c('#ffffff'): _c('#7af8ff')}},
}
