"""Landmarks & buildings for the world map (reference style: bold dark outlines, 3-tone shading, light from top-left)."""
import math
import numpy as np
from kit import C, P, SHADOW, save, sheet, h2


def finish(c, outline):
    t = C(c.w, c.h); t.a = c.a.copy(); t.a[t.a[:, :, 3] < 255] = 0
    t.outline(outline)
    m = (t.a[:, :, 3] > 0) & (c.a[:, :, 3] < 255)
    c.a[m] = t.a[m]
    return c


def tri(c, x0, x1, ytop, ybot, col_l, col_r, apex=None):
    apex = apex if apex is not None else (x0 + x1) / 2
    for y in range(ytop, ybot + 1):
        p = (y - ytop) / max(1, ybot - ytop)
        l = apex - (apex - x0) * p; r = apex + (x1 - apex) * p
        for x in range(int(round(l)), int(round(r)) + 1):
            c.px(x, y, col_l if x < apex else col_r)


# ------------------------------------------------------------- landforms
def facet(x, y, seed):
    """blocky rock facets: smooth value-noise quantised into chunky patches"""
    v = 0
    for k, sc in enumerate((7.0, 3.5)):
        X, Y = x / sc, y / sc
        x0, y0 = int(X), int(Y); fx, fy = X - x0, Y - y0
        a = h2(x0, y0, seed + k); b = h2(x0 + 1, y0, seed + k); c_ = h2(x0, y0 + 1, seed + k); d = h2(x0 + 1, y0 + 1, seed + k)
        v += (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c_ * (1 - fx) * fy + d * fx * fy) * (0.65 if k == 0 else 0.35)
    return v


