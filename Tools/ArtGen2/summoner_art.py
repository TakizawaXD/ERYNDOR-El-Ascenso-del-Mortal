"""El Invocador - a hand-built, fully animated boss sheet (not a recolour), plus his ritual circle.

  python summoner_art.py -> Assets/Art/Characters/Invocador/<Clip>/Invocador_<Clip>_<Dir>.png + Invocador_animations.json
                            (same clips / frame counts / 64x64 cells as the Soldier rig, so the animator builder makes his controller)
                            Assets/Art/World/Effects/rune_circle_anim_96x56.png   8-frame ritual circle
                            Documentation/Previews/summoner_preview.png

Design (after the user's reference, in our style): a tall hovering sorcerer in a layered violet-black robe with tattered hem,
spiked iron halo with pulsing gems behind the hood, two glowing eyes in an empty hood, shoulder mantle with spiked
pauldrons, gold-trimmed rune strip, belt with swinging chains, a skeletal hand holding a chain and the other one
holding a violet soul-flame. Every animation is drawn per frame: floating bob, hem sway, flickering flame, casting
bursts, recoil, teleport smoke and a death that dissolves into motes.
"""
import json, math, os, random
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CH = os.path.join(ROOT, 'Assets', 'Art', 'Characters')
S = 64            # cell
GROUND = 52       # feet row (pivot 12/64 from the bottom)


def hx(s, a=255):
    s = s.lstrip('#'); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


P = {k: hx(v) for k, v in dict(
    ol='#07040c',
    r0='#0c0814', r1='#150d22', r2='#1f1432', r3='#2c1d46', r4='#3d2a60', r5='#54397f',      # robe ramp dark -> light
    m0='#120a1e', m1='#211438', m2='#33215a', m3='#4a3280',                                    # mantle
    tr0='#5a1aa0', tr1='#7a2ad0', tr2='#a052f0', tr3='#d29cff',                                # violet trim / magic
    g0='#6e4a1a', g1='#a8782a', g2='#e0b048', g3='#fff0a0',                                    # gold
    i0='#2a2a36', i1='#46465a', i2='#6c6c84', i3='#a4a4bc', i4='#dcdcec',                      # iron (halo, chains)
    bone0='#6e6a62', bone1='#a8a294', bone2='#dcd6c6',
    eye='#b8f4ff', eye2='#6ad0ff',
    f0='#3a0a6a', f1='#7a1ac0', f2='#c040ff', f3='#ff7cf0', f4='#ffe0ff',                      # soul flame
    gem='#ff4ad8', gem2='#ffb0f0',
).items()}
GLOW = lambda c, a: (c[0], c[1], c[2], a)


