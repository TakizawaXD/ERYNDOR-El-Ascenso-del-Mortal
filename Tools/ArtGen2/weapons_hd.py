"""Weapon & armour icons drawn from continuous shapes at any size (16 px slots, 32 px shop/inventory portraits).

Melee weapons lie on the diagonal (grip bottom-left, tip top-right). For every pixel we compute u (along the weapon,
0 = pommel .. 1 = tip) and v (across, + = lower-right side) and ask each part whether it covers that point; shading
comes from v (lit upper-left edge, dark lower-right edge) plus a specular line on blades. A 1 px dark outline closes it.

  python weapons_hd.py -> Assets/Art/UI/Icons/ui_items_16x16.png + ui_items_32x32.png  (same order as ItemDB icons)
                          Documentation/Previews/weapons_preview.png
"""
import math, os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUTLINE = (20, 16, 30, 255)


def hx(s):
    s = s.lstrip('#'); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


def ramp(*c): return [hx(x) for x in c]          # light .. dark


STEEL = ramp('#ffffff', '#d4dce8', '#9aa6bc', '#5f6a85')
DSTEEL = ramp('#b8c0d4', '#7b84a0', '#4f5772', '#30354a')
MOON = ramp('#e8fbff', '#9fdcf5', '#5aa6d8', '#2c5f96')
FIRE = ramp('#fff3b0', '#ffb648', '#f2652a', '#9e2835')
FROST = ramp('#ffffff', '#bfe9ff', '#7cc4f0', '#3a7bd5')
VENOM = ramp('#efffb0', '#b8e650', '#6fae2c', '#2f6420')
GOLD = ramp('#fff6c8', '#ffd25a', '#e09a2c', '#9a5a1e')
RUNE = ramp('#ffe6f6', '#e48ad0', '#a8509c', '#5a2a66')
BONE = ramp('#ffffff', '#ece4d2', '#c9bca0', '#8f8068')
WOOD = ramp('#d79a64', '#b0703f', '#8a4f2c', '#5a3220')
DWOOD = ramp('#8a6a52', '#5f4636', '#3f2c24', '#26191a')
LEATHER = ramp('#9a5a3a', '#743f2c', '#52281e', '#331812')
BLUEGRIP = ramp('#5a8be0', '#2f5fb0', '#1d3c78', '#122650')
REDGRIP = ramp('#e05a5a', '#b02f3c', '#781d2a', '#4a1018')
BLACK = ramp('#5a5470', '#3a344c', '#26213a', '#16121f')


def shade(r, t, spec=False):
    """t in [-1,1] across the part: -1 lit edge .. +1 dark edge"""
    if spec and -0.55 < t < -0.15: return r[0]
    if t < -0.45: return r[1]
    if t < 0.35: return r[2] if spec else r[1]
    return r[3] if t > 0.7 else r[2]


class Icon:
    def __init__(self, n):
        self.n = n
        self.a = np.zeros((n, n, 4), np.uint8)
        self.z = np.full((n, n), -1e9)          # simple painter's order by layer

    def put(self, x, y, c, layer):
        if 0 <= x < self.n and 0 <= y < self.n and layer >= self.z[y, x]:
            self.a[y, x] = c; self.z[y, x] = layer

    def finish(self, outline=True):
        if outline:
            m = self.a[:, :, 3] > 0
            o = np.zeros_like(m)
            o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
            o &= ~m
            self.a[o] = OUTLINE
        return Image.fromarray(self.a, 'RGBA')


