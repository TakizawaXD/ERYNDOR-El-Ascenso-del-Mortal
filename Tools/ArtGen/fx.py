"""Effects, ambient particles, background, UI — matched to the Tiny RPG characters."""
import math
import numpy as np
from lib import *
from props import flame, K, spr


def ring(c, cx, cy, r, col, th=1.0, ry_scale=1.0):
    """1-px pixel-perfect ellipse ring via angle sampling (no gaps)"""
    seen = set()
    for i in range(720):
        a = i * math.pi / 360
        x, y = int(math.floor(cx + math.cos(a) * r)), int(math.floor(cy + math.sin(a) * r * ry_scale))
        if (x, y) not in seen:
            seen.add((x, y)); c.px(x, y, col)


def disc(c, cx, cy, r, col, ry=None):
    c.ellipse(cx, cy, r, ry or r, col)


# ---------------------------------------------------------------- FX -------
def fx_dust():  # walking dust, 16x16 x5, ground tones
    out = []
    for f in range(5):
        c = Canvas(16, 16)
        puffs = [(6, 12), (10, 12.5), (8, 11)]
        for i, (x, y) in enumerate(puffs):
            r = [1.2, 2.0, 2.4, 2.0, 1.2][f] - i * .3
            if r <= .5:
                continue
            yy = y - f * .6
            xx = x + (i - 1) * f * .5
            disc(c, xx, yy, r, 'd_md' if f > 2 else 'd_hi')
            disc(c, xx - .4, yy - .4, max(.6, r - .9), 'd_hi' if f > 2 else 'c_wht')
        out.append(c)
    return out


def fx_splash():  # water splash 32x32 x5
    out = []
    for f in range(5):
        c = Canvas(32, 32)
        t = f / 4
        ring(c, 16, 24, 3 + t * 9, 'w_lt' if f < 4 else 'w_fo', 1.0, .4)
        for k in range(7):
            a = math.pi * (0.1 + 0.8 * k / 6)
            v = 7 + (k % 3) * 2
            x = 16 - math.cos(a) * v * t * 1.2
            y = 24 - math.sin(a) * v * (t * 2.2 - t * t * 2.0) * 1.6
            if f < 4:
                c.px(x, y, 'w_fo'); c.px(x, y + 1, 'w_lt')
                if k % 2 == 0 and f < 3:
                    c.px(x, y - 1, 'wht')
        if f < 2:
            c.vline(16, 24 - 3 - f * 4, 23, 'w_fo'); c.vline(15, 24 - 1 - f * 3, 23, 'w_lt'); c.vline(17, 24 - 2 - f * 3, 23, 'w_lt')
        out.append(c)
    return out


def fx_hit():  # white impact star, 32x32 x4 (same off-white as the soldier's slash)
    out = []
    for f in range(4):
        c = Canvas(32, 32)
        L = [5, 10, 8, 4][f]
        for k in range(8):
            a = k * math.pi / 4 + (math.pi / 8 if f % 2 else 0)
            ln = L if k % 2 == 0 else L * .55
            for i in range(int(ln)):
                x, y = 16 + math.cos(a) * i, 16 + math.sin(a) * i
                c.px(x, y, 'c_wht' if i < ln * .6 else 'c_gry')
        if f < 2:
            disc(c, 16, 16, [3, 2.2][f], 'wht')
            disc(c, 16, 16, [1.5, 1][f], 'y')
        out.append(c)
    return out