class Cv:
    def __init__(self, w=S, h=S):
        self.a = np.zeros((h, w, 4), np.uint8); self.w, self.h = w, h

    def px(self, x, y, c, over=True):
        x, y = int(round(x)), int(round(y))
        if not (0 <= x < self.w and 0 <= y < self.h): return
        c = P[c] if isinstance(c, str) else c
        if len(c) == 4 and c[3] < 255:
            if self.a[y, x, 3] == 0:
                self.a[y, x] = c
            else:
                k = c[3] / 255
                self.a[y, x, :3] = (np.array(c[:3]) * k + self.a[y, x, :3] * (1 - k)).astype(np.uint8)
            return
        if over or self.a[y, x, 3] == 0: self.a[y, x] = c

    def get(self, x, y):
        return self.a[y, x] if 0 <= x < self.w and 0 <= y < self.h else np.zeros(4, np.uint8)

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            t = i / n; self.px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + .5 - cx) / max(rx, .1)) ** 2 + ((y + .5 - cy) / max(ry, .1)) ** 2 <= 1: self.px(x, y, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if (y0 <= y + .5 < y1) or (y1 <= y + .5 < y0):
                    xs.append(x0 + (y + .5 - y0) / (y1 - y0) * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(round(xs[k])), int(round(xs[k + 1]))): self.px(x, y, c)

    def outline(self, c='ol'):
        m = self.a[:, :, 3] >= 200
        o = np.zeros_like(m)
        o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        o &= self.a[:, :, 3] == 0
        self.a[o] = P[c]

    def img(self): return Image.fromarray(self.a, 'RGBA')


def ramp(v, names):
    v = max(0.0, min(0.999, v)); return names[int(v * len(names))]


# ============================================================== body parts
def halo(c, cx, cy, t, front=False):
    """spiked iron crown-halo: an outer ring, eleven spikes of two lengths, three pulsing gems"""
    for k in range(11):
        a = math.pi + (k + 0.5) / 11 * math.pi
        L = 9.5 if k % 2 == 0 else 6.5
        r0 = 7.5
        for s in range(int(L * 2)):
            r = r0 + s / 2
            w = 1.6 * (1 - s / (L * 2))
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.92
            nx, ny = -math.sin(a), math.cos(a)
            for d in (-w, 0, w):
                c.px(x + nx * d, y + ny * d, 'i3' if d < 0 else 'i1' if d > 0 else 'i2')
        c.px(cx + math.cos(a) * (r0 + L), cy + math.sin(a) * (r0 + L) * 0.92, 'i4')
    for k in range(48):                                           # the ring with rivets
        a = math.pi + k / 47 * math.pi
        x, y = cx + math.cos(a) * 7.5, cy + math.sin(a) * 6.9
        c.px(x, y, 'i2' if k % 6 else 'i4'); c.px(cx + math.cos(a) * 6.5, cy + math.sin(a) * 6.0, 'i0')
    pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
    for k in (2, 5, 8):
        a = math.pi + (k + 0.5) / 11 * math.pi
        x, y = cx + math.cos(a) * 12, cy + math.sin(a) * 11
        c.px(x, y, 'gem2' if pulse > 0.5 else 'gem'); c.px(x + 1, y, 'gem'); c.px(x, y + 1, 'gem')
        c.px(x - 1, y - 1, GLOW(P['gem'], int(60 + 80 * pulse)))


def robe(c, cx, top, bottom, half_top, half_bot, t, sway, lean=0.0, back=False):
    """long robe with shading by column, fold lines, a gold-trimmed rune strip and a tattered, swaying hem"""
    for y in range(int(top), int(bottom) + 1):
        k = (y - top) / max(1, bottom - top)
        half = half_top + (half_bot - half_top) * k ** 0.9
        off = lean * k * 3 + sway * k * k * 1.5
        for x in range(int(cx - half + off), int(cx + half + off) + 1):
            u = (x - (cx - half + off)) / max(1, 2 * half)                 # 0 left .. 1 right
            shade = 0.85 - u * 0.75 + 0.12 * math.sin(u * 9 + k * 2)        # light from the upper left, soft folds
            c.px(x, y, ramp(shade - k * 0.15, ['r0', 'r1', 'r2', 'r3', 'r4']))
    # fold lines
    for fx in (-0.55, -0.15, 0.3, 0.65):
        for y in range(int(top + 6), int(bottom - 1)):
            k = (y - top) / max(1, bottom - top)
            half = half_top + (half_bot - half_top) * k ** 0.9
            x = cx + fx * half + lean * k * 3 + sway * k * k * 1.5 + math.sin(y * 0.4 + fx * 5) * 0.6
            c.px(x, y, 'r0'); c.px(x - 1, y, 'r3' if fx < 0 else 'r2')
    if not back:                                                    # rune strip down the front
        for y in range(int(top + 2), int(bottom - 2)):
            k = (y - top) / max(1, bottom - top)
            x = cx + lean * k * 3 + sway * k * k * 1.5
            c.px(x - 1, y, 'g1'); c.px(x + 1, y, 'g0'); c.px(x, y, 'tr0')
            if (y + int(t * 8)) % 5 == 0: c.px(x, y, 'tr3')            # glowing runes crawl down
    # tattered hem: ragged teeth that sway
    for x in range(int(cx - half_bot - 2), int(cx + half_bot + 3)):
        n = (math.sin(x * 1.7) + math.sin(x * 0.63 + t * 6.28)) * 1.4
        d = int(2 + n + (x * 7 % 3))
        for j in range(max(0, d)):
            xx = x + sway * 1.5 + lean * 3
            if j == d - 1: c.px(xx, bottom + j, 'r0')
            else: c.px(xx, bottom + j, 'r1')
    # wisps of smoke under the hem (he floats)
    for i in range(5):
        a = t * 6.28 + i * 1.3
        x = cx + math.sin(a) * (half_bot - 1) + lean * 3
        y = bottom + 3 + (i % 3) + math.cos(a) * 1.2
        c.px(x, y, GLOW(P['tr1'], 140)); c.px(x + 1, y + 1, GLOW(P['tr0'], 90))


def mantle(c, cx, y, half, lean=0.0, back=False):
    """shoulder mantle with a lit edge and spiked pauldrons"""
    pts = [(cx - half, y + 6), (cx - half + 2, y + 1), (cx - 3, y - 1), (cx + 3, y - 1), (cx + half - 2, y + 1), (cx + half, y + 6),
           (cx + half - 3, y + 9), (cx, y + 7), (cx - half + 3, y + 9)]
    pts = [(px + lean, py) for px, py in pts]
    c.poly(pts, 'm1')
    for x in range(int(cx - half + 2 + lean), int(cx + half - 1 + lean)):
        c.px(x, y + 1 if abs(x - cx - lean) > 3 else y, 'm3' if x < cx + lean else 'm2')
    for side in (-1, 1):                                            # pauldrons with three spikes each
        px0 = cx + side * (half - 2) + lean
        c.ellipse(px0, y + 3, 3.2, 2.6, 'i1'); c.ellipse(px0 - 0.6 * side, y + 2.4, 2, 1.4, 'i2')
        for k in range(3):
            sx = px0 + side * (k - 1) * 1.6
            c.line(sx, y + 1, sx + side * 1.2, y - 3 - (1 - abs(k - 1)) * 2, 'i3')
    if not back:
        c.ellipse(cx + lean, y + 4, 1.8, 1.5, 'g2'); c.px(cx + lean, y + 4, 'gem'); c.px(cx - 1 + lean, y + 3, 'g3')   # clasp


def hood(c, cx, cy, side=0, back=False, eyes_on=1.0, t=0.0):
    """deep hood; side = -1/0/1 (facing left/front/right). The face is a void with two burning eyes."""
    pts = [(cx, cy - 8), (cx + 5, cy - 5), (cx + 7, cy + 1), (cx + 6, cy + 6), (cx - 6, cy + 6), (cx - 7, cy + 1), (cx - 5, cy - 5)]
    if side: pts = [(cx + side * 2, cy - 8), (cx + side * 7, cy - 3), (cx + side * 7, cy + 4), (cx + side * 3, cy + 7), (cx - side * 6, cy + 6), (cx - side * 7, cy - 1), (cx - side * 3, cy - 6)]
    c.poly(pts, 'm1')
    for (x, y) in pts:                                               # rim light
        c.px(x, y, 'm3')
    c.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], 'm3'); c.line(pts[0][0], pts[0][1], pts[-1][0], pts[-1][1], 'm2')
    if back:
        c.line(cx, cy - 7, cx, cy + 5, 'm0')                          # seam at the back
        c.line(cx - 1, cy - 6, cx - 1, cy + 4, 'm2')
        return
    fx = cx + side * 2.5
    c.ellipse(fx, cy + 1.5, 3.8 if not side else 2.6, 4.2, 'ol')       # the void
    c.ellipse(fx, cy + 2.5, 2.6 if not side else 1.8, 3.0, (14, 6, 24, 255))
    if eyes_on > 0:
        a = int(255 * eyes_on)
        eyes = [(fx - 1.6, cy + 1), (fx + 1.6, cy + 1)] if not side else [(fx + side * 0.8, cy + 1)]
        for (ex, ey) in eyes:
            c.px(ex, ey, GLOW(P['eye'], a)); c.px(ex + (1 if not side else side), ey, GLOW(P['eye2'], a))
            for (gx, gy) in ((ex - 1, ey), (ex, ey - 1), (ex, ey + 1), (ex + 2, ey)):
                c.px(gx, gy, GLOW(P['eye2'], int(70 * eyes_on)))
    # hood edge trim
    c.line(pts[-2][0], pts[-2][1], pts[-3][0], pts[-3][1], 'tr0')