# ------------------------------------------------------------------ diagonal weapons
def diagonal(n, parts, length=0.92, curve=0.0):
    """parts: list of (u0, u1, halfwidth(u)->float in px@32, ramp, kind, layer, side) ; side 0 = centred, +1 = only v>0"""
    ic = Icon(n)
    k = n / 32.0
    # axis from (2,30) to (30,2) at 32 px, scaled
    x0, y0, x1, y1 = 2.5 * k, (n - 2.5 * k), n - 2.5 * k, 2.5 * k
    L = math.hypot(x1 - x0, y1 - y0) * length
    ux, uy = (x1 - x0) / math.hypot(x1 - x0, y1 - y0), (y1 - y0) / math.hypot(x1 - x0, y1 - y0)
    vx, vy = -uy, ux                      # perpendicular (points to lower-right)
    for py in range(n):
        for px in range(n):
            cx, cy = px + 0.5 - x0, py + 0.5 - y0
            u = (cx * ux + cy * uy) / L
            v = (cx * vx + cy * vy) / k                                # in 32-px units
            v -= curve * 6 * max(0.0, u - 0.3) ** 2                     # katana sweep
            for (u0, u1, hw, rp, kind, layer, side) in parts:
                if not (u0 <= u <= u1): continue
                t = (u - u0) / max(1e-6, u1 - u0)
                w = hw(t)
                if not isinstance(w, tuple) and w <= 0: continue
                if side == 0:
                    if abs(v) > w: continue
                    tt = v / w
                else:
                    vv = v * side
                    lo, hi = w if isinstance(w, tuple) else (0, w)
                    if isinstance(w, tuple): lo, hi = w
                    if not (lo <= vv <= hi): continue
                    tt = -1 + 2 * (vv - lo) / max(1e-6, hi - lo)
                if kind == 'blade':
                    col = shade(rp, tt, True)
                    if abs(tt) < 0.12 and 0.08 < t < 0.75 and n >= 32: col = rp[2]          # fuller groove
                elif kind == 'wrap':
                    band = int(t * (6 if n >= 32 else 3)) % 2
                    col = rp[1] if band == 0 and tt < 0.3 else rp[2] if tt < 0.5 else rp[3]
                elif kind == 'gem':
                    col = rp[0] if tt < -0.3 else rp[1] if tt < 0.4 else rp[3]
                else:
                    col = shade(rp, tt)
                ic.put(px, py, col, layer)
    return ic


def taper(w, tip=0.18, base=1.0):
    return lambda t: w * (base if t < 1 - tip else max(0.0, (1 - t) / tip) ** 0.8)


def const(w): return lambda t: w


def leaf(w): return lambda t: w * math.sin(math.pi * min(1, t) ** 0.8)


def sword(blade=STEEL, guard=GOLD, grip=LEATHER, gem=None, bw=2.6, blen=0.66, gw=6.5, curve=0.0, pommel=None):
    g0 = 0.25
    parts = [
        (0.03, 0.08, lambda t: 1.8 * math.sin(math.pi * t) + 0.6, pommel or guard, 'metal', 3, 0),
        (0.07, g0, const(1.15), grip, 'wrap', 1, 0),
        (g0, g0 + 0.045, lambda t: gw, guard, 'metal', 4, 0),
        (g0 + 0.04, g0 + 0.04 + blen, taper(bw), blade, 'blade', 2, 0),
    ]
    if gem: parts.append((g0 - 0.005, g0 + 0.05, lambda t: 1.3, gem, 'gem', 5, 0))
    return lambda n: diagonal(n, parts, curve=curve)


def dagger(blade=STEEL, gem=None):
    return sword(blade, GOLD, LEATHER, gem, bw=2.4, blen=0.42, gw=4.5)


def rapier():
    parts = [
        (0.04, 0.09, lambda t: 1.6 * math.sin(math.pi * t) + 0.5, GOLD, 'metal', 3, 0),
        (0.08, 0.24, const(1.0), REDGRIP, 'wrap', 1, 0),
        (0.2, 0.3, lambda t: 3.6 * math.sin(math.pi * t), GOLD, 'metal', 4, 0),           # cup hilt
        (0.27, 1.0, taper(1.0, 0.1), STEEL, 'blade', 2, 0),
    ]
    return lambda n: diagonal(n, parts)


def polearm(head, metal=STEEL, shaft=WOOD, accent=None):
    parts = [(0.0, 0.72, const(1.05), shaft, 'metal', 1, 0), (0.0, 0.05, const(1.3), DSTEEL, 'metal', 2, 0)]
    if head == 'spear':
        parts += [(0.66, 1.0, leaf(2.6), metal, 'blade', 3, 0), (0.62, 0.68, const(1.6), accent or GOLD, 'metal', 4, 0)]
    elif head == 'halberd':
        parts += [(0.74, 1.0, taper(1.3, 0.3), metal, 'blade', 3, 0),
                  (0.58, 0.8, lambda t: (0.5, 6.5 * math.sin(math.pi * t) ** 0.7), metal, 'blade', 3, 1),
                  (0.64, 0.72, lambda t: (0.5, 2.8), metal, 'metal', 3, -1),
                  (0.6, 0.66, const(1.6), DSTEEL, 'metal', 4, 0)]
    else:  # trident
        parts += [(0.62, 0.7, const(4.6), metal, 'metal', 3, 0),
                  (0.68, 1.0, taper(1.0, 0.25), metal, 'blade', 3, 0),
                  (0.66, 0.92, lambda t: (3.4, 4.6), metal, 'blade', 3, 1),
                  (0.66, 0.92, lambda t: (3.4, 4.6), metal, 'blade', 3, -1),
                  (0.6, 0.66, const(1.5), accent or GOLD, 'gem', 4, 0)]
    return lambda n: diagonal(n, parts)


