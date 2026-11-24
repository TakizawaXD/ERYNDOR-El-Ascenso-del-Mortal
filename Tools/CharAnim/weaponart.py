"""Weapon layer for the combat animations: hand-drawn weapon sprites + pixel-art safe posing.

Every weapon is drawn ONCE, pointing up, at the original 1:1 scale of the Tiny RPG characters (the Soldier's sword is
13 px long). `pose()` turns it around its grip to any angle with a 4x4 super-sampled splat (thin blades stay one pixel
wide and connected), then adds the black outline the original sprites use. Only the weapon is turned - the body keeps
its own drawn poses (see weaponsets.py / enemyweapons.py).

Angles: degrees, 0 = pointing up, 90 = pointing right (screen), 180 = down, 270 = left.

Colours: steel and hilt are the Soldier's own sword colours (Soldier_Attack01); wood, gold, gem and rune colours are new
but none of them belongs to a recolourable group of variants.py, so the class recolours never tint the weapons.
"""
import math
import numpy as np
from engine import CELL, blank, over, hx, bbox

W = {k: hx(v) for k, v in dict(
    S='#e8f1f4', T='#c9d5d9', U='#a9c1c9', V='#8fa1ae',        # steel, light -> dark (Soldier's sword)
    W='#805121', w='#5a3412', y='#a8743a',                     # hilt / wood
    G='#f6cf5a', g='#c08a30',                                  # gold
    I='#6c7684', i='#4a525c',                                  # dark iron (hammer / heavy axe heads)
    B='#e9ddc6', b='#b8a88a',                                  # bone / bowstring
    R='#9fe8ff', r='#46b4f0', q='#2a6fc0',                     # legendary rune blue
    O='#f04848', o='#a02838',                                  # gem (staff)
    M='#c8f4ff', m='#64c8f8',                                  # magic crystal
    K='#000000',
).items()}
OUTLINE = hx('#000000')

# rows: drawn pointing UP; grip = (x, y) of the hand pixel inside the drawing
WEAPONS = {
    'sword': dict(grip=(1, 11), rows=[
        ".S.",
        "SST",
        "SST",
        "STU",
        "STU",
        "STU",
        "STU",
        "SUV",
        "SUV",
        "WWW",
        ".W.",
        ".w.",
    ]),
    'greatsword': dict(grip=(2, 16), rows=[
        "..S..",
        ".SST.",
        ".SST.",
        ".STU.",
        ".STU.",
        ".STU.",
        ".STU.",
        ".STU.",
        ".STU.",
        ".SUV.",
        ".SUV.",
        ".SUV.",
        "WWWWW",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..g..",
    ]),
    'katana': dict(grip=(1, 13), rows=[
        "..S",
        ".ST",
        ".ST",
        ".ST",
        "ST.",
        "ST.",
        "ST.",
        "ST.",
        "SU.",
        "SU.",
        "GG.",
        "w..",
        "W..",
        "w..",
        "W..",
    ]),
    'rapier': dict(grip=(1, 13), rows=[
        ".S.",
        ".S.",
        ".S.",
        ".T.",
        ".S.",
        ".T.",
        ".S.",
        ".T.",
        ".U.",
        ".U.",
        "GgG",
        "G.G",
        "GWG",
        ".W.",
        ".g.",
    ]),
    'dagger': dict(grip=(1, 6), rows=[
        ".S.",
        "ST.",
        "STU",
        "STU",
        "WWW",
        ".W.",
        ".w.",
    ]),
    'spear': dict(grip=(1, 15), rows=[
        ".S.",
        "SST",
        "STU",
        "STU",
        ".V.",
        "WgW",
        ".W.",
        ".w.",
        ".W.",
        ".w.",
        ".W.",
        ".w.",
        ".W.",
        ".w.",
        ".W.",
        ".w.",
        ".W.",
        ".w.",
        ".W.",
        ".w.",
        ".g.",
    ]),
    'axe': dict(grip=(2, 10), rows=[
        "..W..",
        "..WSS",
        "..WTSS",
        "..WTTU",
        "..WTUU",
        "..WVV",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
    ]),
    'heavyaxe': dict(grip=(3, 14), rows=[
        "...I...",
        "SS.W.SS",
        "STTWTTS",
        "STUWUTS",
        "STUWUTS",
        "STTWTTS",
        "SV.W.VS",
        "...w...",
        "...W...",
        "...w...",
        "...W...",
        "...w...",
        "...W...",
        "...w...",
        "...W...",
        "...w...",
        "...g...",
    ]),
    'hammer': dict(grip=(2, 13), rows=[
        "IIIII",
        "IUTUI",
        "IVUVI",
        "IIIII",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..g..",
    ]),
    'staff': dict(grip=(2, 13), rows=[
        ".gMg.",
        "gMmMg",
        ".gmg.",
        "..W..",
        "..y..",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..W..",
        "..w..",
        "..g..",
    ]),
    'legendary': dict(grip=(2, 15), rows=[
        "..R..",
        ".RRr.",
        ".RSr.",
        ".RSr.",
        ".RSr.",
        ".rSq.",
        ".RSr.",
        ".RSr.",
        ".rSq.",
        ".RSr.",
        ".RSq.",
        "GGGGG",
        "gGOGg",
        "..w..",
        "..W..",
        "..w..",
        "..G..",
    ]),
    # bows are drawn as seen while aiming to the right: string on the left, arc bulging right; grip = hand on the riser
    'bow': dict(grip=(2, 6), rows=[
        "Wy.",
        "bWy",
        "b.W",
        "b.W",
        "b.W",
        "b.W",
        "b.g",
        "b.W",
        "b.W",
        "b.W",
        "b.W",
        "bWy",
        "Wy.",
    ]),
    'longbow': dict(grip=(2, 8), rows=[
        "By.",
        "bBy",
        "b.B",
        "b.W",
        "b.W",
        "b.W",
        "b.W",
        "b.W",
        "b.g",
        "b.W",
        "b.W",
        "b.W",
        "b.W",
        "b.W",
        "b.B",
        "bBy",
        "By.",
    ]),
    'crossbow': dict(grip=(1, 3), rows=[
        "......y",
        ".....yW",
        "WWWWWVW",
        "wwWWwgW",
        ".W...yW",
        ".w....y",
    ]),
    'arrow': dict(grip=(0, 0), rows=[
        "yWWWWWWVS",
    ]),
    'bolt': dict(grip=(0, 0), rows=["WWWWVS"]),
    'shield': dict(grip=(2, 4), rows=[
        ".IIII.",
        "IUTTUI",
        "IVGgVI",
        "IVggVI",
        "IVUUVI",
        ".IVVI.",
        "..II..",
    ]),
}
# bows / arrows / crossbow are authored horizontally: their "up" is to the right
AUTHORED_RIGHT = {'arrow', 'bolt', 'crossbow'}