def sleeve(c, x0, y0, x1, y1, w=2.6):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        t = i / n; x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        r = w * (0.7 + 0.5 * t)
        c.ellipse(x, y, r + 0.9, r * 0.9 + 0.9, 'ol')
    for i in range(n + 1):
        t = i / n; x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        r = w * (0.7 + 0.5 * t)
        c.ellipse(x, y, r, r * 0.9, 'm2' if t < 0.5 else 'm3')
        c.px(x - r * 0.5, y - r * 0.5, 'r5')
    c.ellipse(x1, y1, w * 1.1, w, 'tr1')                              # cuff
    c.px(x1 - 1, y1 - 1, 'tr3')


def hand(c, x, y, open_=True):
    c.ellipse(x, y, 1.6, 1.4, 'bone1'); c.px(x - 1, y - 1, 'bone2')
    if open_:
        for k in (-1, 0, 1): c.line(x + k, y - 1, x + k * 1.6, y - 3.5, 'bone1')
        c.px(x, y - 4, 'bone2')
    else:
        for k in (-1, 0, 1): c.line(x + k, y + 1, x + k * 0.8, y + 3, 'bone0')


def chain(c, x0, y0, x1, y1, t, sag=3.0):
    n = 10
    for i in range(n + 1):
        u = i / n
        x = x0 + (x1 - x0) * u + math.sin(t * 6.28 + u * 3) * 0.7
        y = y0 + (y1 - y0) * u + math.sin(u * math.pi) * sag
        c.px(x, y, 'i3' if i % 2 == 0 else 'i1')
        if i % 2 == 0: c.px(x + 1, y, 'i1')