def axe(metal=STEEL, double=False, shaft=WOOD):
    head = lambda t: (0.6, 1.0 + 7.5 * math.sin(math.pi * t) ** 0.6)
    parts = [(0.0, 0.84, const(1.15), shaft, 'metal', 1, 0), (0.0, 0.05, const(1.4), DSTEEL, 'metal', 2, 0),
             (0.6, 0.86, head, metal, 'blade', 3, 1), (0.66, 0.8, const(1.6), DSTEEL, 'metal', 4, 0)]
    if double: parts.append((0.6, 0.86, head, metal, 'blade', 3, -1))
    else: parts.append((0.67, 0.79, lambda t: (0.6, 2.4), DSTEEL, 'metal', 3, -1))
    return lambda n: diagonal(n, parts)


def hammer(metal=DSTEEL, holy=False):
    parts = [(0.0, 0.74, const(1.15), WOOD if not holy else DWOOD, 'metal', 1, 0), (0.0, 0.05, const(1.4), DSTEEL, 'metal', 2, 0),
             (0.68, 0.92, const(6.2), metal, 'metal', 3, 0),
             (0.72, 0.76, const(6.6), GOLD if holy else DSTEEL, 'metal', 4, 0),
             (0.84, 0.88, const(6.6), GOLD if holy else DSTEEL, 'metal', 4, 0)]
    if holy: parts += [(0.92, 1.0, leaf(2.0), GOLD, 'gem', 4, 0), (0.77, 0.83, const(1.4), ramp('#ffffff', '#fff3a0', '#ffd25a', '#b07a20'), 'gem', 5, 0)]
    return lambda n: diagonal(n, parts)