# how long each blade is from grip to tip (px) - used for trails and the hitbox data exported to Unity
def reach_px(name):
    d = WEAPONS[name]
    gx, gy = d['grip']
    pts = [(x, y) for y, r in enumerate(d['rows']) for x, c in enumerate(r) if c != '.']
    return max(math.hypot(x - gx, y - gy) for x, y in pts)


def sprite(name, pal=None):
    d = WEAPONS[name]
    p = dict(W); p.update(pal or {})
    h, w = len(d['rows']), max(len(r) for r in d['rows'])
    a = np.zeros((h, w, 4), np.uint8)
    for y, r in enumerate(d['rows']):
        for x, ch in enumerate(r):
            if ch != '.':
                a[y, x] = p[ch]
    return a, d['grip']


def _outline(layer):
    m = layer[:, :, 3] > 0
    o = np.zeros_like(m)
    o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    o &= ~m
    layer[o] = OUTLINE
    return layer


def pose(name, angle, gx, gy, pal=None, outline=True, flipx=False, scale=1.0):
    """64x64 layer with weapon `name` turned to `angle` and its grip on pixel (gx, gy).
    flipx mirrors the drawing first (e.g. the curve of a katana held the other way)."""
    spr, (sx, sy) = sprite(name, pal)
    if flipx:
        spr = spr[:, ::-1].copy(); sx = spr.shape[1] - 1 - sx
    if name in AUTHORED_RIGHT:
        angle = angle - 90
    th = math.radians(angle)
    c, s = math.cos(th), math.sin(th)
    votes = {}
    N = 4
    h, w = spr.shape[:2]
    for y in range(h):
        for x in range(w):
            if spr[y, x, 3] == 0:
                continue
            col = tuple(int(v) for v in spr[y, x])
            for j in range(N):
                for i in range(N):
                    dx = (x + (i + .5) / N - (sx + .5)) * scale
                    dy = (y + (j + .5) / N - (sy + .5)) * scale
                    rx = dx * c - dy * s
                    ry = dx * s + dy * c
                    tx = int(math.floor(gx + .5 + rx)); ty = int(math.floor(gy + .5 + ry))
                    d = votes.setdefault((tx, ty), {})
                    d[col] = d.get(col, 0) + 1
    out = blank()
    for (tx, ty), d in votes.items():
        if not (0 <= tx < CELL and 0 <= ty < CELL):
            continue
        total = sum(d.values())
        if total < N * N * 0.28:
            continue
        out[ty, tx] = max(d.items(), key=lambda kv: kv[1])[0]
    if outline:
        _outline(out)
    return out


def tip(name, angle, gx, gy, frac=1.0):
    r = reach_px(name) * frac
    th = math.radians(angle)
    return gx + math.sin(th) * r, gy - math.cos(th) * r