def flame(c, x, y, size, t):
    """violet soul-flame: layered tongues, hot core, rising motes"""
    for k in range(4):
        r = size * (1 - k * 0.22)
        col = ['f0', 'f1', 'f2', 'f3'][k]
        for i in range(int(r * 2.6) + 2):
            u = i / max(1, r * 2.6)
            w = r * (1 - u) * (0.75 + 0.25 * math.sin(t * 12 + i + k))
            yy = y - u * r * 2.4
            xx = x + math.sin(t * 9 + u * 5 + k) * u * 1.4
            for d in range(-int(w), int(w) + 1): c.px(xx + d, yy, col)
    c.ellipse(x, y - size * 0.3, max(0.8, size * 0.28), max(0.8, size * 0.3), 'f4')
    for i in range(4):                                               # motes
        ph = (t * 1.6 + i * 0.27) % 1
        c.px(x + math.sin(i * 2.1 + t * 5) * (size + 1), y - size * 2.2 - ph * 6, GLOW(P['f3'], int(220 * (1 - ph))))
    for (dx, dy) in ((-size - 1, 0), (size + 1, 0), (0, 1)):        # glow
        c.px(x + dx, y + dy, GLOW(P['f2'], 90))


def burst(c, x, y, r, t):
    for k in range(int(r * 6) + 8):
        a = k / (r * 6 + 8) * 2 * math.pi
        rr = r + math.sin(a * 5 + t * 8) * 0.8
        c.px(x + math.cos(a) * rr, y + math.sin(a) * rr * 0.8, 'f3' if k % 3 else 'f4')
    for k in range(6):
        a = k / 6 * 2 * math.pi + t * 3
        c.line(x + math.cos(a) * (r * 0.4), y + math.sin(a) * r * 0.3, x + math.cos(a) * (r + 2), y + math.sin(a) * (r + 2) * 0.8, GLOW(P['f2'], 200))


