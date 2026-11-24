"""Detailed trees: crowns built from overlapping leaf clumps (each with its own light), creases between clumps,
ambient occlusion under the crown, rim highlights, leaf strokes; trunks with bark and roots."""
import math
import numpy as np
from kit import C, P, SHADOW, save, sheet, h2

GREEN5 = ('g_hi', 'g_lt', 'g_md', 'g_dp', 'g_dp2')
AUTUMN5 = ('yl', 'lava_hi', 'lava', 'mesa', 'mesa_dk')
PURPLE5 = ('pk', 'pu_lt', 'pu', 'pu_dk', 'ash_bk')
SNOWY5 = ('sn', 'g_lt', 'g_md', 'g_dp', 'g_dp2')


def crown(c, cx, cy, R, cols, outline, seed, n_ring=8, flat=1.0):
    hi2, hi, mid, dk, deep = cols
    r = np.random.default_rng(seed)
    clumps = [(cx, cy + R * 0.05, R * 0.55)]
    for k in range(n_ring):
        a = 2 * math.pi * k / n_ring + r.uniform(-.25, .25)
        d = R * r.uniform(0.48, 0.6)
        clumps.append((cx + math.cos(a) * d, cy + math.sin(a) * d * flat, R * r.uniform(0.38, 0.5)))
    for k in range(3):        # a few clumps on top for a rounded silhouette
        a = -math.pi / 2 + r.uniform(-.9, .9)
        clumps.append((cx + math.cos(a) * R * 0.35, cy + math.sin(a) * R * 0.35, R * r.uniform(0.35, 0.45)))
    H, W = c.h, c.w
    owner = np.full((H, W), -1); score = np.full((H, W), -1e9); local = np.zeros((H, W))
    for i, (x0, y0, rr) in enumerate(clumps):
        for y in range(max(0, int(y0 - rr - 2)), min(H, int(y0 + rr + 3))):
            for x in range(max(0, int(x0 - rr - 2)), min(W, int(x0 + rr + 3))):
                dx, dy = x + .5 - x0, y + .5 - y0
                th = math.atan2(dy, dx)
                rim = rr + 0.9 * math.sin(th * 9 + i * 1.7 + seed)
                d = math.hypot(dx, dy)
                if d <= rim:
                    s = y0 * 0.6 + (rim - d) * 0.4          # lower clumps sit in front
                    if s > score[y, x]:
                        score[y, x] = s; owner[y, x] = i
                        nx, ny = dx / rr, dy / rr
                        local[y, x] = -0.6 * nx - 0.8 * ny + 0.3 * math.sqrt(max(0, 1 - min(1, (nx * nx + ny * ny))))
    m = owner >= 0
    ys, xs = np.nonzero(m)
    top, bot = ys.min(), ys.max()
    for y, x in zip(ys, xs):
        s = local[y, x]
        s -= 0.55 * ((y - top) / max(1, bot - top)) ** 1.6          # ambient occlusion toward the bottom
        s -= 0.15 * (x - cx) / R                                     # right side darker
        s += (h2(x, y, seed) - .5) * 0.12
        colr = hi2 if s > 0.55 else hi if s > 0.12 else mid if s > -0.3 else dk if s > -0.62 else deep
        c.px(x, y, colr)
    # creases where a front clump overlaps another one
    for y, x in zip(ys, xs):
        o = owner[y, x]
        for dx, dy in ((0, -1), (-1, 0), (1, 0)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and owner[yy, xx] >= 0 and owner[yy, xx] != o and score[yy, xx] < score[y, x] - 0.5:
                c.px(x, y, dk if local[y, x] < 0.3 else mid)
    # leaf strokes (tiny curved marks), brighter on the lit side
    for k in range(int(len(xs) / 11)):
        i = r.integers(len(xs)); x, y = xs[i], ys[i]
        s = local[y, x] - 0.5 * ((y - top) / max(1, bot - top))
        if s > 0.1: colr = hi2 if r.random() < .5 else mid
        elif s > -0.3: colr = hi
        else: colr = mid
        for ddx, ddy in ((0, 0), (1, -1), (2, -1)):
            if 0 <= y + ddy < H and 0 <= x + ddx < W and m[y + ddy, x + ddx]:
                c.px(x + ddx, y + ddy, colr)
    tmp = C(W, H); tmp.a[m] = c.a[m]; tmp.outline(outline)
    ring = (tmp.a[:, :, 3] > 0) & ~m
    c.a[ring] = tmp.a[ring]
    return m


def trunk_hd(c, cx, top, bot, w, cols=('w_lt', 'w', 'w_dk', 'w_ol'), canopy_shadow=4):
    """slightly tapered trunk, bark fissures, three spreading roots per side"""
    lt, md, dk, ol = cols
    t = C(c.w, c.h)
    for y in range(top, bot + 1):
        p = (y - top) / max(1, bot - top)
        half = w / 2 * (0.85 + 0.25 * p)
        x0, x1 = int(round(cx - half)), int(round(cx + half - 1))
        for x in range(x0, x1 + 1):
            rel = (x - x0) / max(1, x1 - x0)
            colr = lt if rel < .25 else md if rel < .65 else dk
            if (x * 7 + (y // 3)) % 5 == 0 and 0.15 < rel < 0.85: colr = dk
            if y < top + canopy_shadow: colr = dk if rel > .3 else md
            t.px(x, y, colr)
    # roots: diagonal prongs fanning out along the ground
    for side in (-1, 1):
        for k, (ln, drop) in enumerate(((6, 4), (4, 2), (3, 1))):
            x = cx + side * (w // 2 - 1 - k)
            y = bot - drop
            for i in range(ln):
                xx = x + side * i; yy = y + (i * drop) // ln
                t.px(xx, yy, md if i < ln - 1 else dk); t.px(xx, yy + 1, dk)
    t.outline(ol)
    c.paste(t, 0, 0)


def oak_hd(cols=GREEN5, outline='g_ol2', seed=3, w=62, h=80, R=25):
    c = C(w, h)
    c.ellipse(w / 2, h - 6, R * 1.05, 6.5, SHADOW)
    c.ellipse(w / 2 + 2, h - 6, R * 0.6, 4, (9, 27, 21, 50))
    trunk_hd(c, w // 2, h - 30, h - 6, 9)
    crown(c, w / 2, R + 8, R, cols, outline, seed)
    return c


def oak_small_hd(cols=GREEN5, outline='g_ol2', seed=5):
    c = C(44, 56)
    c.ellipse(22, 50, 16, 4.5, SHADOW)
    trunk_hd(c, 22, 32, 50, 7)
    crown(c, 22, 22, 16.5, cols, outline, seed, n_ring=6)
    return c


def pine_hd(snow=False, seed=7):
    """layered fir: each tier has ragged needle tips, lit left side, shade under the tier above"""
    c = C(40, 70)
    c.ellipse(20, 65, 13, 3.5, SHADOW)
    trunk_hd(c, 20, 54, 64, 5, canopy_shadow=3)
    t = C(40, 70)
    r = np.random.default_rng(seed)
    tiers = [(5, 8, 10), (12, 11, 12), (20, 14, 13), (29, 17, 14), (39, 19, 13)]
    for ti, (ty, hw, th) in enumerate(reversed(tiers)):
        tip = [r.integers(0, 3) for _ in range(40)]
        for y in range(th):
            p = (y + 1) / th
            half = hw * p + (1.5 if y == th - 1 else 0)
            for x in range(int(20 - half), int(20 + half) + 1):
                rel = (x - (20 - half)) / max(1, 2 * half)
                if y >= th - tip[x % 40] and (x % 3) != 1: continue          # ragged hanging tips
                colr = 'g_hi' if rel < .18 and y < th - 3 else 'g_lt' if rel < .45 else 'g_md' if rel < .75 else 'g_dp'
                if y >= th - 3: colr = 'g_dp' if rel > .35 else 'g_md'
                if y < 3: colr = 'g_dp2' if rel > .5 else 'g_dp'                   # shadow of the tier above
                if (x * 5 + y * 3 + ti) % 9 == 0 and rel < .6: colr = 'g_hi'
                if snow and y < 4 and ((x + ti) % 4 != 0): colr = 'sn' if rel < .55 else 'sn_md'
                t.px(x, ty + y, colr)
    for y in (2, 3, 4): t.px(20, y, 'sn' if snow else 'g_lt')
    t.outline('g_ol2')
    c.paste(t, 0, 0)
    return c


def bush_hd(seed=11, cols=GREEN5, berries=None):
    c = C(26, 22)
    c.ellipse(13, 18, 11, 3, SHADOW)
    crown(c, 13, 11, 9.5, cols, 'g_ol2', seed, n_ring=5)
    if berries:
        r = np.random.default_rng(seed)
        for _ in range(6):
            x, y = r.integers(6, 20), r.integers(5, 15)
            if c.a[y, x, 3]: c.px(x, y, berries); c.px(x + 1, y, berries); c.px(x, y - 1, 'sn')
    return c


def build():
    made = []
    N = 'Nature/'
    made.append(save(oak_hd(seed=3), N + 'tree_oak.png'))
    made.append(save(oak_hd(seed=21), N + 'tree_oak_b.png'))
    made.append(save(oak_small_hd(), N + 'tree_oak_small.png'))
    made.append(save(oak_hd(cols=AUTUMN5, outline='w_ol', seed=31), N + 'tree_autumn.png'))
    made.append(save(oak_hd(cols=PURPLE5, outline='ash_bk', seed=41), N + 'tree_corrupt.png'))
    made.append(save(oak_small_hd(cols=PURPLE5, outline='ash_bk', seed=43), N + 'tree_corrupt_small.png'))
    made.append(save(pine_hd(), N + 'tree_pine.png'))
    made.append(save(pine_hd(snow=True), N + 'tree_pine_snow.png'))
    made.append(save(sheet([bush_hd(), bush_hd(seed=13, berries='pk'), bush_hd(seed=15, cols=PURPLE5)], 26, 22), N + 'bushes_26x22.png'))
    return made


if __name__ == '__main__':
    for p in build(): print(p)