def fx_blood():  # blood burst for Blood Monster / hurt, 32x32 x5
    out = []
    r = rng(7)
    drops = [(r.uniform(0, 2 * math.pi), r.uniform(4, 11), r.uniform(.8, 1.8)) for _ in range(11)]
    for f in range(5):
        c = Canvas(32, 32)
        t = f / 4
        for (a, v, s) in drops:
            x = 16 + math.cos(a) * v * t
            y = 16 + math.sin(a) * v * t + 6 * t * t
            sz = s * (1 - t * .6)
            disc(c, x, y, max(.6, sz), 'c_red' if f > 1 else 'c_bld')
            if sz > 1.1:
                c.px(x - .5, y - .5, 'c_bld' if f < 3 else 'c_red')
        if f < 2:
            disc(c, 16, 16, 3.5 - f * 1.5, 'c_bld'); disc(c, 15.5, 15.5, 1.5 - f * .5, 'pk')
        if f >= 3:
            for (x, y) in [(13, 27), (18, 28), (21, 26)]:
                c.ellipse(x, y, 1.6, .8, 'c_red2')
        if f < 2:
            c.outline('c_red3')
        out.append(c)
    return out


def fx_poof():  # death / spawn smoke poof, 32x32 x6
    out = []
    puffs = [(16, 18, 4), (11, 17, 3), (21, 17, 3), (13, 13, 3), (19, 13, 3), (16, 21, 3)]
    for f in range(6):
        c = Canvas(32, 32)
        t = f / 5
        for i, (x, y, r) in enumerate(puffs):
            rr = r * (0.5 + t * 1.2) * (1 - max(0, t - .6) * 1.8)
            if rr < .6:
                continue
            cx = 16 + (x - 16) * (1 + t * 1.2)
            cy = 18 + (y - 18) * (1 + t * 1.2) - t * 4
            disc(c, cx, cy, rr, 'c_gry2' if f > 2 else 'c_gry')
            disc(c, cx - rr * .3, cy - rr * .3, rr * .6, 'c_wht' if f < 4 else 'c_gry')
        if 0 < f < 5:
            c.outline('s_md')
        out.append(c)
    return out


def fx_explosion():  # 48x48 x7
    out = []
    for f in range(7):
        c = Canvas(48, 48)
        t = f / 6
        R = 5 + t * 15
        if f <= 4:
            disc(c, 24, 26, R, 'c_red2' if f > 2 else 'or_')
            disc(c, 24, 25, R * .78, 'or_' if f > 2 else 'o')
            disc(c, 23, 24, R * .5, 'o' if f > 1 else 'y')
            if f < 3:
                disc(c, 23, 23, R * .3, 'wht' if f < 2 else 'y')
        else:
            for (x, y, r) in [(18, 22, 7), (29, 21, 7), (24, 16, 6), (24, 27, 7)]:
                rr = r * (1.3 - (f - 5) * .45)
                disc(c, x, y - (f - 4) * 3, rr, 's_md' if f == 5 else 's_wm')
                disc(c, x - 1, y - 1 - (f - 4) * 3, rr * .6, 's_wm' if f == 5 else 'c_gry2')
        # debris sparks
        if 1 <= f <= 4:
            for k in range(10):
                a = k * 2 * math.pi / 10 + .3
                d = R + 3 + f * 1.5
                c.px(24 + math.cos(a) * d, 25 + math.sin(a) * d, 'y' if k % 2 else 'o')
        if f <= 4:
            c.outline('c_red3')
        out.append(c)
    return out


def fx_fire():  # loopable fire, 16x24 x4
    out = []
    for f in range(4):
        c = Canvas(16, 24)
        flame(c, 8, 22, 15, 5, f, seed=2)
        flame(c, 5, 22, 8, 2.5, (f + 2) % 4, seed=5)
        flame(c, 11, 22, 9, 2.5, (f + 1) % 4, seed=9)
        out.append(c)
    return out


def fx_demon_fireball():  # projectile 16x16 x4, faces right
    out = []
    for f in range(4):
        c = Canvas(16, 16)
        for k in range(5):  # trail
            x = 9 - k * 1.8
            y = 8 + math.sin(f * 1.57 + k) * .8
            disc(c, x, y, max(.6, 2.6 - k * .45), ['c_bld', 'c_red', 'c_red2', 'pu', 'pu_dk'][k])
        disc(c, 10.5, 8, 3.2, 'c_bld')
        disc(c, 11, 7.5, 2.0, 'pk')
        c.px(11, 7, 'wht'); c.px(12, 7, 'wht') if f % 2 else None
        c.outline('c_red3')
        out.append(c)
    return out


