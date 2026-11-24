"""Trees, plants, rocks and small props in the reference style."""
import math
import numpy as np
from kit import C, P, SHADOW, save, sheet, h2


def canopy(c, cx, cy, R, cols, outline, seed, squash=1.0, bumps=13, bamp=1.6):
    """round leafy crown: zig-zag rim, light from the top-left, little leaf strokes"""
    hi, mid, dk, dp = cols
    m = np.zeros((c.h, c.w), bool)
    sh = np.zeros((c.h, c.w))
    for y in range(c.h):
        for x in range(c.w):
            dx, dy = (x + .5 - cx), (y + .5 - cy) / squash
            r = math.hypot(dx, dy)
            th = math.atan2(dy, dx)
            rim = R + bamp * math.sin(th * bumps + seed) + 0.8 * math.sin(th * 5 + seed * 2)
            rim = R + round((rim - R) * 1.0)
            if r <= rim:
                m[y, x] = True
                nx, ny = dx / R, dy / R
                sh[y, x] = -0.55 * nx - 0.8 * ny + 0.25 * (1 - min(1, r / R))
    for y in range(c.h):
        for x in range(c.w):
            if not m[y, x]: continue
            s = sh[y, x] + (h2(x, y, seed) - .5) * 0.18
            col = hi if s > -0.15 else mid if s > -0.5 else dk if s > -0.78 else dp
            c.px(x, y, col)
    # leaf strokes: tiny "~" marks, darker on the lit side, lighter on the shaded side
    rnd = np.random.default_rng(seed)
    ys, xs = np.nonzero(m)
    for _ in range(int(len(xs) / 16)):
        k = rnd.integers(len(xs)); x, y = xs[k], ys[k]
        s = sh[y, x]
        col = mid if s > -0.15 else hi if s > -0.5 else mid
        for dx, dy in ((0, 0), (1, -1), (2, 0)):
            if 0 <= y + dy < c.h and 0 <= x + dx < c.w and m[y + dy, x + dx]:
                c.px(x + dx, y + dy, col)
    tmp = C(c.w, c.h); tmp.a[m] = c.a[m]
    tmp.outline(outline)
    c.a[(tmp.a[:, :, 3] > 0) & ~m] = tmp.a[(tmp.a[:, :, 3] > 0) & ~m]
    return m