# ============================================================== one frame
def figure(direction, t, pose=0.0, cast=0.0, flame_size=3.0, recoil=0.0, dissolve=0.0, smoke=0.0, block=0.0, bob_amp=1.0, lean=0.0):
    """direction: Down/Up/Left/Right; t: 0..1 loop phase; pose: 0 relaxed .. 1 arm raised; cast: both arms up;
    recoil: knocked back; dissolve: death; smoke: teleport; block: barrier"""
    c = Cv()
    bob = round(math.sin(t * 2 * math.pi) * 1.2 * bob_amp)
    cx = 32 - recoil * 2 * (1 if direction != 'Left' else -1)
    sway = math.sin(t * 2 * math.pi + 1) * (1.0 + abs(lean))
    top = 21 + bob; bottom = 46 + bob
    side = 1 if direction == 'Right' else -1 if direction == 'Left' else 0
    back = direction == 'Up'
    hood_y = 14 + bob

    # ground glow (he floats over his own light)
    for k in range(3):
        c.ellipse(32, GROUND - 1, 11 - k * 3, 2.4 - k * 0.6, GLOW(P['tr0'], 45 + k * 25))

    # halo behind the head (in front when seen from the back)
    if not back: halo(c, cx + side * -1, hood_y - 1, t)

    # far arm (behind the body)
    if side:
        sleeve(c, cx - side * 4, top + 3, cx - side * 6, top + 12)
        hand(c, cx - side * 6, top + 14, open_=False)
        chain(c, cx - side * 6, top + 15, cx - side * 9, bottom + 1, t, 2)

    robe(c, cx, top, bottom, 7.5 if not side else 6, 12.5 if not side else 10, t, sway, lean=lean + side * 0.3, back=back)
    # belt and hanging chains
    by = top + 10
    for x in range(int(cx - 8), int(cx + 9)): c.px(x + lean, by, 'g0'); c.px(x + lean, by + 1, 'r0')
    if not back:
        c.ellipse(cx + lean, by, 1.8, 1.4, 'g2'); c.px(cx + lean, by, 'gem')
        chain(c, cx - 6 + lean, by + 1, cx - 3 + lean, by + 12, t, 1.5)
        chain(c, cx + 5 + lean, by + 1, cx + 8 + lean, by + 10, t + 0.3, 1.2)
    mantle(c, cx, top - 2, 10.5 if not side else 8.5, lean=lean, back=back)
    hood(c, cx + lean, hood_y, side, back, eyes_on=1.0 - dissolve, t=t)
    if back: halo(c, cx, hood_y - 1, t, front=True)

    # arms
    if not side:
        # viewer's left hand holds a chain; viewer's right hand holds the soul-flame
        la = cast
        lx, ly = cx - 11 + la * 1, top + 12 - la * 14
        sleeve(c, cx - 7, top + 2, lx, ly)
        hand(c, lx, ly + (0 if la else 1), open_=la > 0.5)
        if la < 0.5: chain(c, lx, ly + 2, lx - 3, bottom + 2, t, 1.5)
        ra = max(pose, cast)
        rx, ry = cx + 11 - ra * 1, top + 10 - ra * 15
        sleeve(c, cx + 7, top + 2, rx, ry + 1)
        hand(c, rx, ry + 1)
        flame(c, rx, ry - 2, flame_size * (1 + ra * 0.6), t)
        if la > 0.5: flame(c, lx, ly - 2, flame_size * 1.2, t + 0.5)
    else:
        ra = max(pose, cast)
        hx_, hy_ = cx + side * (8 + ra * 3), top + 9 - ra * 9
        sleeve(c, cx + side * 3, top + 2, hx_, hy_ + 1)
        hand(c, hx_, hy_ + 1)
        flame(c, hx_ + side, hy_ - 2, flame_size * (1 + ra * 0.6), t)

    if cast > 0.6 or pose > 0.85:                                  # the spell leaves his hand
        bxs = [(cx + 10, top - 6)] if not side else [(cx + side * 13, top - 1)]
        if cast > 0.6 and not side: bxs.append((cx - 10, top - 4))
        for (bx, byy) in bxs: burst(c, bx, byy, 3 + (cast + pose) * 2, t)

    if block > 0:                                                   # violet hex barrier in front
        bx = 32 + side * 10
        for k in range(6):
            a0, a1 = k / 6 * 2 * math.pi, (k + 1) / 6 * 2 * math.pi
            c.line(bx + math.cos(a0) * 10, 31 + math.sin(a0) * 13, bx + math.cos(a1) * 10, 31 + math.sin(a1) * 13, GLOW(P['tr2'], int(200 * block)))
        for k in range(12): c.px(bx + random.uniform(-7, 7), 31 + random.uniform(-10, 10), GLOW(P['tr3'], int(160 * block)))

    c.outline()

    if recoil > 0:                                                  # hit flash
        m = c.a[:, :, 3] > 0
        c.a[m, :3] = (c.a[m, :3] * (1 - recoil * 0.6) + np.array([255, 220, 255]) * recoil * 0.6).astype(np.uint8)
    if smoke > 0:                                                   # teleport: he melts into violet smoke
        rng = random.Random(int(smoke * 100))
        ys, xs = np.nonzero(c.a[:, :, 3])
        for y, x in zip(ys, xs):
            if rng.random() < smoke * 0.9: c.a[y, x] = 0
        for i in range(int(30 * smoke)):
            c.px(32 + rng.gauss(0, 7), 34 + rng.gauss(0, 9), GLOW(P[rng.choice(['tr1', 'tr2', 'f3'])], rng.randint(90, 230)))
    if dissolve > 0:                                                # death: crumbles upward into motes
        rng = random.Random(7)
        ys, xs = np.nonzero(c.a[:, :, 3])
        for y, x in zip(ys, xs):
            if rng.random() < dissolve * (0.55 + (GROUND - y) / 90): c.a[y, x] = 0
        for i in range(int(50 * dissolve)):
            c.px(32 + rng.gauss(0, 9), 40 - rng.random() * 34 * dissolve, GLOW(P[rng.choice(['tr2', 'f3', 'eye2'])], rng.randint(80, 230)))
    return c