def fx_sparkle():  # pickup twinkle 16x16 x5
    out = []
    for f in range(5):
        c = Canvas(16, 16)
        L = [1, 3, 5, 3, 1][f]
        for i in range(-L, L + 1):
            col = 'wht' if abs(i) < 2 else 'y'
            c.px(8 + i, 8, col); c.px(8, 8 + i, col)
        if f in (1, 2, 3):
            for d in (1, 2) if f == 2 else (1,):
                for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                    c.px(8 + sx * d, 8 + sy * d, 'y')
        if f >= 2:
            c.px(3, 4 - (f - 2), 'y'); c.px(12, 12 - (f - 2), 'wht')
        out.append(c)
    return out


def fx_heal():  # green crosses rising, 32x32 x6
    out = []
    crosses = [(10, 24, 0), (20, 26, 1), (15, 22, 2), (24, 21, 3)]
    for f in range(6):
        c = Canvas(32, 32)
        for (x, y, d) in crosses:
            k = f - d * .5
            if k < 0 or k > 4:
                continue
            yy = y - k * 4
            col = 'g_hi' if k < 3 else 'g_lt'
            c.hline(x - 2, x + 2, yy, col); c.vline(x, yy - 2, yy + 2, col); c.px(x, yy, 'wht'); c.px(x - 1, yy, 'wht') if k < 2 else None
        c.outline((26, 122, 62, 160))
        out.append(c)
    return out


def fx_magic_circle():  # demon summon circle 32x32 x4 (ground plane, loop)
    out = []
    for f in range(4):
        c = Canvas(32, 32)
        ring(c, 16, 16, 13, 'c_red', 1.0, .5)
        ring(c, 16, 16, 9.5, 'c_red2', 1.0, .5)
        for k in range(6):
            a = k * math.pi / 3 + f * math.pi / 12
            x, y = 16 + math.cos(a) * 11.3, 16 + math.sin(a) * 11.3 * .5
            c.px(x, y, 'c_bld' if (k + f) % 2 else 'pk')
            c.px(x + 1, y, 'c_bld')
        for k in range(12):  # rune ticks inside the inner ring, rotating the other way
            a = k * math.pi / 6 - f * math.pi / 24
            if k % 3 == 0:
                continue
            x, y = 16 + math.cos(a) * 7.5, 16 + math.sin(a) * 7.5 * .5
            c.px(x, y, 'pu')
        c.ellipse(16, 16, 3.5, 1.6, (237, 13, 13, 90 + 30 * (f % 2)))
        out.append(c)
    return out


# ----------------------------------------------------------- ambient ------
def amb_leaf():  # 8x8 x4 tumbling leaf
    shapes = [
        ["..Gv", ".Gvx", "Gvx.", "gG.."],
        ["....", "Gvvx", "gGG.", "...."],
        ["Gv..", "gvG.", ".gvG", "..gG"],
        [".G..", ".vG.", ".vx.", ".gG."],
    ]
    return [spr(8, 8, s, ox=2, oy=2) for s in shapes]


def amb_firefly():  # 8x8 x4 glow pulse
    out = []
    for f in range(4):
        c = Canvas(8, 8)
        a = [30, 70, 110, 70][f]
        for y in range(8):
            for x in range(8):
                d = math.hypot(x + .5 - 4, y + .5 - 4)
                if d < 3.6:
                    c.a[y, x] = (255, 252, 64, int(a * (1 - d / 3.6)))
        c.px(4, 4, 'y' if f else 'o'); c.px(3, 4, 'y') if f == 2 else None
        out.append(c)
    return out


