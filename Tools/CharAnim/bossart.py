"""Tiny painter for the big boss sprites (128x128 cells, feet on row 112).

Each body part is a mask filled with a 4-6 colour ramp and cel-shaded from the top-left (rim light, core shadow on the
lower-right, darker lower third). Parts drawn over others leave a dark seam so the shapes read; the whole figure gets a
dark outline at the end. Emissive parts (eyes, orbs, runes, lava) are flat bright colours with a soft halo.
Pure numpy + PIL, no source art is used.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

C = 128
FEET = 112          # first row below the feet -> pivot (0.5, 16/128)
CX = 64
OUTLINE = (14, 8, 18, 255)


def hx(s, a=255):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def ramp(*cols):
    return [hx(c) for c in cols]


# ------------------------------------------------------------------ masks
class Mask:
    """bool mask built from PIL primitives (no anti-aliasing = clean pixel edges)"""

    def __init__(self):
        self.im = Image.new('L', (C, C), 0)
        self.d = ImageDraw.Draw(self.im)

    def ell(self, cx, cy, rx, ry, on=True):
        self.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255 if on else 0)
        return self

    def poly(self, pts, on=True):
        self.d.polygon([(round(x), round(y)) for x, y in pts], fill=255 if on else 0)
        return self

    def line(self, pts, w=1, on=True):
        self.d.line([(round(x), round(y)) for x, y in pts], fill=255 if on else 0, width=max(1, int(w)))
        return self

    def rect(self, x0, y0, x1, y1, on=True):
        self.d.rectangle([x0, y0, x1, y1], fill=255 if on else 0)
        return self

    def px(self, x, y, on=True):
        if 0 <= x < C and 0 <= y < C:
            self.im.putpixel((int(x), int(y)), 255 if on else 0)
        return self

    @property
    def a(self):
        return np.array(self.im) > 0


def rot(pts, ang, pivot):
    """rotate points (degrees, screen space: +ang turns clockwise) around pivot"""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    px, py = pivot
    return [(px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c) for x, y in pts]


def limb_dir(angle, side):
    """angle 0 = hanging down, 90 = horizontal out (side=+1 right, -1 left), 180 = straight up"""
    a = math.radians(angle)
    return side * math.sin(a), math.cos(a)


def _shift(m, dx, dy):
    o = np.zeros_like(m)
    h, w = m.shape
    ys = slice(max(0, dy), min(h, h + dy)); yd = slice(max(0, -dy), min(h, h - dy))
    xs = slice(max(0, dx), min(w, w + dx)); xd = slice(max(0, -dx), min(w, w - dx))
    o[ys, xs] = m[yd, xd]
    return o


def dilate(m, r=1, diag=False):
    o = m.copy()
    for _ in range(r):
        n = o.copy()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (-1, -1), (1, -1), (-1, 1)) if diag else ()):
            n |= _shift(o, dx, dy)
        o = n
    return o


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self):
        self.f = np.zeros((C, C, 4), np.uint8)
        self.glow = []                       # (mask, colour, radius) soft halos applied at the end

    @property
    def solid(self):
        return self.f[:, :, 3] > 0

    def part(self, mask, rmp, seam=True, flat=False, mid=None, light=1):
        """cel-shade a mask with a ramp (dark -> light) and paint it over the canvas"""
        m = mask.a if isinstance(mask, Mask) else mask
        if not m.any():
            return
        n = len(rmp)
        if flat or n == 1:
            lvl = np.full(m.shape, n - 1, int)
        else:
            mid = (n - 3 if n >= 5 else n - 2) if mid is None else mid
            lvl = np.full(m.shape, mid, int)
            # rim light top-left
            rim = m & ~_shift(m, 1, 1)
            rim2 = m & ~_shift(m, 0, 1)
            lvl[rim | rim2] += light
            # core shadow bottom-right
            d1 = m & ~_shift(m, -1, -1)
            d2 = m & ~_shift(m, -2, -2) & ~d1
            d3 = m & ~_shift(m, -3, -3) & ~d1 & ~d2
            lvl[d1] -= 2
            lvl[d2] -= 1
            lvl[d3 & (np.arange(C)[:, None] % 2 == np.arange(C)[None, :] % 2)] -= 1    # dithered terminator
            # darker lower third of the part
            ys = np.nonzero(m)[0]
            y0, y1 = ys.min(), ys.max()
            low = np.zeros_like(m); low[y0 + (y1 - y0) * 2 // 3 + 1:] = True
            lvl[low & m] -= 1
            lvl = np.clip(lvl, 0, n - 1)
        if seam:
            ring = dilate(m) & ~m & self.solid
            self.f[ring, :3] = (self.f[ring, :3].astype(int) * 0.45).astype(np.uint8)
        cols = np.array(rmp, np.uint8)
        self.f[m] = cols[lvl[m]]

    def flat(self, mask, col):
        m = mask.a if isinstance(mask, Mask) else mask
        self.f[m] = col

    def emit(self, mask, core, edge=None, halo=None, radius=2):
        """emissive: bright core, slightly darker rim, optional soft halo"""
        m = mask.a if isinstance(mask, Mask) else mask
        if not m.any():
            return
        rim = m & ~(_shift(m, 1, 0) & _shift(m, -1, 0) & _shift(m, 0, 1) & _shift(m, 0, -1))
        self.f[m] = core
        if edge is not None:
            self.f[rim] = edge
        if halo is not None:
            self.glow.append((m, halo, radius))

    def pixels(self, pts, col):
        for x, y in pts:
            x, y = int(round(x)), int(round(y))
            if 0 <= x < C and 0 <= y < C:
                self.f[y, x] = col

    def finish(self, outline=True):
        if outline:
            s = self.solid
            o = dilate(s) & ~s
            self.f[o] = OUTLINE
        for m, col, r in self.glow:
            s = self.solid
            for k in range(1, r + 1):
                ring = dilate(m, k, diag=k > 1) & ~s
                a = int(col[3] * (1 - (k - 1) / r))
                self.f[ring] = (col[0], col[1], col[2], a)
                s = s | ring
        self.glow = []
        return self.f


# ------------------------------------------------------------------ effects on finished frames
def tint(f, col, k):
    o = f.copy()
    m = o[:, :, 3] > 0
    o[m, :3] = (o[m, :3].astype(float) * (1 - k) + np.array(col[:3], float) * k).astype(np.uint8)
    return o


def shift(f, dx, dy):
    o = np.zeros_like(f)
    h, w = f.shape[:2]
    o[max(0, dy):min(h, h + dy), max(0, dx):min(w, w + dx)] = f[max(0, -dy):min(h, h - dy), max(0, -dx):min(w, w - dx)]
    return o


def over(dst, src):
    o = dst.copy()
    m = src[:, :, 3] > 0
    a = src[:, :, 3:4].astype(float) / 255
    o[m, :3] = (src[m, :3] * a[m] + o[m, :3] * (1 - a[m])).astype(np.uint8)
    o[m, 3] = np.maximum(o[m, 3], src[m, 3])
    return o


def dissolve(f, k, col, seed=3):
    """death: pixels burn away from the top down into rising embers (k 0..1)"""
    rng = np.random.default_rng(seed)
    noise = rng.random((C, C))
    o = f.copy()
    m = o[:, :, 3] > 0
    if not m.any():
        return o
    ys = np.nonzero(m)[0]
    top, bot = ys.min(), ys.max()
    hgt = np.clip((np.arange(C)[:, None] - top) / max(1, bot - top), 0, 1)
    thresh = k * 1.4 - (1 - hgt) * 0.4
    gone = m & (noise < thresh)
    edge = m & ~gone & (noise < thresh + 0.12)
    o[gone] = 0
    o[edge] = col
    # embers rising from the burnt pixels
    gy, gx = np.nonzero(gone)
    if len(gy):
        pick = rng.choice(len(gy), size=min(len(gy), 18), replace=False)
        for i in pick:
            y = int(gy[i] - 4 - k * 14 * rng.random()); x = int(gx[i] + rng.integers(-2, 3))
            if 0 <= y < C and 0 <= x < C and o[y, x, 3] == 0:
                o[y, x] = col
    return o


def arc(f, cx, cy, r_out, r_in, a0, a1, cols, ry=1.0, fade=False):
    """slash trail between radii, angles in degrees (0 = right, 90 = down)"""
    o = f.copy()
    for y in range(C):
        for x in range(C):
            dx, dy = x - cx, (y - cy) / ry
            r = math.hypot(dx, dy)
            if not (r_in <= r <= r_out):
                continue
            a = math.degrees(math.atan2(dy, dx)) % 360
            lo, hi = a0 % 360, a1 % 360
            inside = lo <= a <= hi if lo <= hi else (a >= lo or a <= hi)
            if not inside:
                continue
            t = (r - r_in) / max(1, r_out - r_in)
            span = (a - lo) % 360 / max(1, (hi - lo) % 360)
            if fade and (x + y) % 2 == 0 and span < 0.5:
                continue
            c = cols[min(len(cols) - 1, int(t * len(cols)))]
            o[y, x] = c
    return o


def ring(f, cx, cy, r, col, ry=0.42, w=1):
    o = f.copy()
    for k in range(w):
        rr = r - k
        n = max(16, int(rr * 7))
        for i in range(n):
            a = 2 * math.pi * i / n
            x, y = int(round(cx + math.cos(a) * rr)), int(round(cy + math.sin(a) * rr * ry))
            if 0 <= x < C and 0 <= y < C:
                o[y, x] = col
    return o


def sparks(f, cx, cy, n, r, cols, seed=1):
    rng = np.random.default_rng(seed)
    o = f.copy()
    for i in range(n):
        a = rng.random() * 2 * math.pi
        d = r * (0.4 + 0.6 * rng.random())
        x, y = int(cx + math.cos(a) * d), int(cy + math.sin(a) * d * 0.8)
        if 0 <= x < C and 0 <= y < C:
            o[y, x] = cols[i % len(cols)]
            if i % 3 == 0 and 0 <= y - 1 < C:
                o[y - 1, x] = cols[i % len(cols)]
    return o


def save_sheet(frames, path):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    s = np.zeros((C, C * len(frames), 4), np.uint8)
    for i, f in enumerate(frames):
        s[:, i * C:(i + 1) * C] = f
    s[s[:, :, 3] == 0] = 0
    Image.fromarray(s, 'RGBA').save(path)