# ============================================================== clips
def frames_for(name, d, n):
    out = []
    for i in range(n):
        u = i / max(1, n - 1)       # 0..1 through a one-shot
        lp = i / n                  # loop phase
        if name in ('Idle', 'Sit', 'Swim', 'Climb', 'Fall', 'Land', 'Jump', 'Victory', 'Sleep', 'Push', 'Pull', 'Interact', 'PickUp', 'Defeat'):
            out.append(figure(d, lp, pose=0.15 if name == 'Victory' else 0.0, cast=0.7 * math.sin(u * math.pi) if name == 'Victory' else 0))
        elif name in ('Walk', 'Run'):
            out.append(figure(d, lp, lean=(0.6 if name == 'Run' else 0.35) * (1 if d == 'Right' else -1 if d == 'Left' else 0), bob_amp=0.6))
        elif name in ('Attack', 'ComboAttack', 'HeavyAttack', 'CriticalAttack', 'ChargedAttack_Release'):
            pose = math.sin(min(1, u * 1.3) * math.pi / 2) if u < 0.75 else (1 - u) * 4
            out.append(figure(d, lp, pose=pose, flame_size=3.0 + (0.8 if name == 'HeavyAttack' else 0)))
        elif name in ('SpecialAttack', 'CastSpell', 'ChargeEnergy', 'ChargedAttack_Charge'):
            cast = math.sin(min(1, u * 1.2) * math.pi / 2) if u < 0.8 else (1 - u) * 5
            out.append(figure(d, lp, cast=cast, flame_size=3.2))
        elif name in ('Hurt', 'Knockback'):
            out.append(figure(d, lp, recoil=1 - u, eyes_on=1))
        elif name == 'Death':
            out.append(figure(d, lp, dissolve=min(1, u * 1.1)))
        elif name in ('Roll', 'Dodge'):
            out.append(figure(d, lp, smoke=math.sin(u * math.pi)))
        elif name in ('Block', 'BlockHit'):
            out.append(figure(d, lp, block=1.0 if name == 'Block' else 1 - u * 0.5, cast=0.5))
        else:
            out.append(figure(d, lp))
    return out


# keep the kwarg used above harmless
_fig = figure
def figure(direction, t, eyes_on=None, **kw): return _fig(direction, t, **kw)