def amb_rain():  # drop 8x8 + splash 3 frames
    out = []
    c = Canvas(8, 8); c.vline(4, 1, 5, (188, 224, 242, 200)); c.px(4, 6, (255, 255, 255, 220)); out.append(c)
    for f in range(3):
        c = Canvas(8, 8)
        r = 1 + f
        c.px(4 - r, 6, 'w_fo'); c.px(4 + r, 6, 'w_fo')
        if f < 2: c.px(4, 5 - f, 'w_fo'); c.px(4 - r + 1, 5, 'w_lt'); c.px(4 + r - 1, 5, 'w_lt')
        out.append(c)
    return out


def amb_motes():  # pollen / dust 4x4 x2
    a = Canvas(4, 4); a.px(1, 1, (244, 210, 156, 230)); a.px(2, 1, (244, 210, 156, 120)); a.px(1, 2, (244, 210, 156, 120))
    b = Canvas(4, 4); b.px(1, 1, (255, 255, 255, 200)); b.px(2, 2, (255, 255, 255, 90))
    return [a, b]


def amb_cloud_shadow():  # 96x48, very soft; drift slowly over the map
    c = Canvas(96, 48)
    for (x, y, r) in [(28, 26, 16), (48, 20, 19), (68, 26, 15), (40, 32, 13), (58, 32, 13)]:
        for yy in range(48):
            for xx in range(96):
                if math.hypot(xx + .5 - x, (yy + .5 - y) * 1.3) <= r:
                    c.a[yy, xx] = (20, 16, 40, 38)
    return c


def amb_fog():  # 64x64 seamless fog tile, 2px pixel blocks
    c = Canvas(64, 64)
    r = rng(77)
    ph = [r.uniform(0, 6.28) for _ in range(4)]
    for y in range(0, 64, 2):
        for x in range(0, 64, 2):
            v = (math.sin(2 * math.pi * x / 64 + ph[0]) + math.sin(2 * math.pi * (x + y) / 64 + ph[1])
                 + math.sin(2 * math.pi * 2 * y / 64 + ph[2]) + .5 * math.sin(2 * math.pi * (2 * x - y) / 64 + ph[3]))
            a = max(0, v) / 3.5
            a = round(a * 4) / 4  # posterise = pixel-art friendly bands
            if a > 0:
                for dy in (0, 1):
                    for dx in (0, 1):
                        c.a[y + dy, x + dx] = (236, 240, 246, int(a * 70))
    return c