# ------------------------------------------------------------------ bows
def bow(wood=WOOD, string=(240, 240, 235, 255), tips=None, glow=None, depth=0.33, cross=False):
    def draw(n):
        ic = Icon(n); k = n / 32
        cx = n * 0.3
        top, bot = 2.5 * k, n - 2.5 * k
        for py in range(n):
            for px in range(n):
                y = py + 0.5
                t = (y - (top + bot) / 2) / ((bot - top) / 2)
                if abs(t) > 1: continue
                xc = cx + depth * n * (1 - t * t) ** 0.9
                w = (1.3 + 0.9 * (1 - abs(t))) * k
                d = px + 0.5 - xc
                if abs(d) <= w:
                    col = shade(wood, d / w)
                    if abs(t) < 0.12: col = shade(LEATHER, d / w)
                    if tips and abs(t) > 0.85: col = shade(tips, d / w)
                    ic.put(px, py, col, 2)
        # string
        for py in range(int(top), int(bot) + 1):
            ic.put(int(cx), py, string, 1)
        # arrow
        ay = n // 2
        for px in range(int(cx) - int(2 * k), int(n - 2 * k)):
            ic.put(px, ay, (200, 205, 215, 255) if px < n - 5 * k else (255, 255, 255, 255), 3)
        for i in range(int(3 * k)):
            ic.put(int(n - 3 * k) - i, ay - 1 - i // 2, (230, 235, 240, 255), 3); ic.put(int(n - 3 * k) - i, ay + 1 + i // 2, (150, 158, 175, 255), 3)
        for i in range(int(3 * k)):
            ic.put(int(cx) - int(2 * k) + i, ay - 1, (190, 50, 60, 255), 3); ic.put(int(cx) - int(2 * k) + i, ay + 1, (150, 30, 40, 255), 3)
        if glow:
            for i in range(int(4 * k)):
                ic.put(int(n * 0.62) + i, ay - 2 - (i % 2), glow, 4); ic.put(int(n * 0.62) + i, ay + 2 + (i % 2), glow, 4)
        return ic
    return draw


def crossbow():
    def draw(n):
        ic = Icon(n); k = n / 32
        for py in range(n):
            for px in range(n):
                x, y = (px + 0.5) / k, (py + 0.5) / k
                if 3 <= x <= 27 and 14.5 <= y <= 18.5:                                     # stock
                    ic.put(px, py, shade(WOOD, (y - 16.5) / 2), 2)
                if 3 <= x <= 9 and 17 <= y <= 22:                                          # butt
                    ic.put(px, py, shade(DWOOD, (y - 19.5) / 2.5), 2)
                t = (y - 16) / 12
                if abs(t) <= 1:
                    xc = 21 + 3.5 * (1 - t * t)
                    if abs(x - xc) <= 1.4: ic.put(px, py, shade(DSTEEL, (x - xc) / 1.4), 3)
                if abs(t) <= 1 and abs(x - (14 + 7 * abs(t))) <= 0.5: ic.put(px, py, (235, 235, 230, 255), 1)
                if 12 <= x <= 29.5 and 15 <= y <= 16: ic.put(px, py, (220, 226, 236, 255) if x < 28 else (255, 255, 255, 255), 4)
        return ic
    return draw


# ------------------------------------------------------------------ armour
def armor(body, trim, cape=None, pauldron=None, emblem=None, chain=False, robe=False):
    def draw(n):
        ic = Icon(n); k = n / 32
        for py in range(n):
            for px in range(n):
                x, y = (px + 0.5) / k, (py + 0.5) / k
                if cape and 6 <= x <= 26 and 6 <= y <= 30 - abs(x - 16) * 0.2:
                    ic.put(px, py, shade(cape, (x - 16) / 10 + 0.3), 0)
                half = 8.5 if y < 17 else 7.0 if not robe else 7.0 + (y - 17) * 0.35
                bottom = 26 if not robe else 29
                if 6 <= y <= bottom and abs(x - 16) <= half - (2.5 if y < 8 and abs(x - 16) < 3.5 else 0):
                    neck = y < 9 and abs(x - 16) < 3.2
                    if neck: continue
                    tt = (x - 16) / half * 0.7 + (y - 16) / 20
                    col = shade(body, tt)
                    if chain and (int(x) + int(y)) % 2 == 0 and y > 9: col = body[2]
                    if abs(x - 16) < 0.6 and 9 < y < 18 and not robe: col = body[3]                # centre seam
                    if 17 <= y <= 19: col = shade(trim, tt)                                          # belt
                    if 17 <= y <= 19 and abs(x - 16) < 1.5: col = GOLD[1]
                    ic.put(px, py, col, 1)
                if pauldron:
                    for sx in (8.5, 23.5):
                        if (x - sx) ** 2 / 16 + (y - 8.5) ** 2 / 9 <= 1:
                            ic.put(px, py, shade(pauldron, (x - sx) / 4 + (y - 8.5) / 6), 2)
                if emblem and ((abs(x - 16) < 0.8 and 10 <= y <= 15.5) or (abs(y - 12) < 0.8 and abs(x - 16) < 2.6)):
                    ic.put(px, py, emblem[0], 3)
        return ic
    return draw


DRAGON = ramp('#ff8a7a', '#c8343c', '#8a1a2a', '#4a0e18')
SHADOW = ramp('#7a6aa0', '#4a3f6a', '#2d2742', '#1a1428')
PURPLE = ramp('#d07ae0', '#a63bbd', '#6a1f80', '#3e0f4a')
FOREST = ramp('#7cc06a', '#3e7a33', '#2b5a25', '#173a16')
BROWN = ramp('#c89a6a', '#97703f', '#6a4a26', '#3d2814')
CLOTH = ramp('#e2b48a', '#b8865a', '#8a5e3c', '#5a3a24')
BLUE = ramp('#7ab0ff', '#2a64b8', '#17458c', '#0e2a5a')

def staff(gem, shaft=WOOD, ring=GOLD):
    """magic staff: long shaft, gold collar and a glowing crystal on top (combat animations 2026-11-21)"""
    parts = [(0.0, 0.8, const(1.1), shaft, 'metal', 1, 0), (0.0, 0.05, const(1.4), DSTEEL, 'metal', 2, 0),
             (0.74, 0.8, const(2.4), ring, 'metal', 3, 0), (0.8, 1.0, leaf(3.0), gem, 'gem', 4, 0)]
    return lambda n: diagonal(n, parts)


ICONS = [
    sword(STEEL, DSTEEL, LEATHER, blen=0.5, gw=5),                       # sword_short
    sword(STEEL, GOLD, LEATHER),                                          # sword_long
    sword(STEEL, GOLD, BLUEGRIP, gem=BLUE, gw=7.5),                       # sword_knight
    sword(STEEL, DSTEEL, BLACK, bw=3.8, blen=0.7, gw=8.5),                # greatsword
    sword(STEEL, BLACK, REDGRIP, bw=1.6, blen=0.7, gw=3.2, curve=0.35, pommel=BLACK),   # katana
    sword(MOON, DSTEEL, BLUEGRIP, bw=1.7, blen=0.7, gw=3.4, curve=0.35, pommel=MOON),    # katana_moon
    rapier(),                                                             # rapier
    dagger(),                                                             # dagger
    dagger(VENOM, gem=VENOM),                                             # dagger_venom
    polearm('spear'),                                                     # spear
    polearm('halberd'),                                                   # halberd
    polearm('trident', FROST, DWOOD, MOON),                               # trident
    axe(),                                                                # axe
    axe(FROST, True, DWOOD),                                              # axe_frost
    hammer(),                                                             # hammer
    hammer(GOLD, True),                                                   # mace_holy
    sword(FIRE, BLACK, BLACK, gem=FIRE, bw=2.9, gw=7),                    # blade_ash
    sword(RUNE, GOLD, PURPLE, gem=RUNE, bw=2.2, blen=0.7, gw=5, curve=0.2),   # sword_rune
    bow(WOOD, depth=0.28),                                                # bow_short
    bow(WOOD, tips=GOLD, depth=0.36),                                     # bow_long
    crossbow(),                                                           # crossbow
    bow(FOREST, (255, 246, 190, 255), GOLD, (180, 255, 140, 255)),        # bow_elf
    bow(BONE, (220, 225, 235, 255), DRAGON, depth=0.34),                  # bow_bone
    bow(DRAGON, (255, 210, 90, 255), GOLD, (255, 170, 60, 255), 0.36),    # bow_dragon
    armor(CLOTH, LEATHER, robe=True),                                     # armor_cloth
    armor(BROWN, LEATHER, pauldron=LEATHER),                              # armor_leather
    armor(STEEL, LEATHER, chain=True, pauldron=DSTEEL),                   # armor_chain
    armor(STEEL, GOLD, pauldron=STEEL),                                   # armor_plate
    armor(GOLD, BLUE, pauldron=GOLD, emblem=[(255, 255, 255, 255)], cape=BLUE),   # armor_paladin
    armor(SHADOW, PURPLE, pauldron=BLACK, cape=PURPLE),                   # armor_shadow
    armor(BROWN, FOREST, cape=FOREST),                                    # armor_ranger
    armor(DRAGON, GOLD, pauldron=GOLD, emblem=[GOLD[0]], cape=BLACK),     # armor_dragon
    armor(FROST, MOON, pauldron=FROST),                                   # armor_frost
    axe(DSTEEL, True, DWOOD),                                             # 33 heavyaxe
    staff(MOON),                                                          # 34 staff_oak
    staff(FROST, DWOOD, MOON),                                            # 35 staff_frost
]


def build():
    for size in (16, 32):
        imgs = [f(size).finish() for f in ICONS]
        cols = 8; rows = (len(imgs) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * size, rows * size), (0, 0, 0, 0))
        for i, im in enumerate(imgs): sheet.alpha_composite(im, ((i % cols) * size, (i // cols) * size))
        sheet.save(os.path.join(ROOT, 'Assets', 'Art', 'UI', 'Icons', f'ui_items_{size}x{size}.png'))
    big = Image.open(os.path.join(ROOT, 'Assets', 'Art', 'UI', 'Icons', 'ui_items_32x32.png'))
    small = Image.open(os.path.join(ROOT, 'Assets', 'Art', 'UI', 'Icons', 'ui_items_16x16.png'))
    pv = Image.new('RGBA', (big.width + 16, big.height + small.height + 24), (28, 24, 38, 255))
    pv.alpha_composite(big, (8, 8)); pv.alpha_composite(small, (8, big.height + 16))
    pv.resize((pv.width * 3, pv.height * 3), Image.NEAREST).save(os.path.join(ROOT, 'Documentation', 'Previews', 'weapons_preview.png'))
    print(len(ICONS), 'icons')


if __name__ == '__main__':
    build()