def mountain(seed=1, w=64, h=56, snow=True):
    """main ridge (lit left / shaded right), secondary ridges with creases, jagged snow cap with streaks"""
    c = C(w, h)
    c.ellipse(w / 2, h - 4, w / 2 - 2, 4, SHADOW)
    r = np.random.default_rng(seed)
    apex = w / 2 + r.integers(-w // 10, w // 10 + 1)
    top, bot = 3, h - 4
    ridge = lambda y: apex + 3 * math.sin((y - top) * 0.18 + seed) * (y - top) / (bot - top)
    subs = [(top + (bot - top) * r.uniform(.25, .6), r.choice([-1, 1]) * r.uniform(.5, .9)) for _ in range(4)]
    snowline = top + (bot - top) * 0.45
    for y in range(top, bot):
        p = (y - top) / (bot - top)
        hl, hr = (apex - 1) * p, (w - 1 - apex) * p
        jag = int(round(1.2 * math.sin(y * .8 + seed)))
        for x in range(int(apex - hl) + jag, int(apex + hr) + 1 - jag):
            rx = ridge(y)
            lit = x < rx
            shade = 0.0
            for (sy, slope) in subs:
                if y > sy:
                    sx = rx + slope * (y - sy) * 1.4
                    d = x - sx
                    if 0 <= d < 2: shade -= 1.0          # crease on the far side of a sub-ridge
                    elif -2 < d < 0: shade += 0.6        # lit edge of the sub-ridge
            v = h2(x // 3, y // 3, seed) * 0.4
            sl = snowline + 4 * math.sin(x * .45 + seed) + 3 * h2(x, 0, seed)
            if snow and y < sl:
                base = 2 if lit else 1
                lvl = base + shade + v
                col = 'sn' if lvl > 1.7 else 'sn_md' if lvl > 0.9 else 'sn_dk'
            else:
                base = 2.2 if lit else 0.9
                lvl = base + shade + v - p * 0.6
                col = 'st_hi' if lvl > 2.3 else 'st_lt' if lvl > 1.6 else 'st' if lvl > 0.9 else 'st_md' if lvl > 0.3 else 'st_dk'
                if snow and y < sl + 6 and (x * 3 + y) % 7 == 0 and lit: col = 'sn_md'     # snow streaks in the gullies
            c.px(x, y, col)
        c.px(int(ridge(y)), y, 'sn_dk' if (snow and y < snowline) else 'st_dk') if y > top + 3 else None
    # boulders at the foot
    for k in range(3):
        bx = r.integers(4, w - 6); by = bot - r.integers(0, 3)
        c.ellipse(bx, by, 2.5, 1.6, 'st'); c.px(bx - 1, by - 1, 'st_lt')
    return finish(c, 'st_ol')


def mesa(seed=2):
    c = C(48, 40)
    c.ellipse(24, 36, 20, 3.5, SHADOW)
    for y in range(12, 35):
        for x in range(6, 42):
            v = facet(x, y * 2, seed)
            lit = x < 16 + 3 * math.sin(y * .4)
            strata = (y + int(2 * math.sin(x * .3))) % 7 == 0
            col = 'mesa_dk' if strata else (('mesa_lt' if v > .45 else 'mesa') if lit else ('mesa' if v > .55 else 'mesa_dk'))
            c.px(x, y, col)
    c.ellipse(24, 12, 18.5, 5, 'mesa_lt'); c.ellipse(24, 11.5, 15, 3.4, 's_md')
    for (x, y) in [(18, 10), (28, 12)]: c.px(x, y, 'g_md'); c.px(x + 1, y, 'g_dk')
    return finish(c, 'w_ol')


def volcano_frames(S=1.0):
    out = []
    for f in range(4):
        c = C(int(80 * S), int(64 * S))
        cx = c.w / 2; top = int(10 * S); bot = c.h - int(4 * S)
        c.ellipse(cx, bot - 1, c.w / 2 - 4, 4 * S, SHADOW)
        for y in range(top, bot):
            p = (y - top) / (bot - top)
            half = 8 * S + (c.w / 2 - 10 * S) * p
            for x in range(int(cx - half), int(cx + half) + 1):
                lit = x < cx - half * 0.15
                v = facet(x, y, 5)
                col = ('st_md' if v > .62 else 'ash') if lit else ('ash' if v > .6 else 'ash_dk')
                c.px(x, y, col)
        c.ellipse(cx, top + 1, 9 * S, 3 * S, 'lava_dk'); c.ellipse(cx, top + 1, 6 * S, 2 * S, 'lava' if f % 2 else 'lava_hi')
        # lava streams flowing down (animated glow)
        for k, (sx, drift) in enumerate([(cx - 4 * S, -0.45), (cx + 4 * S, 0.4), (cx, 0.05)]):
            for y in range(top + 3, int(bot - 8 * S) - k * int(6 * S)):
                x = sx + (y - top - 3) * drift + math.sin(y * .3 + k) * 1.2
                v = (y + f * 3 + k * 2) % 8
                c.px(round(x), y, 'lava_hi' if v < 2 else 'lava')
                c.px(round(x) + 1, y, 'lava_dk')
        # smoke puffs
        for k in range(3):
            yy = top - 4 - k * 3 - f % 2
            c.ellipse(cx + (k - 1) * 3 + f % 2, yy, 2.5 * S - k * .4, 2 * S - k * .3, 'st_md' if k else 'st')
        out.append(finish(c, 'ash_bk'))
    return out


# ------------------------------------------------------------- buildings
PERSON = 18          # Soldier body height in px: every door/opening is sized from it
DOOR_H, DOOR_W = 20, 10


def door(c, cx, bottom, cols=('w_ol', 'w_mid', 'w')):
    ol, fill, frame = cols
    c.rect(cx - DOOR_W // 2 - 1, bottom - DOOR_H - 1, cx + DOOR_W // 2, bottom, ol)
    c.rect(cx - DOOR_W // 2, bottom - DOOR_H, cx + DOOR_W // 2 - 1, bottom, fill)
    for y in range(bottom - DOOR_H + 3, bottom, 4):
        c.rect(cx - DOOR_W // 2, y, cx + DOOR_W // 2 - 1, y, frame)
    c.px(cx + DOOR_W // 2 - 3, bottom - DOOR_H // 2, 'yl_dk')


def window(c, x, y, w=8, h=8):
    c.rect(x, y, x + w - 1, y + h - 1, 'w_ol'); c.rect(x + 1, y + 1, x + w - 2, y + h - 2, 'yl')
    c.rect(x + 1, y + h // 2, x + w - 2, y + h // 2, 'w_ol'); c.rect(x + w // 2, y + 1, x + w // 2, y + h - 2, 'w_ol')
    c.px(x + 1, y + 1, 'sn')


def house(roof=('red', 'red_dk'), w=64, h=68):
    """log cabin: wall 32 px (door 20 px), roof 28 px - a person is 18 px"""
    c = C(w, h)
    c.ellipse(w / 2, h - 3, w / 2 - 1, 3.5, SHADOW)
    wall_top, ground = h - 36, h - 4
    for y in range(wall_top, ground):
        col = 'w' if ((y - wall_top) // 4) % 2 else 'w_dk'
        if (y - wall_top) % 4 == 0: col = 'w_ol'
        c.rect(6, y, w - 7, y, col)
    for x in (5, 6, w - 7, w - 6):
        c.rect(x, wall_top, x, ground, 'w_lt' if x in (5, w - 7) else 'w')
    door(c, w // 2, ground)
    window(c, 12, wall_top + 7); window(c, w - 20, wall_top + 7)
    rl, rd = roof
    rtop = wall_top - 28
    for y in range(rtop, wall_top + 2):
        p = (y - rtop) / (wall_top + 2 - rtop)
        half = 6 + (w / 2 - 1) * p
        for x in range(int(w / 2 - half), int(w / 2 + half) + 1):
            col = rl if x < w / 2 else rd
            if (y - rtop) % 5 == 4: col = rd if x < w / 2 else 'w_ol'
            c.px(x, y, col)
    c.rect(w // 2 - 1, rtop - 2, w // 2, rtop + 1, 'w_dk')
    c.rect(w - 20, rtop + 4, w - 16, rtop + 14, 'st_md'); c.rect(w - 20, rtop + 3, w - 16, rtop + 3, 'st_dk')
    return finish(c, 'w_ol')


def stone_wall():
    """castle wall segment (tileable horizontally, 32 wide)"""
    c = C(32, 40)
    c.rect(0, 10, 31, 37, 'st')
    for y in range(10, 38):
        row = (y - 10) // 4
        for x in range(32):
            off = 0 if row % 2 else 4
            if (y - 10) % 4 == 3 or (x + off) % 8 == 0: c.px(x, y, 'st_dk')
            elif (y - 10) % 4 == 0: c.px(x, y, 'st_lt')
    for x in range(0, 32, 8):          # battlements
        c.rect(x, 4, x + 4, 9, 'st_lt'); c.rect(x, 4, x + 4, 4, 'st_hi')
    c.rect(0, 36, 31, 37, 'st_md')
    t = finish(c, 'st_ol')
    return t


def tower(roof=('wa_dp', 'st_ol'), w=40, h=100, flag=True):
    """stone tower: 20 px door, body ~3.5 persons tall, conical roof"""
    c = C(w, h)
    c.ellipse(w / 2, h - 3, w / 2 - 1, 3.5, SHADOW)
    body_top, ground = h - 64, h - 4
    c.rect(5, body_top, w - 6, ground, 'st')
    c.rect(5, body_top, 10, ground, 'st_lt'); c.rect(w - 11, body_top, w - 6, ground, 'st_md')
    for y in range(body_top + 2, ground, 5): c.rect(5, y, w - 6, y, 'st_dk')
    for y in range(body_top + 6, ground, 10):
        off = 0 if (y // 10) % 2 else 6
        for x in range(7 + off, w - 7, 12): c.rect(x, y - 4, x, y, 'st_dk')
    door(c, w // 2, ground, ('st_ol', 'w_mid', 'w'))
    for wy in (body_top + 8, body_top + 24):
        c.rect(w // 2 - 2, wy, w // 2 + 1, wy + 7, 'st_ol'); c.rect(w // 2 - 1, wy + 1, w // 2, wy + 6, 'yl')
    rl, rd = roof
    tri(c, 1, w - 2, body_top - 30, body_top, rl, rd)
    c.rect(2, body_top - 1, w - 3, body_top + 1, 'st_lt')
    if flag:
        c.rect(w // 2, body_top - 38, w // 2, body_top - 30, 'st_ol'); c.rect(w // 2 + 1, body_top - 38, w // 2 + 7, body_top - 35, 'red')
    return finish(c, 'st_ol')


def windmill_frames():
    """tower 58 px with a 20 px door + 26 px blades"""
    out = []
    W_, H_ = 72, 104
    for f in range(4):
        c = C(W_, H_)
        cx, ground = W_ // 2, H_ - 4
        c.ellipse(cx, H_ - 3, 20, 3.5, SHADOW)
        top = ground - 58
        for y in range(top, ground):
            p = (y - top) / (ground - top)
            half = 11 + 7 * p
            for x in range(int(cx - half), int(cx + half) + 1):
                c.px(x, y, 'sn' if x < cx + 2 else 'sn_md')
        for y in range(top + 8, ground, 9): c.rect(int(cx - 10), y, int(cx + 10), y, 'sn_dk')
        door(c, cx, ground)
        window(c, cx - 4, top + 14)
        tri(c, cx - 14, cx + 14, top - 14, top + 1, 'red', 'red_dk', apex=cx)
        hx_, hy_ = cx, top - 2
        ang0 = f * math.pi / 8
        for k in range(4):
            a = ang0 + k * math.pi / 2
            for i in range(3, 30):
                x = hx_ + math.cos(a) * i; y = hy_ + math.sin(a) * i
                c.px(round(x), round(y), 'w_dk')
                if i > 8:
                    nx, ny = -math.sin(a), math.cos(a)
                    for j in (1, 2, 3, 4, 5):
                        c.px(round(x + nx * j), round(y + ny * j), 'sn' if j < 5 else 'sn_dk')
        c.ellipse(hx_, hy_, 2.2, 2.2, 'w_ol')
        out.append(finish(c, 'w_ol'))
    return out


def lighthouse():
    W_, H_ = 36, 108
    c = C(W_, H_)
    cx, ground = W_ // 2, H_ - 4
    c.ellipse(cx, H_ - 3, 15, 3, SHADOW)
    top = ground - 76
    for y in range(top, ground):
        half = 8 + (y - top) * 0.07
        band = ((y - top) // 12) % 2
        for x in range(int(cx - half), int(cx + half) + 1):
            lit = x < cx
            col = ('sn' if lit else 'sn_md') if band == 0 else ('red' if lit else 'red_dk')
            c.px(x, y, col)
    door(c, cx, ground, ('st_ol', 'w_mid', 'w'))
    c.rect(cx - 9, top - 12, cx + 8, top, 'st_ol'); c.rect(cx - 8, top - 11, cx + 7, top - 1, 'yl'); c.rect(cx - 6, top - 9, cx - 3, top - 3, 'sn')
    c.rect(cx - 11, top - 1, cx + 10, top + 1, 'st_md')
    tri(c, cx - 10, cx + 10, top - 24, top - 12, 'red', 'red_dk')
    return finish(c, 'st_ol')


def dark_tower_frames():
    out = []
    W_, H_ = 44, 120
    for f in range(4):
        c = C(W_, H_)
        cx, ground = W_ // 2, H_ - 4
        c.ellipse(cx, H_ - 3, 18, 3.5, SHADOW)
        top = ground - 84
        for y in range(top, ground):
            half = 10 + (y - top) * 0.09
            for x in range(int(cx - half), int(cx + half) + 1):
                lit = x < cx - 3
                col = 'st_md' if lit else 'st_dk'
                if (y % 7 == 0) or ((x + (y // 7) * 3) % 9 == 0 and y % 7 < 6): col = 'ash_dk'
                c.px(x, y, col)
        door(c, cx, ground, ('ash_bk', 'pu_dk', 'ash_dk'))
        for wy in (top + 14, top + 36):
            c.rect(cx - 2, wy, cx + 1, wy + 8, 'ash_bk'); c.rect(cx - 1, wy + 1, cx, wy + 7, 'g_hi' if f % 2 else 'g_lt')
        tri(c, cx - 14, cx + 14, top - 22, top, 'pu', 'pu_dk')
        glow = [4.5, 6, 7.5, 6][f]
        c.ellipse(cx, top - 26, glow, glow, (99, 199, 77, 90))
        c.ellipse(cx, top - 26, 2.2, 2.2, 'g_hi')
        out.append(finish(c, 'ash_bk'))
    return out


def ruin_wall():
    c = C(40, 32)
    c.ellipse(20, 29, 18, 2.6, SHADOW)
    heights = [12, 14, 15, 18, 20, 20, 19, 21, 22, 22, 20, 18, 16, 16, 15, 14, 12, 12, 10, 10, 11, 12, 13, 12, 10, 8, 8, 9, 10, 10, 9, 7, 6, 6, 5, 5]
    for i, hh in enumerate(heights):
        x = i + 2
        for y in range(28 - hh, 28):
            ry = 27 - y; row = ry // 4; off = 0 if row % 2 else 3
            mort = ry % 4 == 3 or (x + off) % 7 == 0
            col = 'st_dk' if mort else ('st_lt' if ry % 4 == 2 else 'st')
            if y == 28 - hh: col = 'st_hi'
            c.px(x, y, col)
    for (x, y) in [(8, 14), (9, 14), (9, 15), (16, 8), (17, 8), (25, 17), (26, 17)]: c.px(x, y, 'g_md')
    return finish(c, 'st_ol')


def pillar():
    c = C(16, 34)
    c.ellipse(8, 31, 7, 2.4, SHADOW)
    c.rect(4, 8, 11, 28, 'st'); c.rect(4, 8, 5, 28, 'st_lt'); c.rect(10, 8, 11, 28, 'st_md')
    for y in (12, 18, 24): c.rect(4, y, 11, y, 'st_dk')
    c.rect(3, 6, 12, 8, 'st_lt'); c.px(5, 5, 'st'); c.px(9, 4, 'st'); c.px(10, 5, 'st')
    c.rect(2, 28, 13, 30, 'st_lt'); c.rect(2, 30, 13, 30, 'st_md')
    for (x, y) in [(5, 20), (6, 21), (10, 14)]: c.px(x, y, 'g_md')
    return finish(c, 'st_ol')


def dock_set():
    """dock planks: horizontal (W, mid, E) and vertical (N, mid, S) 16x16"""
    out = []
    for k in range(3):
        c = C(16, 16)
        for x in range(16):
            c.rect(x, 3, x, 12, 'w_lt' if x % 4 == 0 else 'w' if x % 4 in (1, 2) else 'w_dk')
        c.rect(0, 2, 15, 2, 'w_ol'); c.rect(0, 13, 15, 13, 'w_ol'); c.rect(0, 14, 15, 15, (0, 0, 0, 60))
        if k in (0, 2):
            px = 0 if k == 0 else 12
            c.rect(px, 0, px + 3, 15, 'w_dk'); c.rect(px, 0, px + 3, 1, 's'); c.rect(px + 1, 0, px + 1, 15, 'w')
        out.append(c)
    for k in range(3):
        c = C(16, 16)
        for y in range(16):
            c.rect(3, y, 12, y, 'w_lt' if y % 4 == 0 else 'w' if y % 4 in (1, 2) else 'w_dk')
        c.rect(2, 0, 2, 15, 'w_ol'); c.rect(13, 0, 13, 15, 'w_ol'); c.rect(14, 0, 15, 15, (0, 0, 0, 60))
        if k in (0, 2):
            py = 0 if k == 0 else 12
            for px in (0, 12):
                c.rect(px, py, px + 3, py + 3, 'w_dk'); c.rect(px, py, px + 3, py, 's')
        out.append(c)
    return out


def boat():
    c = C(40, 28)
    c.ellipse(20, 22, 18, 3, (0, 109, 168, 255))
    for y in range(14, 22):
        p = (y - 14) / 8
        half = 17 - p * 5
        for x in range(int(20 - half), int(20 + half) + 1):
            c.px(x, y, 'w' if y > 15 else 'w_lt')
    c.rect(4, 14, 36, 14, 's')
    c.rect(19, 0, 20, 14, 'w_dk')
    tri(c, 21, 33, 2, 12, 'sn', 'sn_md', apex=21)
    return finish(c, 'w_ol')


def bridge_set():
    """wooden bridge, horizontal (W, mid, E) + vertical (N, mid, S)"""
    out = []
    for k in range(3):
        c = C(16, 16)
        for x in range(16):
            c.rect(x, 4, x, 12, 'w_lt' if x % 3 == 0 else 'w')
            c.px(x, 12, 'w_dk')
        c.rect(0, 2, 15, 3, 'w_dk'); c.rect(0, 2, 15, 2, 'w_lt'); c.rect(0, 13, 15, 14, 'w_ol')
        if k != 1:
            px = 0 if k == 0 else 12
            c.rect(px, 0, px + 3, 4, 'w'); c.rect(px, 0, px + 3, 0, 's'); c.rect(px, 11, px + 3, 15, 'w'); c.rect(px, 11, px + 3, 11, 's')
        out.append(finish(c, 'w_ol'))
    for k in range(3):
        c = C(16, 16)
        for y in range(16):
            c.rect(4, y, 11, y, 'w_lt' if y % 3 == 0 else 'w')
        c.rect(2, 0, 3, 15, 'w_dk'); c.rect(12, 0, 13, 15, 'w_dk'); c.rect(14, 0, 14, 15, 'w_ol'); c.rect(1, 0, 1, 15, 'w_ol')
        out.append(c)
    return out


def waterfall_frames():
    out = []
    for f in range(4):
        c = C(32, 32)
        for y in range(32):
            for x in range(2, 30):
                col = 'wa'
                k = (y - f * 4 + x * 7) % 16
                if x % 5 == 1 and k < 6: col = 'foam' if k < 2 else 'wa_lt'
                elif x % 5 == 3 and k < 4: col = 'wa_dk'
                c.px(x, y, col)
            c.px(1, y, 'w_ol'); c.px(30, y, 'w_ol')
        for x in range(2, 30):
            c.px(x, 31 - (x + f) % 2, 'foam')
        out.append(c)
    return out


# ------------------------------------------------------------- props
def barrel():
    c = C(16, 16)
    c.ellipse(8, 14, 6, 1.8, SHADOW)
    c.rect(3, 4, 12, 13, 'w'); c.rect(3, 4, 4, 13, 'w_lt'); c.rect(11, 4, 12, 13, 'w_dk')
    for y in (6, 11): c.rect(3, y, 12, y, 'st_md')
    c.ellipse(8, 4, 5, 1.6, 'w_lt'); c.ellipse(8, 4, 3.5, 1, 'w_mid')
    return finish(c, 'w_ol')


def crate():
    c = C(16, 16)
    c.ellipse(8, 14, 7, 1.8, SHADOW)
    c.rect(2, 3, 13, 13, 'w'); c.rect(2, 3, 13, 4, 's_dk'); c.rect(2, 3, 2, 13, 'w_lt'); c.rect(13, 3, 13, 13, 'w_dk')
    for i in range(10): c.px(3 + i, 5 + i * 8 // 10, 'w_lt')
    c.rect(2, 8, 13, 8, 'w_dk')
    return finish(c, 'w_ol')


def chest_frames():
    out = []
    for f in range(3):
        c = C(16, 16)
        c.ellipse(8, 14, 7, 1.8, SHADOW)
        c.rect(2, 8, 13, 13, 'w'); c.rect(2, 8, 13, 8, 'w_lt'); c.rect(2, 12, 13, 13, 'w_dk')
        for x in (2, 13): c.rect(x, 8, x, 13, 'yl_dk')
        if f == 0:
            c.rect(2, 4, 13, 7, 'w_lt'); c.rect(2, 4, 13, 4, 's'); c.rect(7, 6, 8, 9, 'yl'); c.px(7, 8, 'w_ol')
        else:
            c.rect(2, 2 - f + 1, 13, 4 - f + 1, 'w_dk'); c.rect(3, 6, 12, 7, 'w_ol')
            for x in range(3, 13, 2): c.px(x, 7, 'yl'); c.px(x + 1, 6, 'yl_dk')
            if f == 2:
                c.px(5, 3, 'sn'); c.px(10, 2, 'sn'); c.px(8, 4, 'yl')
        out.append(finish(c, 'w_ol'))
    return out


def sign():
    c = C(16, 16)
    c.ellipse(8, 14, 4, 1.4, SHADOW)
    c.rect(7, 8, 8, 13, 'w_dk')
    c.rect(2, 3, 13, 8, 'w_lt'); c.rect(2, 3, 13, 3, 's'); c.rect(2, 8, 13, 8, 'w')
    for x in (4, 6, 9, 11): c.px(x, 5, 'w_dk'); c.px(x, 6, 'w_dk') if x % 2 else None
    return finish(c, 'w_ol')


def torch_frames():
    out = []
    for f in range(4):
        c = C(16, 32)
        c.ellipse(8, 30, 3, 1.2, SHADOW)
        c.rect(7, 14, 8, 29, 'w'); c.rect(7, 14, 7, 29, 'w_lt')
        c.rect(5, 12, 10, 14, 'st_md'); c.rect(5, 12, 10, 12, 'st_lt')
        h = [7, 8, 6, 8][f]
        for y in range(h):
            p = y / h
            half = 2.4 * (1 - p) ** .7 + (0.4 if y == 0 else 0)
            sx = 7.5 + math.sin(f * 1.6 + y) * p
            for x in range(int(sx - half), int(sx + half) + 1):
                col = 'yl' if abs(x + .5 - sx) < half * .45 and p < .6 else 'lava_hi' if p < .75 else 'lava'
                c.px(x, 11 - y, col)
        out.append(finish(c, 'w_ol'))
    return out


def campfire_frames():
    out = []
    for f in range(4):
        c = C(16, 16)
        c.ellipse(8, 13, 7, 2, SHADOW)
        for (x, y) in [(2, 12), (5, 13), (10, 13), (13, 12)]:
            c.rect(x, y, x + 1, y, 'st_lt'); c.px(x, y + 1, 'st_md')
        for i in range(8):
            c.px(4 + i, 11 - (i % 2), 'w'); c.px(4 + i, 12 - (i % 2), 'w_dk')
        h = [7, 8, 6, 8][f]
        for y in range(h):
            p = y / h
            half = 3 * (1 - p) ** .8
            sx = 8 + math.sin(f * 1.7 + y * .9) * p
            for x in range(int(sx - half), int(sx + half) + 1):
                col = 'yl' if abs(x + .5 - sx) < half * .4 and p < .5 else 'lava_hi' if p < .7 else 'lava'
                c.px(x, 10 - y, col)
        out.append(finish(c, 'w_ol'))
    return out


def well():
    c = C(24, 28)
    c.ellipse(12, 25, 10, 2.5, SHADOW)
    c.ellipse(12, 19, 9, 5, 'st'); c.ellipse(12, 17, 9, 4, 'st_lt'); c.ellipse(12, 17, 6, 2.4, 'wa_dk')
    for x in (4, 19): c.rect(x, 4, x + 1, 17, 'w')
    tri(c, 2, 21, 0, 6, 'red', 'red_dk')
    c.rect(6, 8, 17, 8, 'w_dk'); c.rect(11, 8, 11, 13, 'st_dk'); c.rect(10, 13, 12, 15, 'w')
    return finish(c, 'w_ol')


def stall():
    """market stall = the shop"""
    c = C(40, 36)
    c.ellipse(20, 33, 18, 2.5, SHADOW)
    c.rect(4, 20, 35, 31, 'w'); c.rect(4, 20, 35, 21, 'w_lt'); c.rect(4, 30, 35, 31, 'w_dk')
    for x in (5, 34): c.rect(x, 6, x + 1, 31, 'w_dk')
    for x in range(3, 37):
        c.rect(x, 4, x, 9, 'red' if (x // 4) % 2 else 'sn')
    c.rect(3, 10, 36, 10, 'red_dk')
    for (x, col) in [(9, 'red'), (14, 'yl'), (20, 'g_lt'), (25, 'pk'), (30, 'yl_dk')]:
        c.ellipse(x, 19, 2, 1.6, col)
    return finish(c, 'w_ol')


def hay():
    c = C(16, 16)
    c.ellipse(8, 14, 6, 1.6, SHADOW)
    c.ellipse(8, 9, 6, 5, 'yl_dk'); c.ellipse(7, 8, 4, 3, 'yl')
    for x in (5, 8, 11): c.px(x, 10, 's_sh')
    return finish(c, 'w_ol')


def wheat():
    c = C(16, 16)
    for x in range(1, 16, 3):
        for y in range(6, 15): c.px(x, y, 'yl_dk' if y > 8 else 'yl')
        c.px(x + 1, 6, 'yl'); c.px(x - 1, 7, 'yl')
    return c


def build_structures():
    made = []
    S = 'Structures/'
    made.append(save(mountain(1), S + 'mountain_snow_a.png'))
    made.append(save(mountain(4, 56, 48), S + 'mountain_snow_b.png'))
    made.append(save(mountain(7, 48, 40, snow=False), S + 'mountain_rock.png'))
    made.append(save(mesa(), S + 'mesa.png'))
    made.append(save(sheet(volcano_frames(), 80, 64), S + 'volcano_anim_80x64.png'))
    made.append(save(sheet(volcano_frames(2.0), 160, 128), S + 'volcano_big_anim_160x128.png'))
    made.append(save(mountain(11, 96, 84), S + 'mountain_big_a.png'))
    made.append(save(mountain(13, 112, 92), S + 'mountain_big_b.png'))
    made.append(save(house(), S + 'house_red.png'))
    made.append(save(house(roof=('wa_dp', 'st_ol')), S + 'house_blue.png'))
    made.append(save(house(roof=('s_md', 's_sh')), S + 'house_thatch.png'))
    made.append(save(stone_wall(), S + 'castle_wall.png'))
    made.append(save(tower(), S + 'castle_tower.png'))
    made.append(save(tower(roof=('red', 'red_dk'), w=34, h=88), S + 'watchtower.png'))
    made.append(save(sheet(windmill_frames(), 72, 104), S + 'windmill_anim_72x104.png'))
    made.append(save(lighthouse(), S + 'lighthouse.png'))
    made.append(save(sheet(dark_tower_frames(), 44, 120), S + 'dark_tower_anim_44x120.png'))
    made.append(save(ruin_wall(), S + 'ruin_wall.png'))
    made.append(save(pillar(), S + 'ruin_pillar.png'))
    made.append(save(sheet(dock_set(), 16, 16), S + 'dock_16x16.png'))
    made.append(save(boat(), S + 'boat.png'))
    made.append(save(sheet(bridge_set(), 16, 16), S + 'bridge_16x16.png'))
    made.append(save(sheet(waterfall_frames(), 32, 32), S + 'waterfall_anim_32x32.png'))
    PR = 'Props/'
    made.append(save(sheet([barrel(), crate(), sign(), hay(), wheat()], 16, 16), PR + 'props_16x16.png'))
    made.append(save(sheet(chest_frames(), 16, 16), PR + 'chest_anim_16x16.png'))
    made.append(save(sheet(torch_frames(), 16, 32), PR + 'torch_anim_16x32.png'))
    made.append(save(sheet(campfire_frames(), 16, 16), PR + 'campfire_anim_16x16.png'))
    made.append(save(well(), PR + 'well.png'))
    made.append(save(stall(), PR + 'market_stall.png'))
    return made


if __name__ == '__main__':
    for p in build_structures(): print(p)
