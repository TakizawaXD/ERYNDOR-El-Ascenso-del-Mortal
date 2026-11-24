"""Shared helpers + project palette for the pixel_16 woods / Tiny RPG art set.

All colours below were sampled from the existing assets
(free_pixel_16_woods.png and the Tiny RPG character sheets).
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Art'))


def hx(s, a=255):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


# ---- palette (sampled) ----------------------------------------------------
P = {k: hx(v) for k, v in dict(
    # greens
    g_hi='#7de230', g_lt='#65d53e', g_lt2='#5fcb39', g='#59c135', g_md='#14a02e',
    g_dk='#1a7a3e', g_ol='#23674e', g_dp='#24523b', g_mo='#328464',
    # earth
    d_hi='#f4d29c', d='#dba463', d_md='#c88b60', d_md2='#bb7547', d_cr='#ba756a',
    d_rd='#a65d3d', d_br='#8c5036', d_dk='#71413b', d_dk2='#5b3138', d_ol='#4e2428',
    d_ol2='#422433', d_pk='#8e5252',
    # water
    w_fo='#bce0f2', w_lt='#78c3e9', w='#249fde', w_md='#1e7fb1', w_md2='#1b74a2',
    w_dk='#446285', w_dp='#294d73', w_bl='#285cc4',
    # stone
    s_hi='#d5d4d1', s_lt='#b8bbc4', s='#8b93af', s_wm='#7b7773', s_md='#5a5755',
    s_dk='#4a5462', s_dk2='#333941', s_ol='#242234',
    # wood
    wd_lt='#a08662', wd='#796755', wd_md='#5a4e44', wd_dk='#423934', wd_ol='#322b28',
    # warm accents
    y='#fffc40', o='#f9a31b', or_='#fa6a0a', pk='#e86a73', sk='#d19771',
    pu='#793a80', pu_dk='#403353',
    # from characters
    c_red='#a22b4b', c_red2='#6e1438', c_red3='#311339', c_bld='#ed0d0d',
    c_wht='#f4edea', c_gry='#d9d8d8', c_gry2='#c0bfbf', c_blk='#1f1a1a',
    c_stl='#9badb7', c_stl2='#607581', c_stl3='#425c6b', c_lea='#7b4e16', c_lea2='#603a0a',
    blk='#000000', wht='#ffffff',
).items()}
SHADOW = (0, 0, 0, 55)
CLEAR = (0, 0, 0, 0)


def C(name_or_rgba, a=None):
    c = P[name_or_rgba] if isinstance(name_or_rgba, str) else name_or_rgba
    return c if a is None else (c[0], c[1], c[2], a)


class Canvas:
    def __init__(self, w, h):
        self.a = np.zeros((h, w, 4), np.uint8)
        self.w, self.h = w, h

    def px(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = C(c)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return tuple(self.a[y, x])
        return CLEAR

    def rect(self, x0, y0, x1, y1, c):  # inclusive
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x, y1, c)

    def ellipse(self, cx, cy, rx, ry, c, blend=False):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                    if blend:
                        self.blend(x, y, c)
                    else:
                        self.px(x, y, c)

    def blend(self, x, y, c):
        c = C(c)
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        d = self.a[y, x].astype(float) / 255
        s = np.array(c, float) / 255
        oa = s[3] + d[3] * (1 - s[3])
        if oa == 0:
            return
        rgb = (s[:3] * s[3] + d[:3] * d[3] * (1 - s[3])) / oa
        self.a[y, x] = np.round(np.r_[rgb, oa] * 255).astype(np.uint8)

    def shadow(self, cx, cy, rx, ry, c=SHADOW):
        """Soft drop shadow drawn *under* existing pixels (like the woods pack)."""
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                    if 0 <= x < self.w and 0 <= y < self.h and self.a[y, x, 3] == 0:
                        self.a[y, x] = c

    def sprite(self, rows, pal, ox=0, oy=0, flip=False):
        for j, r in enumerate(rows):
            if flip:
                r = r[::-1]
            for i, ch in enumerate(r):
                if ch in '. ':
                    continue
                self.px(ox + i, oy + j, pal[ch])

    def outline(self, c, diag=False, only_empty=True):
        a = self.a
        m = a[:, :, 3] == 255
        o = np.zeros_like(m)
        o[1:, :] |= m[:-1, :]; o[:-1, :] |= m[1:, :]
        o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        if diag:
            o[1:, 1:] |= m[:-1, :-1]; o[:-1, :-1] |= m[1:, 1:]
            o[1:, :-1] |= m[:-1, 1:]; o[:-1, 1:] |= m[1:, :-1]
        o &= ~m
        if only_empty:
            o &= a[:, :, 3] == 0
        a[o] = C(c)

    def paste(self, other, ox, oy):
        src = other.a if isinstance(other, Canvas) else other
        h, w = src.shape[:2]
        for y in range(h):
            for x in range(w):
                if src[y, x, 3]:
                    if src[y, x, 3] == 255:
                        self.px(ox + x, oy + y, tuple(src[y, x]))
                    else:
                        self.blend(ox + x, oy + y, tuple(src[y, x]))

    def img(self):
        return Image.fromarray(self.a, 'RGBA')


def save(canvas_or_img, rel):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = canvas_or_img.img() if isinstance(canvas_or_img, Canvas) else canvas_or_img
    # kill colour bleeding in fully transparent pixels (prevents halos with filtering)
    a = np.array(im)
    a[a[:, :, 3] == 0] = 0
    Image.fromarray(a, 'RGBA').save(path)
    return path


def sheet(frames, cw, ch, cols=None):
    cols = cols or len(frames)
    rows = (len(frames) + cols - 1) // cols
    s = Canvas(cw * cols, ch * rows)
    for i, f in enumerate(frames):
        s.paste(f, (i % cols) * cw, (i // cols) * ch)
    return s


def rng(seed):
    return np.random.default_rng(seed)


def hash2(x, y, s=0):
    h = (int(x) * 374761393 + int(y) * 668265263 + s * 2147483647) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return ((h ^ (h >> 16)) & 0xffff) / 65535.0