def amb_light_ray():  # 32x64 god-ray, diagonal
    c = Canvas(32, 64)
    for y in range(64):
        for x in range(32):
            u = x - y * .35
            if 2 < u < 18:
                edge = min(u - 2, 18 - u) / 8
                fade = 1 - y / 64
                a = int(min(1, edge) * fade * 55)
                a = (a // 11) * 11
                if a:
                    c.a[y, x] = (255, 250, 200, a)
    return c


# ------------------------------------------------------------------- UI ---
UIK = dict(K)
UIK.update({'#': 'blk', '-': 'c_blk'})


def ui_panel():  # 48x48, 9-slice border 8: wooden frame + parchment
    c = Canvas(48, 48)
    c.rect(0, 0, 47, 47, 'd_ol')
    c.rect(1, 1, 46, 46, 'd_br'); c.hline(1, 46, 1, 'd_rd'); c.vline(1, 1, 46, 'd_rd')
    c.rect(2, 2, 45, 45, 'd_rd'); c.hline(2, 45, 2, 'd_md'); c.vline(2, 2, 45, 'd_md')
    c.hline(2, 45, 45, 'd_br'); c.vline(45, 2, 45, 'd_br')
    for x in range(4, 44, 6):  # wood grain
        c.px(x, 3, 'd_br'); c.px(x + 2, 44, 'd_dk')
    c.rect(4, 4, 43, 43, 'd_ol')
    c.rect(5, 5, 42, 42, 'd_hi'); c.hline(5, 42, 5, 'd_md'); c.vline(5, 5, 42, 'd_md')
    for (x, y) in [(1, 1), (44, 1), (1, 44), (44, 44)]:  # corner rivets
        c.rect(x, y, x + 2, y + 2, 's_lt'); c.px(x, y, 's_hi'); c.px(x + 2, y + 2, 's_dk')
    return c


def ui_dialog():  # 48x32 dark dialog box, 9-slice border 6
    c = Canvas(48, 32)
    c.rect(0, 0, 47, 31, 'blk')
    c.rect(1, 1, 46, 30, 's_lt'); c.hline(1, 46, 1, 's_hi')
    c.rect(2, 2, 45, 29, 's_dk'); c.rect(3, 3, 44, 28, 'blk')
    c.rect(4, 4, 43, 27, 's_ol')
    for (x, y) in [(1, 1), (45, 1), (1, 29), (45, 29)]:
        c.rect(x, y, x + 1, y + 1, 'o')
    return c


def ui_buttons():  # 3 states x 48x16, 9-slice border 4
    out = []
    for st in range(3):
        c = Canvas(48, 16)
        top = 0 if st < 2 else 1
        c.rect(0, top, 47, 15, 'd_ol')
        face = {0: ('d_md', 'd_hi', 'd_br'), 1: ('d_hi', 'wht', 'd_md'), 2: ('d_br', 'd_md2', 'd_dk')}[st]
        c.rect(1, top + 1, 46, 13, face[0])
        c.hline(1, 46, top + 1, face[1]); c.vline(1, top + 1, 13, face[1])
        if st < 2:
            c.hline(1, 46, 13, face[2]); c.hline(1, 46, 14, 'd_dk2')
        out.append(c)
    return out


def ui_slots():  # 20x20 normal / selected / disabled, 9-slice border 4
    out = []
    for st in range(3):
        c = Canvas(20, 20)
        c.rect(0, 0, 19, 19, 'd_ol')
        c.rect(1, 1, 18, 18, 'd_dk2' if st != 2 else 's_dk2')
        c.hline(1, 18, 1, 'd_ol'); c.vline(1, 1, 18, 'd_ol')
        c.hline(2, 18, 18, 'd_dk' if st != 2 else 's_dk')
        if st == 1:
            for i in range(20):
                for (x, y) in [(i, 0), (i, 19), (0, i), (19, i)]:
                    c.px(x, y, 'y')
            for (x, y) in [(0, 0), (19, 0), (0, 19), (19, 19)]:
                c.px(x, y, 'o')
        out.append(c)
    return out


def ui_bars():  # frame 64x10 (9s 3), fills 1-row tile-able 8x6: hp, stamina, mana, empty
    fr = Canvas(64, 10)
    fr.rect(0, 0, 63, 9, 'blk'); fr.rect(1, 1, 62, 8, 's_ol'); fr.hline(1, 62, 1, 's_dk2')
    for (x, y) in [(0, 0), (63, 0), (0, 9), (63, 9)]:
        fr.a[y, x] = (0, 0, 0, 0)
    fills = []
    for (a, b, c_) in [('pk', 'c_bld', 'c_red'), ('g_hi', 'g_lt', 'g_md'), ('w_fo', 'w_lt', 'w_bl'), ('s_md', 's_dk', 's_dk2')]:
        c = Canvas(8, 6)
        c.rect(0, 0, 7, 5, b); c.hline(0, 7, 0, a); c.hline(0, 7, 1, a) if False else None
        c.hline(0, 7, 4, c_); c.hline(0, 7, 5, c_)
        fills.append(c)
    return fr, fills


def ui_hearts():  # 16x16 full / half / empty
    rows = [
        "..##..##..",
        ".#6b#b66#.",
        "#6Abbbbbb#",
        "#6bbbbbbr#",
        "#bbbbbbrr#",
        ".#bbbbrr#.",
        "..#bbrr#..",
        "...#rr#...",
        "....##....",
    ]
    k = dict(UIK)
    full = spr(16, 16, rows, oy=3)
    half_rows = [r[:5] + r[5:].replace('b', 's').replace('r', 't').replace('6', 's').replace('A', 's') for r in rows]
    half = spr(16, 16, half_rows, oy=3)
    empty_rows = [r.replace('b', 's').replace('r', 't').replace('6', 's').replace('A', 'm') for r in rows]
    empty = spr(16, 16, empty_rows, oy=3)
    return [full, half, empty]


ICONS = {
    'sword': [
        "...........##.",
        "..........#cA#",
        ".........#cC#.",
        "........#cC#..",
        ".......#cC#...",
        "..#...#cC#....",
        "..##.#cC#.....",
        "...##cC#......",
        "....#Y#.......",
        "...#YK##......",
        "..#BK#.##.....",
        ".#BK#.........",
        ".##...........",
    ],
    'axe': [
        "......###.....",
        ".....#cAC#....",
        "....#cAACC#...",
        "....#cAC#C#...",
        ".....##RCt#...",
        ".....#RK##....",
        "....#RK#......",
        "...#RK#.......",
        "..#RK#........",
        ".#RK#.........",
        ".##...........",
    ],
    'bow': [
        "...####.......",
        "..#lRR#C......",
        "...##.#RC.....",
        "......#RC.....",
        ".......#RC....",
        ".......#RC....",
        ".......#RC....",
        "......#RC.....",
        "......#RC.....",
        "...##.#RC.....",
        "..#lRR#C......",
        "...####.......",
    ],
    'arrow': [
        "..........###",
        ".........#cA#",
        "........#cC#.",
        ".......#RC#..",
        "......#R#....",
        ".....#R#.....",
        "..#.#R#......",
        "..##R#.......",
        "..#R##.......",
        ".#C###.......",
        "#C#..........",
    ],
    'shield': [
        "..#########..",
        ".#pqqooooom#.",
        ".#qbbbbbbbm#.",
        ".#qbbYYbbbm#.",
        ".#obYyyYbbm#.",
        ".#obbYYbbrm#.",
        "..#obbbbrm#..",
        "..#obbbrrm#..",
        "...#obrrm#...",
        "....#omm#....",
        ".....###.....",
    ],
    'potion_red': [
        "....###....",
        "...#lRB#...",
        "....#C#....",
        "...#WAW#...",
        "..#WcCCW#..",
        ".#bAbbbbr#.",
        ".#b6bbbbr#.",
        ".#bbbbbrr#.",
        ".#rbbbrre#.",
        "..#rrrre#..",
        "...#####...",
    ],
    'potion_blue': [
        "....###....",
        "...#lRB#...",
        "....#C#....",
        "...#WAW#...",
        "..#WcCCW#..",
        ".#UAUUUUi#.",
        ".#UWUUUUi#.",
        ".#UUUUUii#.",
        ".#iUUUiij#.",
        "..#iiiij#..",
        "...#####...",
    ],
    'coin': [
        "...####...",
        "..#yyyY#..",
        ".#yAyYYF#.",
        ".#yyYyYF#.",
        ".#yyYyYF#.",
        ".#yyYyYF#.",
        ".#YyyYFF#.",
        "..#FFFF#..",
        "...####...",
    ],
    'key': [
        "..###.......",
        ".#yAy#......",
        "#y#.#Y#.....",
        "#Y#.#F#.....",
        ".#YFF####...",
        "..##YyyyY#..",
        "....###Y#Y#.",
        "......#F##F#",
        ".......#..#.",
    ],
    'mushroom': [
        "...####...",
        "..#bAbb#..",
        ".#bAbbcb#.",
        "#bbbbbbbr#",
        "#cbbcbbrr#",
        ".####r###.",
        "...#cC#...",
        "...#cC#...",
        "...####...",
    ],
    'meat': [
        "....#####...",
        "...#6bbbr#..",
        "..#6Abbbrr#.",
        "..#bbbbbrr#.",
        "..#rbbbrre#.",
        "...#rrree#..",
        "...##eee#...",
        "..#cA###....",
        ".#cC#.......",
        ".##.........",
    ],
    'scroll': [
        ".#########.",
        "#hlhhhhhlL#",
        ".#hhhhhhL#.",
        ".#h--h-hL#.",
        ".#hhhhhhL#.",
        ".#h-h--hL#.",
        ".#hhhhhhL#.",
        "#hlhhhhhlL#",
        ".#########.",
    ],
    'skull': [
        "..######..",
        ".#cAcccC#.",
        "#cAccccCC#",
        "#c##cc##C#",
        "#c#b#c#bC#",
        "#cc##C##C#",
        ".#cCc#CC#.",
        "..#c#C#C#.",
        "..#######.",
    ],
    'gem_demon': [
        "...#####...",
        "..#6AbbE#..",
        ".#6Abbbre#.",
        "#bbbbbbrre#",
        ".#rbbbrre#.",
        "..#rbbre#..",
        "...#rre#...",
        "....#e#....",
        ".....#.....",
    ],
}


def ui_icons():
    out = []
    for name, rows in ICONS.items():
        c = Canvas(16, 16)
        rw = max(len(r) for r in rows)
        t = Canvas(16, 16); t.sprite(rows, UIK, (16 - rw) // 2, (16 - len(rows)) // 2)
        c.paste(t, 0, 0)
        out.append(c)
    return out


def ui_prompts():  # 16x16: key E (2 frames bob), "!" bubble, "?" bubble
    out = []
    for f in range(2):
        rows = [
            ".##########.",
            "#cAAAAAAAAC#",
            "#Ac######CC#",
            "#Ac#AAAACCC#",
            "#Ac###ACCCC#",
            "#Ac#AAAACCC#",
            "#Ac######CC#",
            "#CCCCCCCCCC#",
            "#ssssssssss#",
            ".##########.",
        ]
        out.append(spr(16, 16, rows, oy=3 - f))
    for sym in ('!', '?'):
        body = [
            ".#########.",
            "#AAAAAAAAc#",
            "#AAAA{}AAc#",
            "#AAAA{}AAc#",
            "#AAAA{}AAc#",
            "#AAAAAAAAc#",
            "#AAAA{}AAc#",
            "#cccccccCC#",
            ".###..####.",
            "....#.#....",
            ".....#.....",
        ]
        if sym == '!':
            body = [r.replace('{}', 'bb') for r in body]
        else:
            body[2] = "#AAA#####c#"[:0] + "#AAAyyyAAc#"
            body[3] = "#AAAAAyAAc#"
            body[4] = "#AAAAyAAAc#"
            body[6] = "#AAAAyAAAc#"
            body = [r.replace('{}', 'AA') for r in body]
            body = [r.replace('y', 'Y') for r in body]
        out.append(spr(16, 16, body, oy=2))
    return out


def ui_cursors():  # pointer + target reticle 16x16
    ptr = [
        "#.........",
        "##........",
        "#A#.......",
        "#AA#......",
        "#AAA#.....",
        "#AAAA#....",
        "#AAAAA#...",
        "#AAAAAA#..",
        "#AAA####..",
        "#A#A#.....",
        "##.#A#....",
        "#..#A#....",
        "....##....",
    ]
    a = spr(16, 16, ptr, ox=1, oy=1)
    b = Canvas(16, 16)
    ring(b, 8, 8, 5.5, 'c_bld', 1.2)
    for (x0, y0, x1, y1) in [(7, 0, 8, 3), (7, 12, 8, 15), (0, 7, 3, 8), (12, 7, 15, 8)]:
        b.rect(x0, y0, x1, y1, 'c_wht')
    b.px(7, 7, 'c_bld'); b.px(8, 8, 'c_bld'); b.px(7, 8, 'c_bld'); b.px(8, 7, 'c_bld')
    b.outline('blk')
    return [a, b]


def build():
    out = []
    S = save
    out.append(S(sheet(fx_dust(), 16, 16), 'Effects/fx_dust_walk_anim_16x16.png'))
    out.append(S(sheet(fx_splash(), 32, 32), 'Effects/fx_water_splash_anim_32x32.png'))
    out.append(S(sheet(fx_hit(), 32, 32), 'Effects/fx_hit_spark_anim_32x32.png'))
    out.append(S(sheet(fx_blood(), 32, 32), 'Effects/fx_blood_burst_anim_32x32.png'))
    out.append(S(sheet(fx_poof(), 32, 32), 'Effects/fx_smoke_poof_anim_32x32.png'))
    out.append(S(sheet(fx_explosion(), 48, 48), 'Effects/fx_explosion_anim_48x48.png'))
    out.append(S(sheet(fx_fire(), 16, 24), 'Effects/fx_fire_loop_anim_16x24.png'))
    out.append(S(sheet(fx_demon_fireball(), 16, 16), 'Effects/fx_demon_fireball_anim_16x16.png'))
    out.append(S(sheet(fx_sparkle(), 16, 16), 'Effects/fx_pickup_sparkle_anim_16x16.png'))
    out.append(S(sheet(fx_heal(), 32, 32), 'Effects/fx_heal_anim_32x32.png'))
    out.append(S(sheet(fx_magic_circle(), 32, 32), 'Effects/fx_demon_summon_circle_anim_32x32.png'))
    out.append(S(sheet(amb_leaf(), 8, 8), 'Environments/Ambient/amb_leaf_fall_anim_8x8.png'))
    out.append(S(sheet(amb_firefly(), 8, 8), 'Environments/Ambient/amb_firefly_anim_8x8.png'))
    out.append(S(sheet(amb_rain(), 8, 8), 'Environments/Ambient/amb_rain_8x8.png'))
    out.append(S(sheet(amb_motes(), 4, 4), 'Environments/Ambient/amb_motes_4x4.png'))
    out.append(S(amb_cloud_shadow(), 'Environments/Ambient/amb_cloud_shadow.png'))
    out.append(S(amb_fog(), 'Environments/Ambient/amb_fog_tile_seamless.png'))
    out.append(S(amb_light_ray(), 'Environments/Ambient/amb_light_ray.png'))
    out.append(S(ui_panel(), 'UI/ui_panel_wood_9s8.png'))
    out.append(S(ui_dialog(), 'UI/ui_dialog_box_9s6.png'))
    out.append(S(sheet(ui_buttons(), 48, 16), 'UI/ui_button_states_48x16_9s4.png'))
    out.append(S(sheet(ui_slots(), 20, 20), 'UI/ui_inventory_slot_20x20_9s4.png'))
    fr, fills = ui_bars()
    out.append(S(fr, 'UI/ui_bar_frame_9s3.png'))
    out.append(S(sheet(fills, 8, 6), 'UI/ui_bar_fills_8x6.png'))
    out.append(S(sheet(ui_hearts(), 16, 16), 'UI/ui_hearts_16x16.png'))
    out.append(S(sheet(ui_icons(), 16, 16, 7), 'UI/Icons/ui_icons_items_16x16.png'))
    out.append(S(sheet(ui_prompts(), 16, 16), 'UI/ui_prompts_16x16.png'))
    out.append(S(sheet(ui_cursors(), 16, 16), 'UI/ui_cursors_16x16.png'))
    return out


if __name__ == '__main__':
    for p in build():
        print(p)