def hand(frame, x, y, cols, big=False):
    """the fist closed around the grip, drawn over the weapon (2x2, or 3x2 for gauntlets)"""
    out = frame.copy()
    hi, lo = cols
    pts = [(x, y, hi), (x + 1, y, hi), (x, y + 1, lo), (x + 1, y + 1, lo)]
    if big:
        pts += [(x - 1, y, hi), (x - 1, y + 1, lo)]
    for px_, py_, c in pts:
        if 0 <= px_ < CELL and 0 <= py_ < CELL:
            out[py_, px_] = c
    # outline the fist where it sticks out into empty space
    for px_, py_, _ in pts:
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Y = px_ + ox, py_ + oy
            if 0 <= X < CELL and 0 <= Y < CELL and out[Y, X, 3] == 0:
                out[Y, X] = OUTLINE
    return out


SLASH = hx('#f4edea'); SLASH2 = hx('#d9d8d8'); SLASH3 = hx('#c0bfbf')
GLOW_TRAIL = (hx('#c8f4ff'), hx('#64c8f8'), hx('#2a6fc0'))
GOLD_TRAIL = (hx('#fff3b0'), hx('#f6cf5a'), hx('#c08a30'))
FIRE_TRAIL = (hx('#fff0a0'), hx('#f9a31b'), hx('#e43b44'))
WHITE_TRAIL = (SLASH, SLASH2, SLASH3)


def trail(frame, gx, gy, r_in, r_out, a0, a1, cols=WHITE_TRAIL, fade=False, ry=1.0, behind=False):
    """crescent smear swept by the blade between angles a0 -> a1 (our angle convention), thickest in the middle,
    sharpest at the leading edge (a1) like the originals. ry < 1 flattens it (seen from above)."""
    out = frame.copy()
    lo, hi = (a0, a1) if a0 <= a1 else (a1, a0)
    span = max(hi - lo, 1e-3)
    for y in range(CELL):
        for x in range(CELL):
            dx, dy = x + .5 - (gx + .5), (y + .5 - (gy + .5)) / ry
            r = math.hypot(dx, dy)
            if r < r_in - .5 or r > r_out + .5:
                continue
            a = math.degrees(math.atan2(dx, -dy))
            # bring a into [lo, lo+360)
            while a < lo: a += 360
            while a >= lo + 360: a -= 360
            if a > hi:
                continue
            t = (a - lo) / span
            if a0 > a1: t = 1 - t                      # t = 0 at the start of the swing, 1 at the blade
            thick = (r_out - r_in) * (0.25 + 0.75 * math.sin(math.pi * min(1, t * 0.9 + 0.1))) * (0.5 if fade else 1)
            if r < r_out - thick:
                continue
            edge = r > r_out - 1 or r < r_out - thick + 1 or t < 0.25
            col = cols[2] if fade else (cols[1] if edge else cols[0])
            if behind and out[y, x, 3] > 0:
                continue
            out[y, x] = col
    return out


def thrust_lines(frame, x0, x1, y, cols=WHITE_TRAIL, rows=(-1, 0, 1)):
    """speed lines behind a stab (horizontal); rows are offsets around y"""
    out = frame.copy()
    for k, oy in enumerate(rows):
        L = abs(x1 - x0) - (2 if oy else 0)
        step = 1 if x1 >= x0 else -1
        for i in range(max(0, L)):
            X = x0 + (i + (1 if oy else 0)) * step
            Y = y + oy
            if 0 <= X < CELL and 0 <= Y < CELL and out[Y, X, 3] == 0:
                out[Y, X] = cols[0] if oy == 0 else cols[1]
    return out


def vthrust_lines(frame, x, y0, y1, cols=WHITE_TRAIL, cols_off=(-1, 0, 1)):
    out = frame.copy()
    for ox in cols_off:
        step = 1 if y1 >= y0 else -1
        L = abs(y1 - y0) - (2 if ox else 0)
        for i in range(max(0, L)):
            Y = y0 + (i + (1 if ox else 0)) * step
            X = x + ox
            if 0 <= X < CELL and 0 <= Y < CELL and out[Y, X, 3] == 0:
                out[Y, X] = cols[0] if ox == 0 else cols[1]
    return out


def compose(body, weapon_layer, behind):
    return over(weapon_layer, body) if behind else over(body, weapon_layer)


def preview(path, names=None, angles=(0, 45, 90, 135, 180, 225, 270, 315), k=6):
    """contact sheet of every weapon at 8 angles (for the docs)"""
    from PIL import Image
    names = names or [n for n in WEAPONS if n not in ('arrow', 'bolt')]
    cell = 40
    sheet = np.zeros((cell * len(names), cell * len(angles), 4), np.uint8)
    sheet[:] = (70, 90, 70, 255)
    for r, n in enumerate(names):
        for c, a in enumerate(angles):
            lay = pose(n, a, 32, 32)
            crop = lay[12:52, 12:52]
            m = crop[:, :, 3] > 0
            sheet[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell][m] = crop[m]
    Image.fromarray(sheet, 'RGBA').resize((sheet.shape[1] * k, sheet.shape[0] * k), Image.NEAREST).save(path)


if __name__ == '__main__':
    import os, sys
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..', 'Documentation', 'CombatAnimations', 'weapons_angles.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    preview(out)
    print('wrote', out)
