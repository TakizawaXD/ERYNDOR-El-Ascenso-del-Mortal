"""Frame engine for the Tiny RPG character animation set.

Every frame is a 64x64 RGBA numpy array. All characters share one spatial reference:
  * body centre between columns 31 and 32 (so a horizontal flip never shifts the body)
  * feet touch row 51 (bottom exclusive = 52)  -> Unity pivot (0.5, 12/64)
"""
import glob, os
import numpy as np
from PIL import Image

CELL = 64
CX = 32          # flip axis: x -> 63 - x keeps a body centred on 31.5 in place
FEET = 52        # first row below the feet
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'Assets', 'Art', 'Characters')


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


def blank():
    return np.zeros((CELL, CELL, 4), np.uint8)


def opaque(f):
    return f[:, :, 3] > 0


def bbox(f):
    ys, xs = np.nonzero(f[:, :, 3])
    if len(xs) == 0:
        return None
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


# --------------------------------------------------------------- layering --
def over(dst, src, dx=0, dy=0):
    """alpha-composite src onto dst with integer offset (returns new array)"""
    out = dst.copy()
    h, w = src.shape[:2]
    ys, xs = np.nonzero(src[:, :, 3])
    for y, x in zip(ys, xs):
        X, Y = x + dx, y + dy
        if 0 <= X < out.shape[1] and 0 <= Y < out.shape[0]:
            s = src[y, x].astype(float) / 255
            if s[3] >= 1:
                out[Y, X] = src[y, x]
            else:
                d = out[Y, X].astype(float) / 255
                a = s[3] + d[3] * (1 - s[3])
                rgb = (s[:3] * s[3] + d[:3] * d[3] * (1 - s[3])) / max(a, 1e-6)
                out[Y, X] = np.round(np.r_[rgb, a] * 255)
    return out


def shift(f, dx=0, dy=0):
    return over(blank(), f, dx, dy)


def flip(f):
    return f[:, ::-1].copy()


def rot90(f, k=1, pivot=(32, 44)):
    """lossless 90-degree rotation around a pivot (pixel art safe)"""
    out = blank()
    ys, xs = np.nonzero(f[:, :, 3])
    px, py = pivot
    for y, x in zip(ys, xs):
        dx, dy = x - px, y - py
        for _ in range(k % 4):
            dx, dy = -dy, dx
        X, Y = px + dx, py + dy
        if 0 <= X < CELL and 0 <= Y < CELL:
            out[Y, X] = f[y, x]
    return out


def squash(f, rows=1, cut=None):
    """pixel-art squash: delete `rows` rows just above `cut` and drop the upper body down"""
    b = bbox(f)
    if b is None or rows <= 0:
        return f.copy()
    top, bot = b[1], b[3]
    cut = cut if cut is not None else top + (bot - top) * 2 // 3
    out = blank()
    out[cut:bot] = f[cut:bot]
    out[top + rows:cut] = f[top:cut - rows]
    return out


def stretch(f, rows=1, cut=None):
    """duplicate the waist row `rows` times and lift the upper body"""
    b = bbox(f)
    if b is None or rows <= 0:
        return f.copy()
    top, bot = b[1], b[3]
    cut = cut if cut is not None else top + (bot - top) * 2 // 3
    out = blank()
    out[cut:bot] = f[cut:bot]
    out[top - rows:cut - rows] = f[top:cut]
    for i in range(rows):
        out[cut - rows + i] = f[cut - 1]
    return out


def lean(f, px=1, above=None):
    """shear the upper body forward by px (positive = right)"""
    b = bbox(f)
    if b is None:
        return f.copy()
    top, bot = b[1], b[3]
    split = above if above is not None else top + (bot - top) // 2
    out = f.copy()
    out[top:split] = 0
    out = over(out, _rows(f, top, split), px, 0)
    return out


def _rows(f, a, b):
    o = blank(); o[a:b] = f[a:b]; return o


def recolor(f, mapping):
    out = f.copy()
    for y, x in zip(*np.nonzero(f[:, :, 3])):
        k = tuple(int(v) for v in f[y, x][:3])
        if k in mapping:
            out[y, x][:3] = mapping[k]
    return out


def silhouette(f, col):
    out = f.copy()
    m = opaque(f)
    out[m] = col
    return out


def outline(f, col, diag=False):
    m = opaque(f)
    o = np.zeros_like(m)
    o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    if diag:
        o[1:, 1:] |= m[:-1, :-1]; o[:-1, :-1] |= m[1:, 1:]; o[1:, :-1] |= m[:-1, 1:]; o[:-1, 1:] |= m[1:, :-1]
    o &= ~m
    out = f.copy()
    out[o] = col
    return out


def alpha(f, a):
    out = f.copy()
    out[:, :, 3] = (out[:, :, 3].astype(float) * a).astype(np.uint8)
    return out


def ascii_sprite(rows, pal):
    h, w = len(rows), max(len(r) for r in rows)
    a = np.zeros((h, w, 4), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch not in '. ':
                a[y, x] = pal[ch]
    return a


def place(sprite, cx=31.5, feet=FEET, dx=0, dy=0, dst=None):
    """put a small sprite so its horizontal centre is cx and its bottom row touches feet-1"""
    h, w = sprite.shape[:2]
    x0 = int(round(cx - w / 2 + .5 - .5)) if w % 2 == 0 else int(round(cx - (w - 1) / 2))
    y0 = feet - h
    return over(dst if dst is not None else blank(), sprite, x0 + dx, y0 + dy)


def save_sheet(frames, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    s = np.zeros((CELL, CELL * len(frames), 4), np.uint8)
    for i, f in enumerate(frames):
        s[:, i * CELL:(i + 1) * CELL] = f
    s[s[:, :, 3] == 0] = 0
    Image.fromarray(s, 'RGBA').save(path)


# -------------------------------------------------------- source loading --
def load_strip(path):
    im = np.array(Image.open(path).convert('RGBA'))
    n = im.shape[1] // 100
    return [im[:, i * 100:(i + 1) * 100] for i in range(n)]


def normalise(cell100, cx, feet):
    """crop a 100x100 original cell into the 64x64 shared reference"""
    x0 = int(round(cx + .5)) - CX
    y0 = feet - FEET
    out = blank()
    for y in range(CELL):
        for x in range(CELL):
            X, Y = x + x0, y + y0
            if 0 <= X < 100 and 0 <= Y < 100:
                out[y, x] = cell100[Y, X]
    return out