def trunk(c, cx, top, bot, w, cols=('w_lt', 'w', 'w_dk'), outline='w_ol', roots=True):
    lt, md, dk = cols
    t = C(c.w, c.h)
    for y in range(top, bot + 1):
        flare = 0
        if roots and y > bot - 4:
            flare = (y - (bot - 4))
        x0, x1 = cx - w // 2 - flare, cx + (w - 1) // 2 + flare
        for x in range(x0, x1 + 1):
            rel = (x - x0) / max(1, x1 - x0)
            col = lt if rel < .3 else md if rel < .7 else dk
            if roots and y > bot - 3 and (x - cx) % 3 == 0 and abs(x - cx) > 1: col = dk
            t.px(x, y, col)
    # bark lines
    for y in range(top + 2, bot - 3, 3):
        t.px(cx + (y // 3) % 2 - 1, y, dk)
    t.outline(outline)
    c.paste(t, 0, 0)


GREEN = ('g_lt', 'g_md', 'g_dp', 'g_dp2')
PURPLE = ('pu_lt', 'pu', 'pu_dk', 'ash_bk')
AUTUMN = ('lava_hi', 'lava', 'mesa', 'mesa_dk')


def oak(w=58, h=76, R=24, cols=GREEN, outline='g_ol2', seed=3):
    c = C(w, h)
    c.ellipse(w / 2, h - 6, R * 1.0, 6, SHADOW)
    trunk(c, w // 2, h - 30, h - 4, 10)
    canopy(c, w / 2, R + 2, R, cols, outline, seed)
    return c


def oak_small(seed=5, cols=GREEN, outline='g_ol2'):
    c = C(40, 52)
    c.ellipse(20, 47, 15, 4.5, SHADOW)
    trunk(c, 20, 28, 49, 7)
    canopy(c, 20, 17, 15.5, cols, outline, seed, bumps=11, bamp=1.3)
    return c


def pine(snow=False, seed=7):
    c = C(36, 66)
    c.ellipse(18, 62, 12, 3, SHADOW)
    trunk(c, 18, 50, 63, 6, roots=False)
    t = C(36, 66)
    tiers = [(7, 10, 9), (17, 14, 11), (29, 17, 12), (41, 17, 10)]   # (y, half width, height)
    for (ty, hw, th) in reversed(tiers):
        for y in range(th):
            half = hw * (y + 1) / th
            for x in range(int(18 - half), int(18 + half) + 1):
                rel = (x - (18 - half)) / max(1, 2 * half)
                zig = (x + y) % 2 == 0 and y == th - 1
                if zig: continue
                col = 'g_lt' if rel < .45 else 'g_md' if rel < .8 else 'g_dp'
                if y == th - 1 and rel > .3: col = 'g_dp'
                if snow and y < 2 + (x % 3 == 0): col = 'sn' if rel < .6 else 'sn_md'
                t.px(x, ty + y, col)
    t.px(18, 5, 'sn' if snow else 'g_lt'); t.px(18, 6, 'sn' if snow else 'g_lt')
    t.outline('g_ol2')
    c.paste(t, 0, 0)
    return c


def dead_tree(seed=9):
    c = C(32, 44)
    c.ellipse(16, 40, 9, 2.5, SHADOW)
    t = C(32, 44)
    trunk(t, 16, 18, 41, 6, cols=('st_lt', 'st', 'st_md'), outline='st_ol')

    def branch(x, y, ang, ln, th):
        for i in range(int(ln)):
            x += math.cos(ang); y += math.sin(ang)
            for dx in range(-int(th), int(th) + 1):
                t.px(round(x) + dx, round(y), 'st' if dx <= 0 else 'st_md')
        return x, y
    for (ang, ln) in [(-2.2, 12), (-1.0, 11), (-1.6, 10)]:
        x, y = branch(16, 20, ang, ln, 1)
        branch(x, y, ang - .6, 5, 0); branch(x, y, ang + .6, 4, 0)
    t.outline('st_ol')
    c.paste(t, 0, 0)
    return c


def palm():
    c = C(32, 48)
    c.ellipse(16, 44, 9, 2.5, SHADOW)
    t = C(32, 48)
    for y in range(14, 45):
        x = 16 + int(3 * math.sin((y - 14) / 12))
        t.rect(x - 1, y, x + 1, y, 'w_lt' if y % 3 else 'w')
    for ang in (-2.8, -2.2, -1.2, -0.5, 0.1, 2.9):
        for i in range(13):
            x = 16 + math.cos(ang) * i; y = 14 + math.sin(ang) * i * .6 + (i * i) * 0.04
            t.px(round(x), round(y), 'g_lt'); t.px(round(x), round(y) + 1, 'g_md')
    t.outline('g_ol2')
    c.paste(t, 0, 0)
    return c


def bush(seed=11, cols=GREEN, flowers=False):
    c = C(20, 18)
    c.ellipse(10, 15, 8, 2.2, SHADOW)
    canopy(c, 10, 9, 7.2, cols, 'g_ol2', seed, bumps=8, bamp=1.0)
    if flowers:
        for (x, y) in [(6, 7), (12, 5), (13, 10), (8, 11)]:
            c.px(x, y, 'pk_hi'); c.px(x + 1, y, 'pk'); c.px(x, y + 1, 'pk_dk')
    return c


def tulip():
    rows = ["..a.a..", ".abcba.", ".abbba.", "..aaa..", "...d...", ".dede..", "..ede.."]
    pal = {'a': 'pk_dk', 'b': 'pk', 'c': 'pk_hi', 'd': 'g_dk', 'e': 'g_ol'}
    c = C(16, 16)
    c.ellipse(8, 14, 4, 1.4, SHADOW)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != '.': c.px(5 + i, 7 + j, pal[ch])
    return c


def daisies():
    c = C(16, 16)
    for (x, y) in [(5, 8), (10, 6), (9, 11)]:
        c.px(x, y + 2, 'g_dk')
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)): c.px(x + dx, y + dy, 'yl')
        c.px(x, y, 'yl_dk')
    return c


def tuft():
    c = C(16, 16)
    for (x, y) in [(4, 10), (9, 12)]:
        c.px(x, y, 'g_dk'); c.px(x + 2, y, 'g_dk'); c.px(x + 1, y + 1, 'g_dk2'); c.px(x - 1, y - 1, 'g_md'); c.px(x + 3, y - 1, 'g_md')
    return c


def rock(big=False, snow=False, water=False):
    w, h = (22, 18) if big else (14, 12)
    c = C(w, h)
    if water:
        c.ellipse(w / 2, h - 3, w / 2 - 1, 2.2, 'wa_dk')
    else:
        c.ellipse(w / 2, h - 3, w / 2 - 1.5, 2.2, SHADOW)
    t = C(w, h)
    rx, ry = (9, 7) if big else (5.5, 4.2)
    cx, cy = w / 2, h - 3 - ry
    for y in range(h):
        for x in range(w):
            dx, dy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            if dx * dx + dy * dy <= 1 and not (dy < -.5 and abs(dx) > .7):
                s = -dx * .5 - dy * .9
                col = 'st_hi' if s > .6 else 'st_lt' if s > 0 else 'st' if s > -.5 else 'st_dk'
                if snow and dy < -.35: col = 'sn' if s > 0 else 'sn_md'
                t.px(x, y, col)
    if big:
        for i in range(4): t.px(cx - 2 + i, cy + 1 + i // 2, 'st_dk')
    t.outline('st_ol')
    c.paste(t, 0, 0)
    return c


def lilypad(flower=False):
    c = C(16, 16)
    c.ellipse(8, 9, 4.5, 3.4, 'g_lt')
    c.ellipse(7.5, 8.5, 2.5, 1.8, 'g_hi')
    c.px(8, 8, 'wa'); c.px(9, 7, 'wa'); c.px(10, 6, 'wa')
    t = C(16, 16); t.a = c.a.copy(); t.outline('g_bk'); c.a = t.a
    if flower:
        c.px(7, 7, 'pk'); c.px(8, 6, 'pk_hi'); c.px(9, 7, 'pk'); c.px(8, 7, 'pk_dk')
    return c


def cattails():
    c = C(18, 20)
    for i, (x, hgt) in enumerate([(3, 12), (6, 15), (9, 11), (12, 14), (15, 10)]):
        for y in range(19 - hgt, 19):
            c.px(x, y, 'g_md' if y % 2 else 'g_dk')
        c.rect(x, 19 - hgt - 3, x, 19 - hgt, 'w_dk'); c.px(x, 19 - hgt - 4, 'g_md')
        c.px(x - 1, 16 - i % 2, 'g_md'); c.px(x - 2, 15 - i % 2, 'g_lt')
    return c


def log():
    c = C(32, 16)
    c.ellipse(16, 13, 14, 2.4, SHADOW)
    c.rect(4, 5, 27, 11, 'w')
    c.rect(4, 5, 27, 6, 'w_lt'); c.rect(4, 10, 27, 11, 'w_dk')
    for x in range(7, 26, 5): c.px(x, 8, 'w_dk'); c.px(x + 1, 8, 'w_dk')
    c.ellipse(5, 8.5, 2.6, 3.6, 's_hi'); c.ellipse(5, 8.5, 1.4, 2.2, 's'); c.px(5, 8, 's_dk')
    t = C(32, 16); t.a = c.a.copy(); t.a[t.a[:, :, 3] < 255] = 0; t.outline('w_ol')
    c.a[(t.a[:, :, 3] > 0) & (c.a[:, :, 3] < 255)] = t.a[(t.a[:, :, 3] > 0) & (c.a[:, :, 3] < 255)]
    return c


def stump():
    c = C(18, 16)
    c.ellipse(9, 13, 8, 2.4, SHADOW)
    t = C(18, 16)
    t.rect(5, 6, 12, 12, 'w'); t.rect(5, 6, 6, 12, 'w_lt'); t.rect(11, 6, 12, 12, 'w_dk')
    for x in (3, 4, 13, 14): t.px(x, 12, 'w_dk'); t.px(x, 11, 'w_dk' if x in (4, 13) else CLEARC)
    t.ellipse(8.5, 5.5, 4, 2, 's_hi'); t.ellipse(8.5, 5.5, 2.4, 1.1, 's'); t.px(8, 5, 's_dk')
    t.outline('w_ol')
    c.paste(t, 0, 0)
    return c


CLEARC = (0, 0, 0, 0)


def mushrooms():
    c = C(16, 16)
    for (x, y, r) in [(6, 10, 2.5), (10, 11, 2)]:
        c.rect(x, y, x, y + 3, 's_hi')
        c.ellipse(x + .5, y, r, r * .7, 'red')
        c.px(x - 1, y - 1, 'sn'); c.px(x + 1, y, 'sn')
    t = C(16, 16); t.a = c.a.copy(); t.outline('w_ol'); c.a = t.a
    return c


def fence_set():
    out = []
    def post(c, x):
        c.rect(x, 3, x + 3, 13, 'w'); c.rect(x, 3, x, 13, 'w_lt'); c.rect(x + 3, 4, x + 3, 13, 'w_dk')
        c.rect(x, 2, x + 3, 3, 's'); c.px(x + 1, 2, 's_hi')
    def rails(c, x0, x1):
        for y in (6, 10):
            c.rect(x0, y, x1, y, 'w_lt'); c.rect(x0, y + 1, x1, y + 1, 'w_dk')
    def fin(c):
        t = C(16, 16); t.paste(c, 0, 0); t.outline('w_ol')
        o = C(16, 16)
        for x in range(16):
            if t.a[13, x, 3]: o.px(x, 14, SHADOW)
        o.paste(t, 0, 0); return o
    c = C(16, 16); rails(c, 6, 15); post(c, 2); out.append(fin(c))
    c = C(16, 16); rails(c, 0, 15); post(c, 6); out.append(fin(c))
    c = C(16, 16); rails(c, 0, 9); post(c, 10); out.append(fin(c))
    c = C(16, 16); post(c, 6); out.append(fin(c))
    return out


def build_nature():
    made = []
    N = 'Nature/'
    made.append(save(oak(), N + 'tree_oak.png'))
    made.append(save(oak(seed=21), N + 'tree_oak_b.png'))
    made.append(save(oak_small(), N + 'tree_oak_small.png'))
    made.append(save(oak(cols=AUTUMN, outline='w_ol', seed=31), N + 'tree_autumn.png'))
    made.append(save(oak(cols=PURPLE, outline='ash_bk', seed=41), N + 'tree_corrupt.png'))
    made.append(save(oak_small(cols=PURPLE, outline='ash_bk', seed=43), N + 'tree_corrupt_small.png'))
    made.append(save(pine(), N + 'tree_pine.png'))
    made.append(save(pine(snow=True), N + 'tree_pine_snow.png'))
    made.append(save(dead_tree(), N + 'tree_dead.png'))
    made.append(save(palm(), N + 'tree_palm.png'))
    made.append(save(sheet([bush(), bush(seed=13, flowers=True), bush(seed=15, cols=PURPLE)], 20, 18), N + 'bushes_20x18.png'))
    made.append(save(sheet([tulip(), daisies(), tuft(), mushrooms()], 16, 16), N + 'plants_16x16.png'))
    made.append(save(sheet([lilypad(), lilypad(True)], 16, 16), N + 'lilypads_16x16.png'))
    made.append(save(cattails(), N + 'cattails.png'))
    made.append(save(rock(), N + 'rock_small.png'))
    made.append(save(rock(big=True), N + 'rock_big.png'))
    made.append(save(rock(big=True, snow=True), N + 'rock_snow.png'))
    made.append(save(rock(water=True), N + 'rock_water.png'))
    made.append(save(log(), N + 'log.png'))
    made.append(save(stump(), N + 'stump.png'))
    made.append(save(sheet(fence_set(), 16, 16), N + 'fence_16x16.png'))
    return made


if __name__ == '__main__':
    for p in build_nature(): print(p)