def rune_circle(n=8, W=96, H=56):
    """ritual circle: glow pool, double rim with ticks, rotating ring of sigils, counter-rotating dashed ring,
    hexagram, inner eye-rune and rising motes"""
    out = []
    cx, cy = W / 2, H / 2
    sig = [  # 3x5 sigils
        ["x.x", ".x.", "xxx", ".x.", "x.x"], ["xxx", "x..", "xx.", "x..", "xxx"], [".x.", "xxx", ".x.", "x.x", ".x."],
        ["x..", "xx.", "x.x", "xx.", "x.."], ["xxx", "x.x", ".x.", "x.x", "xxx"], [".x.", "x.x", "xxx", "..x", ".x."]]
    for f in range(n):
        t = f / n
        c = Cv(W, H)
        pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
        for k in range(6):                                         # glow pool
            c.ellipse(cx, cy, 44 - k * 6, 24 - k * 3.3, GLOW(P['tr0'], int(18 + k * 8 + pulse * 10)))
        def ring(r, col, dash=None, rot=0.0, step=320):
            for k in range(step):
                a = k / step * 2 * math.pi + rot
                if dash and (k // dash) % 2: continue
                c.px(cx + math.cos(a) * r, cy + math.sin(a) * r * 0.55, col)
        ring(44, 'tr1'); ring(42, 'tr3' if pulse > 0.6 else 'tr2')
        for k in range(48):                                         # ticks
            a = k / 48 * 2 * math.pi
            r0, r1 = (42, 39) if k % 4 else (42, 37)
            c.line(cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.55, cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.55, 'tr1')
        for k in range(12):                                         # rotating sigils
            a = k / 12 * 2 * math.pi + t * 2 * math.pi / 12
            sx, sy = cx + math.cos(a) * 33, cy + math.sin(a) * 33 * 0.55
            g = sig[k % len(sig)]
            col = 'gem2' if (k + f) % 4 == 0 else 'tr3'
            for yy, row in enumerate(g):
                for xx, ch in enumerate(row):
                    if ch == 'x': c.px(sx - 1 + xx, sy - 2 + yy, col)
        ring(27, 'tr2', dash=6, rot=-t * 2 * math.pi / 6)
        ring(25, 'tr1')
        for k in range(2):                                          # hexagram
            pts = [(cx + math.cos(a) * 24, cy + math.sin(a) * 24 * 0.55) for a in
                   [k * math.pi / 3 + j * 2 * math.pi / 3 + t * 0.4 - math.pi / 2 for j in range(3)]]
            for j in range(3):
                c.line(*pts[j], *pts[(j + 1) % 3], 'tr2' if k else 'tr3')
        ring(11, 'tr3'); ring(9, 'tr1')
        c.ellipse(cx, cy, 6, 3, 'f1'); c.ellipse(cx, cy, 2.4, 2.4 * 0.9, 'f4' if pulse > 0.5 else 'f3')        # eye rune
        c.line(cx - 8, cy, cx + 8, cy, 'tr2')
        rng = random.Random(f)
        for i in range(10):                                         # motes rising from the rim
            a = rng.random() * 2 * math.pi
            h = ((t + i / 10) % 1) * 14
            c.px(cx + math.cos(a) * 40, cy + math.sin(a) * 22 - h, GLOW(P['f3'], int(220 * (1 - h / 14))))
        out.append(c)
    return out


def build():
    src = os.path.join(CH, 'Soldier')
    man = json.load(open(os.path.join(src, 'Soldier_animations.json')))
    man['character'] = 'Invocador'
    dst = os.path.join(CH, 'Invocador')
    random.seed(3)
    for clip in man['clips']:
        rel = clip['file'].replace('Soldier_', 'Invocador_', 1)
        fr = frames_for(clip['name'], clip['dir'], clip['frames'])
        sheet = Image.new('RGBA', (S * len(fr), S), (0, 0, 0, 0))
        for i, f in enumerate(fr): sheet.alpha_composite(f.img(), (i * S, 0))
        path = os.path.join(dst, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
        sheet.save(path)
        clip['file'] = rel
    with open(os.path.join(dst, 'Invocador_animations.json'), 'w') as fh: json.dump(man, fh, indent=1)
    circ = rune_circle()
    sh = Image.new('RGBA', (96 * len(circ), 56), (0, 0, 0, 0))
    for i, f in enumerate(circ): sh.alpha_composite(f.img(), (i * 96, 0))
    eff = os.path.join(ROOT, 'Assets', 'Art', 'World', 'Effects'); sh.save(os.path.join(eff, 'rune_circle_anim_96x56.png'))
    # preview: idle in 4 directions, an attack, a cast, death, over the circle
    pv = Image.new('RGBA', (8 * 64, 64 + 64), (24, 18, 34, 255))
    pv.alpha_composite(circ[0].img(), (8, 70)); pv.alpha_composite(circ[3].img(), (110, 70))
    shots = [figure(d, 0.2) for d in ('Down', 'Right', 'Up', 'Left')] + [figure('Down', 0.4, pose=1), figure('Down', 0.6, cast=1),
             figure('Down', 0.3, recoil=1), figure('Down', 0.3, dissolve=0.6)]
    for i, f in enumerate(shots): pv.alpha_composite(f.img(), (i * 64, 0))
    over = figure('Down', 0.1)
    pv.alpha_composite(over.img(), (8 + 16, 64 + 2))
    pv.resize((pv.width * 3, pv.height * 3), Image.NEAREST).save(os.path.join(ROOT, 'Documentation', 'Previews', 'summoner_preview.png'))
    print(len(man['clips']), 'clips')


if __name__ == '__main__':
    build()
