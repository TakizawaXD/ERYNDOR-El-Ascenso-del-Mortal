"""Five hand-designed bosses, drawn procedurally at 128x128 (feet on row 112), 4 directions each.

  python bosses.py [BossKey ...]  -> Assets/Art/Characters/<BossKey>/<cat>/<BossKey>_<Anim>_<Dir>.png + manifest

Same manifest format as build.py, read by CharacterAnimationBuilder (cell 128, pivot (0.5, 16/128)).
Down = front, Up = back, Right = profile, Left = mirror of Right.

  BossInvocador      El Invocador           - hooded giant with a spiked halo, a violet orb and grave chains
  BossOrcWarlord     Gorgrak el Caudillo    - horned skull helm, spiked pauldrons, a cleaver as tall as a man
  BossBloodMother    Madre de Sangre        - a swollen crimson mass with a bone crown, many eyes and a maw
  BossDemonLord      Señor Demonio          - winged, ram horns, a crown of fire, lava veins, burning greatsword
  BossFrostColossus  Coloso de Escarcha     - stone and ice titan with crystal shoulders and a frozen heart
"""
import json, math, os, sys
import numpy as np
from bossart import *

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'Assets', 'Art', 'Characters')
PREVIEW = os.path.join(ROOT, 'Documentation', 'CharacterPreviews')
G = FEET - 1            # ground row


class P:
    """pose: every field optional"""
    def __init__(self, d, base):
        self.bob = d.get('bob', 0); self.step = d.get('step', 0); self.t = d.get('t', 0)
        self.arm = d.get('arm', base.arm0); self.off = d.get('off', base.off0)
        self.glow = d.get('glow', 0); self.lean = d.get('lean', 0); self.mouth = d.get('mouth', 0)
        self.wing = d.get('wing', 0); self.squash = d.get('squash', 0); self.kneel = d.get('kneel', 0)


def limb(c, sh, ang, side, L, w0, w1, rmp, hand=None, hand_r=0):
    dx, dy = limb_dir(ang, side)
    nx, ny = -dy, dx
    ex, ey = sh[0] + dx * L, sh[1] + dy * L
    m = Mask().poly([(sh[0] + nx * w0 / 2, sh[1] + ny * w0 / 2), (ex + nx * w1 / 2, ey + ny * w1 / 2),
                     (ex - nx * w1 / 2, ey - ny * w1 / 2), (sh[0] - nx * w0 / 2, sh[1] - ny * w0 / 2)])
    m.ell(sh[0], sh[1], w0 / 2, w0 / 2)
    c.part(m, rmp)
    if hand is not None:
        c.part(Mask().ell(ex + dx, ey + dy, hand_r, hand_r), hand)
    return (ex + dx * (hand_r + 1), ey + dy * (hand_r + 1)), (dx, dy)


def local(origin, d, pts):
    """(u along d, v across) -> canvas points"""
    ox, oy = origin; dx, dy = d; nx, ny = -dy, dx
    return [(ox + u * dx + v * nx, oy + u * dy + v * ny) for u, v in pts]


def dark(rmp, k=1):
    return [rmp[max(0, i - k)] for i in range(len(rmp))]


class Boss:
    key = ''
    arm0, off0 = 30, 15
    hover = 0
    slash = [hx('#ffffff'), hx('#ffe8b0'), hx('#f0a040')]
    ember = hx('#ffffff')
    flash = hx('#ffffff')

    def frame(self, v, d):
        p = P(d, self)
        c = Canvas()
        self.draw(c, v, p)
        f = c.finish()
        if p.lean:
            top = f.copy(); top[FEET - 34:] = 0
            f[:FEET - 34] = 0
            f = over(f, shift(top, p.lean if v != 'U' else 0, 0 if v == 'R' else abs(p.lean) // 2 * (1 if v == 'D' else -1)))
        return f


# ======================================================================== EL INVOCADOR
class Invocador(Boss):
    key = 'BossInvocador'
    arm0, off0 = 62, 14
    ROBE = ramp('#07040d', '#100a1c', '#1a1230', '#271b46', '#36265e', '#4c3880')
    HALO = ramp('#3a2e22', '#6e5a3c', '#a88e58', '#dcc688', '#fff2c4')
    BONE = ramp('#3a3048', '#6a5a7a', '#a898b8', '#dcd0e8')
    CHAIN = ramp('#24242e', '#4e4e5e', '#8a8a9e', '#c4c4d4')
    VIOLET, VIOLET2 = hx('#d6a8ff'), hx('#8a3ce0')
    slash = [hx('#ffffff'), hx('#e2c4ff'), hx('#a060f0'), hx('#6a2ab0')]
    ember = hx('#c48cff')

    def halo(self, c, cx, cy, p, edge_on=False):
        hot = p.glow >= 2
        m = Mask()
        if edge_on:
            m.ell(cx, cy, 3, 15).ell(cx, cy, 1, 13, on=False)
            for k in (-1, 1):
                for i, L in enumerate((7, 5, 4)):
                    y = cy + k * (15 + L / 2); m.poly([(cx - 1 - i * 2, cy + k * (13 - i * 4)), (cx + 1 - i * 2, cy + k * (13 - i * 4)), (cx - i * 3, cy + k * (15 + L))])
        else:
            m.ell(cx, cy, 15, 15).ell(cx, cy, 12, 12, on=False)
            for i in range(12):
                a = math.radians(i * 30 + (p.t * 4 if hot else 0))
                L = 22 if i % 2 == 0 else 18
                b0 = (cx + math.cos(a - .1) * 14, cy + math.sin(a - .1) * 14)
                b1 = (cx + math.cos(a + .1) * 14, cy + math.sin(a + .1) * 14)
                m.poly([b0, b1, (cx + math.cos(a) * L, cy + math.sin(a) * L)])
        if hot:
            c.emit(m, hx('#f6e4ff'), self.VIOLET, halo=(190, 120, 255, 120), radius=2)
        else:
            c.part(m, self.HALO, seam=False)

    def orb(self, c, x, y, p):
        r = 4 + (1 if p.glow >= 1 else 0) + (1 if p.glow >= 2 else 0)
        c.emit(Mask().ell(x, y, r, r), hx('#ffffff'), self.VIOLET, halo=(170, 90, 255, 150), radius=3)
        for i in range(3):
            a = math.radians(p.t * 40 + i * 120)
            c.pixels([(x + math.cos(a) * (r + 4), y + math.sin(a) * (r + 3))], self.VIOLET)

    def chain(self, c, x, y, p, sway=0):
        pts = []
        yy = y
        while yy < G - 1:
            k = (yy - y) / max(1, G - y)
            pts.append((x + sway * k * k, yy)); yy += 2
        for i, (px, py) in enumerate(pts):
            c.pixels([(px, py)], self.CHAIN[2 if i % 2 else 3])
            if i % 2: c.pixels([(px + 1, py)], self.CHAIN[1])

    def robe_pts(self, w0, w1, top, bot, step, cx=64):
        hem = []
        n = 9
        for i in range(n + 1):
            x = cx - w1 + 2 * w1 * i / n + step * (1 - abs(i - n / 2) / (n / 2))
            hem.append((x, bot - (3 if i % 2 else 0)))
        return [(cx - w0, top), (cx + w0, top), (cx + w0 + 5, top + 18)] + hem[::-1][:1] + hem[::-1][1:] + [(cx - w0 - 5, top + 18)]

    def draw(self, c, v, p):
        b = p.bob - 3 - p.kneel                       # floats above the ground
        top, bot = 50 + b, G - 2 + p.bob + p.kneel // 2
        if v == 'D' or v == 'U':
            front = v == 'D'
            ms = 1 if front else -1                     # side of the orb arm
            if front: self.halo(c, 64, 36 + b, p)
            # off arm (chain) behind the robe edge
            robe = Mask().poly(self.robe_pts(12, 22, top, bot, p.step * 2))
            c.part(robe, self.ROBE)
            # glowing trim
            if front:
                trim = Mask().rect(63, top + 14, 64, bot - 4)
                for yy in (top + 22, top + 34, top + 46):
                    trim.poly([(63.5, yy - 3), (66.5, yy), (63.5, yy + 3), (60.5, yy)]).poly([(63.5, yy - 1), (64.5, yy), (63.5, yy + 1), (62.5, yy)], on=False)
                c.emit(trim, self.VIOLET if p.glow else self.VIOLET2, hx('#6a2ab0'), halo=(150, 70, 230, 70) if p.glow else None, radius=1)
            else:
                sig = Mask().ell(64, top + 26, 9, 9).ell(64, top + 26, 8, 8, on=False).line([(64, top + 15), (64, top + 37)]).line([(55, top + 26), (73, top + 26)])
                c.emit(sig, self.VIOLET2, None, halo=(140, 60, 220, 60) if p.glow else None, radius=1)
            mantle = Mask().poly([(46, top), (82, top), (88, top + 10), (83, top + 13), (79, top + 9), (74, top + 15), (69, top + 10),
                                  (64, top + 17), (59, top + 10), (54, top + 15), (49, top + 9), (45, top + 13), (40, top + 10)])
            c.part(mantle, dark(self.ROBE, -1) if False else self.ROBE[1:] + [hx('#7a5cb8')])
            hood = Mask().poly([(64, 21 + b), (72, 29 + b), (76, 40 + b), (75, 51 + b), (53, 51 + b), (52, 40 + b), (56, 29 + b)])
            c.part(hood, self.ROBE)
            if front:
                c.flat(Mask().ell(64, 42 + b, 6, 7), hx('#050308'))
                eye = 3 if p.glow >= 1 else 2
                c.emit(Mask().rect(60, 42 + b, 60 + eye - 1, 42 + b).rect(68 - eye + 1, 42 + b, 68, 42 + b), hx('#f4e0ff'), None,
                       halo=(200, 120, 255, 150), radius=1)
            # chain arm
            hand, d = limb(c, (50 if front else 78, top + 4), p.off, -ms, 17, 7, 9, self.ROBE[1:], self.BONE, 2)
            self.chain(c, hand[0], hand[1] + 2, p, sway=-ms * (3 + p.step * 2))
            # orb arm
            hand, d = limb(c, (78 if front else 50, top + 4), p.arm, ms, 16, 7, 9, self.ROBE[1:], self.BONE, 2)
            self.orb(c, hand[0] + d[0] * 4, hand[1] + d[1] * 4, p)
            if not front: self.halo(c, 64, 36 + b, p)
            if p.glow >= 2:
                f = c.f
                c.f = ring(f, 64, G, 26 + p.t % 3 * 2, hx('#a060f0'), w=2)
        else:   # profile, facing right
            self.halo(c, 58, 36 + b, p, edge_on=True)
            hand, d = limb(c, (60, top + 4), p.off, -1, 15, 6, 8, dark(self.ROBE), self.BONE, 2)
            self.chain(c, hand[0], hand[1] + 2, p, sway=-4 - p.step * 2)
            robe = Mask().poly([(57, top), (71, top), (75, top + 18), (80 + p.step, bot), (76, bot - 3), (70, bot), (64, bot - 3),
                                (58, bot), (52, bot - 3), (47 + p.step, bot), (51, top + 18)])
            c.part(robe, self.ROBE)
            c.emit(Mask().rect(72, top + 16, 73, bot - 6), self.VIOLET2, None)
            hood = Mask().poly([(60, 21 + b), (69, 29 + b), (73, 40 + b), (71, 51 + b), (55, 51 + b), (53, 38 + b), (55, 28 + b)])
            c.part(hood, self.ROBE)
            c.flat(Mask().ell(70, 42 + b, 3, 6), hx('#050308'))
            c.emit(Mask().rect(70, 42 + b, 72, 42 + b), hx('#f4e0ff'), None, halo=(200, 120, 255, 150), radius=1)
            mantle = Mask().poly([(54, top), (73, top), (77, top + 10), (72, top + 14), (66, top + 9), (60, top + 15), (55, top + 9), (51, top + 12)])
            c.part(mantle, self.ROBE[1:] + [hx('#7a5cb8')])
            hand, d = limb(c, (66, top + 4), p.arm, 1, 15, 7, 9, self.ROBE[1:], self.BONE, 2)
            self.orb(c, hand[0] + d[0] * 4, hand[1] + d[1] * 4, p)
            if p.glow >= 2:
                c.f = ring(c.f, 64, G, 26 + p.t % 3 * 2, hx('#a060f0'), w=2)


# ======================================================================== GORGRAK, ORC WARLORD
class OrcWarlord(Boss):
    key = 'BossOrcWarlord'
    arm0, off0 = 24, 18
    SKIN = ramp('#10140a', '#202a14', '#34421e', '#4c5e2a', '#68783a', '#8c9c52')
    IRON = ramp('#16161c', '#2c2d38', '#4c4f5e', '#767c90', '#aab2c4', '#dfe6f0')
    BONE = ramp('#3e3224', '#7a6648', '#b8a27a', '#e6d8b4', '#fff6dc')
    LEATHER = ramp('#1a100a', '#342014', '#54341e', '#74502c')
    CLOTH = ramp('#2e080a', '#561018', '#861c22', '#b4302c', '#d85040')
    EYE = hx('#ffe27a')
    slash = [hx('#ffffff'), hx('#ffe6b0'), hx('#e8a050'), hx('#a05a28')]
    ember = hx('#f0a050')

    def cleaver(self, c, hand, d, big=1.0):
        # handle back behind the fist, long haft forward, a huge notched blade on the end
        haft = Mask().poly(local(hand, d, [(-7, -1.5), (30 * big, -1.5), (30 * big, 1.5), (-7, 1.5)]))
        c.part(haft, self.LEATHER + [hx('#94683a')])
        blade = local(hand, d, [(14 * big, 1), (34 * big, 1), (38 * big, 6), (36 * big, 14), (30 * big, 18), (24 * big, 15),
                                (20 * big, 17), (15 * big, 12), (13 * big, 6)])
        c.part(Mask().poly(blade), self.IRON)
        edge = local(hand, d, [(30 * big, 18), (36 * big, 14), (38 * big, 6)])
        c.part(Mask().line(edge, 1), [hx('#f4f8ff')], seam=False, flat=True)
        c.part(Mask().ell(*local(hand, d, [(22 * big, 7)])[0], 2, 2), self.BONE, seam=False)    # bone rivet
        c.part(Mask().ell(*local(hand, d, [(31 * big, 0)])[0], 2, 2), self.BONE, seam=False)

    def horns(self, c, cx, cy, side, back=False):
        pts = [(cx + side * 7, cy), (cx + side * 15, cy - 4), (cx + side * 21, cy - 12), (cx + side * 20, cy - 22), (cx + side * 16, cy - 28)]
        for i in range(len(pts) - 1):
            c.part(Mask().line([pts[i], pts[i + 1]], 6 - i), self.BONE, seam=i == 0)
        c.part(Mask().line([pts[3], pts[4]], 2), self.BONE[2:], seam=False)

    def pauldron(self, c, cx, cy, side):
        c.part(Mask().ell(cx, cy, 11, 8), self.IRON)
        for i, (dx, L) in enumerate(((-6, 9), (0, 12), (6, 9))):
            x = cx + dx * side
            c.part(Mask().poly([(x - 2, cy - 5), (x + 2, cy - 5), (x + side * 2, cy - 5 - L)]), self.BONE, seam=False)

    def legs(self, c, p, cxs=(55, 73), w=10):
        for i, x in enumerate(cxs):
            lift = (p.step if i == 0 else -p.step)
            fy = G - max(0, lift) * 3 + p.kneel
            c.part(Mask().poly([(x - w / 2, 88 + p.bob), (x + w / 2, 88 + p.bob), (x + w / 2 - 1, fy - 5), (x - w / 2 + 1, fy - 5)]), self.SKIN)
            c.part(Mask().poly([(x - w / 2 - 1, fy - 8), (x + w / 2 + 1, fy - 8), (x + w / 2 + 2, fy), (x - w / 2 - 2, fy)]), self.IRON)

    def draw(self, c, v, p):
        b = p.bob + p.kneel
        if v in ('D', 'U'):
            front = v == 'D'
            ms = 1 if front else -1
            self.legs(c, p)
            if not front:   # hide cape
                c.part(Mask().poly([(46, 60 + b), (82, 60 + b), (86, 96 + b), (78, 92 + b), (72, 98 + b), (64, 93 + b), (56, 98 + b), (50, 92 + b), (42, 96 + b)]),
                       ramp('#2a1a10', '#4a3020', '#6a4a30', '#8c6a46', '#ae8c62'))
            torso = Mask().ell(64, 74 + b, 21, 17)
            c.part(torso, self.SKIN)
            if front:
                c.part(Mask().line([(47, 62 + b), (80, 88 + b)], 4), self.LEATHER, seam=True)
                c.part(Mask().ell(58, 68 + b, 1, 1).ell(70, 70 + b, 1, 1), [hx('#3a1a0c')], seam=False, flat=True)   # scars
            c.part(Mask().rect(44, 85 + b, 84, 90 + b), self.LEATHER)
            c.part(Mask().poly([(56, 90 + b), (72, 90 + b), (70, 104 + b), (58, 104 + b)]), self.CLOTH)
            if front:
                c.part(Mask().ell(64, 87 + b, 4, 4), self.BONE)
                c.flat(Mask().rect(62, 86 + b, 62, 86 + b).rect(66, 86 + b, 66, 86 + b), hx('#1a1010'))
            # head sunk between the shoulders
            c.part(Mask().ell(64, 57 + b, 10, 8), self.SKIN)
            c.part(Mask().poly([(54, 58 + b), (74, 58 + b), (72, 66 + b), (56, 66 + b)]), self.SKIN)
            for s in (-1, 1): self.horns(c, 64, 49 + b, s)
            c.part(Mask().ell(64, 50 + b, 10, 6).rect(53, 50 + b, 75, 56 + b, on=False), self.BONE)
            if front:
                c.flat(Mask().rect(57, 49 + b, 59, 51 + b).rect(69, 49 + b, 71, 51 + b), hx('#100808'))   # skull sockets
                paint = Mask().poly([(55, 56 + b), (60, 58 + b), (60, 60 + b), (55, 58 + b)]).poly([(73, 56 + b), (68, 58 + b), (68, 60 + b), (73, 58 + b)])
                paint.line([(52, 66 + b), (58, 72 + b)], 2).line([(76, 66 + b), (70, 72 + b)], 2).line([(55, 74 + b), (61, 80 + b)], 2).line([(73, 74 + b), (67, 80 + b)], 2)
                c.flat(paint, self.CLOTH[3])
                c.flat(Mask().line([(57, 53 + b), (62, 55 + b)], 1).line([(71, 53 + b), (66, 55 + b)], 1), hx('#0a0806'))     # brow
                c.emit(Mask().rect(59, 56 + b, 61, 56 + b).rect(67, 56 + b, 69, 56 + b), self.EYE, None, halo=(255, 170, 40, 150), radius=1)
                c.flat(Mask().poly([(56, 61 + b), (72, 61 + b), (70, 65 + b), (58, 65 + b)]), hx('#1a0606'))
                for x in range(58, 71, 3):
                    c.part(Mask().poly([(x - 1, 65 + b), (x + 1, 65 + b), (x, 62 + b)]), self.BONE[2:], seam=False)
                for x in (57, 71):
                    c.part(Mask().poly([(x - 1.5, 63 + b), (x + 1.5, 63 + b), (x + (x - 64) // 6, 55 + b)]), self.BONE, seam=False)
            self.pauldron(c, 43, 62 + b, -1); self.pauldron(c, 85, 62 + b, 1)
            # off arm then weapon arm
            limb(c, (42, 66 + b), p.off, -ms if front else ms, 18, 10, 9, self.SKIN, self.SKIN, 4)
            hand, d = limb(c, (86, 66 + b) if front else (42, 66 + b), p.arm, ms, 18, 10, 9, self.SKIN, self.SKIN, 4)
            self.cleaver(c, hand, d, 1.3)
            if not front: self.pauldron(c, 43, 62 + b, -1); self.pauldron(c, 85, 62 + b, 1)
        else:
            far = dark(self.SKIN)
            limb(c, (60, 64 + b), p.off, -1, 17, 9, 8, far, far, 4)
            self.legs(c, p, cxs=(58, 68), w=10)
            c.part(Mask().ell(63, 74 + b, 16, 17), self.SKIN)
            c.part(Mask().rect(47, 85 + b, 79, 90 + b), self.LEATHER)
            c.part(Mask().poly([(66, 90 + b), (76, 90 + b), (74, 104 + b), (66, 104 + b)]), self.CLOTH)
            c.part(Mask().ell(69, 57 + b, 9, 8), self.SKIN)
            c.part(Mask().poly([(66, 58 + b), (80, 58 + b), (78, 66 + b), (64, 66 + b)]), self.SKIN)
            self.horns(c, 62, 49 + b, -1)
            c.part(Mask().ell(68, 50 + b, 10, 6).rect(57, 50 + b, 79, 56 + b, on=False), self.BONE)
            c.flat(Mask().rect(73, 49 + b, 75, 51 + b), hx('#100808'))
            c.emit(Mask().rect(74, 55 + b, 76, 55 + b), self.EYE, None, halo=(255, 170, 40, 150), radius=1)
            c.part(Mask().poly([(76.5, 63 + b), (79.5, 63 + b), (78, 57 + b)]), self.BONE, seam=False)
            self.pauldron(c, 64, 62 + b, 1)
            hand, d = limb(c, (66, 66 + b), p.arm, 1, 18, 10, 9, self.SKIN, self.SKIN, 4)
            self.cleaver(c, hand, d, 1.3)


# ======================================================================== MADRE DE SANGRE
class BloodMother(Boss):
    key = 'BossBloodMother'
    arm0, off0 = 40, 40
    FLESH = ramp('#24040f', '#480a1e', '#74142c', '#a2283e', '#cc4c58', '#ee8a84')
    BONE = ramp('#3e3224', '#7a6648', '#b8a27a', '#e6d8b4', '#fff6dc')
    SAC = ramp('#4a0c2a', '#7e1e52', '#b23c80', '#e070b4', '#ffb0de')
    EYE, EYE2 = hx('#fff27a'), hx('#e09a20')
    slash = [hx('#ffd0d0'), hx('#f06070'), hx('#b02040'), hx('#600c20')]
    ember = hx('#f06070')

    def tendril(self, c, x0, y0, ang, side, L, w, t, rmp=None):
        pts = []
        for i in range(6):
            k = i / 5
            a = math.radians(ang + math.sin(t * 1.3 + i) * 12 * k)
            pts.append((x0 + side * math.sin(a) * L * k + math.sin(t + i) * k, y0 + math.cos(a) * L * k))
        for i in range(5):
            c.part(Mask().line([pts[i], pts[i + 1]], max(1, w - i * w / 5)), rmp or self.FLESH, seam=i == 0)
        return pts[-1]

    def eye(self, c, x, y, r, look=0):
        c.emit(Mask().ell(x, y, r, r), self.EYE, self.EYE2, halo=(255, 200, 60, 110), radius=1)
        c.flat(Mask().rect(x + look, y - (1 if r > 2 else 0), x + look, y + (1 if r > 2 else 0)), hx('#1a0606'))

    def draw(self, c, v, p):
        b, sq = p.bob + p.kneel, p.squash
        rx, ry = 27 + sq, 22 - sq
        cy = G - ry + b // 2
        t = p.t
        if v in ('D', 'U'):
            front = v == 'D'
            for i, (x, a, s) in enumerate(((44, 70, -1), (52, 40, -1), (76, 40, 1), (84, 70, 1))):
                self.tendril(c, x, G - 4, a + p.step * 8 * s, s, 14, 5, t + i)
            # whipping arms (big tendrils from the flanks)
            body = Mask().ell(64, cy, rx, ry).ell(64, cy - ry + 4 - b // 2, 19 - sq, 15 - sq).ell(42, G - 9, 10, 9).ell(86, G - 9, 10, 9)
            c.part(body, self.FLESH)
            sp = 1 + (t % 2) + p.glow
            for (x, y, r) in ((45, cy - 6, 5), (84, cy - 4, 6), (71, cy - ry + 2, 4), (52, cy + 8, 3)):
                c.part(Mask().ell(x, y, r + sp // 2, r + sp // 2), self.SAC)
                c.emit(Mask().ell(x - 1, y - 1, 1, 1), hx('#ffd8ee'), None)
            # bone crown
            ty = cy - ry - 12 + b // 2
            for i, dx in enumerate((-14, -7, 0, 7, 14)):
                L = 12 if dx == 0 else 9 if abs(dx) == 7 else 6
                c.part(Mask().poly([(64 + dx - 3, ty + 8 + abs(dx) // 3), (64 + dx + 3, ty + 8 + abs(dx) // 3), (64 + dx * 1.2, ty + 8 - L)]), self.BONE)
            if front:
                mo = 3 + p.mouth
                c.flat(Mask().ell(64, cy + 6, 13, mo), hx('#1a0408'))
                c.flat(Mask().ell(64, cy + 6 + mo // 2, 9, max(1, mo // 2)), hx('#4a0a14'))
                for i in range(7):
                    x = 54 + i * 3.4
                    c.part(Mask().poly([(x - 1, cy + 6 - mo), (x + 1.5, cy + 6 - mo), (x + .2, cy + 6 - mo + 3)]), self.BONE[2:], seam=False)
                    c.part(Mask().poly([(x, cy + 6 + mo + 1), (x + 2, cy + 6 + mo + 1), (x + 1, cy + 6 + mo - 2)]), self.BONE[2:], seam=False)
                self.eye(c, 64, cy - 9, 3 + (1 if p.glow else 0))
                for (x, y) in ((54, cy - 4), (74, cy - 4), (57, cy - 13), (71, cy - 13), (48, cy + 2), (80, cy + 2)):
                    self.eye(c, x, y, 1.5)
            else:
                for i in range(6):
                    x = 50 + i * 5.6
                    c.part(Mask().poly([(x - 2, cy - 6 + abs(i - 2.5) * 2), (x + 2, cy - 6 + abs(i - 2.5) * 2), (x, cy - 14 + abs(i - 2.5) * 2)]), self.BONE)
            for s, a in ((-1, p.off), (1, p.arm)):
                tip = self.tendril(c, 64 + s * 22, cy - 6, a, s, 22, 7, t * 2 + s)
                c.part(Mask().poly([(tip[0] - 2, tip[1]), (tip[0] + 2, tip[1]), (tip[0] + s * 3, tip[1] + 5)]), self.BONE, seam=False)
        else:
            for i, (x, a, s) in enumerate(((48, 70, -1), (56, 40, -1), (72, 40, 1), (80, 70, 1))):
                self.tendril(c, x, G - 4, a + p.step * 8 * s, s, 12, 5, t + i)
            self.tendril(c, 50, cy - 6, p.off, -1, 20, 6, t * 2, dark(self.FLESH))
            body = Mask().ell(62, cy, rx - 6, ry).ell(60, cy - ry + 4 - b // 2, 16 - sq, 14 - sq)
            c.part(body, self.FLESH)
            for (x, y, r) in ((50, cy - 4, 6), (60, cy - ry + 2, 4)):
                c.part(Mask().ell(x, y, r + (t % 2), r + (t % 2)), self.SAC)
            ty = cy - ry - 12 + b // 2
            for dx in (-10, -3, 4):
                c.part(Mask().poly([(60 + dx - 3, ty + 9), (60 + dx + 3, ty + 9), (60 + dx - 2, ty - 2)]), self.BONE)
            mo = 3 + p.mouth
            c.flat(Mask().ell(82, cy + 6, 5, mo), hx('#1a0408'))
            for i in range(3):
                c.part(Mask().poly([(78 + i * 3, cy + 6 - mo), (80 + i * 3, cy + 6 - mo), (79 + i * 3, cy + 9 - mo)]), self.BONE[2:], seam=False)
            self.eye(c, 78, cy - 8, 3 + (1 if p.glow else 0), look=1)
            self.eye(c, 82, cy - 1, 1.5, look=1); self.eye(c, 72, cy - 14, 1.5, look=1)
            tip = self.tendril(c, 74, cy - 6, p.arm, 1, 22, 7, t * 2)
            c.part(Mask().poly([(tip[0] - 2, tip[1]), (tip[0] + 2, tip[1]), (tip[0] + 3, tip[1] + 5)]), self.BONE, seam=False)


# ======================================================================== SEÑOR DEMONIO
class DemonLord(Boss):
    key = 'BossDemonLord'
    arm0, off0 = 28, 22
    HIDE = ramp('#0c080e', '#1a121e', '#2c202e', '#423242', '#5c4858', '#7a6272')
    HORN = ramp('#181010', '#382820', '#664c36', '#9c7c5a', '#d2b88e')
    WING = ramp('#140606', '#2e0c0c', '#521616', '#782420', '#9a3628')
    METAL = ramp('#14100e', '#342a28', '#5e5250', '#968a86', '#d0c8c4')
    LAVA, LAVA2 = hx('#ffe080'), hx('#f06020')
    slash = [hx('#ffffff'), hx('#ffe080'), hx('#f88020'), hx('#c02818')]
    ember = hx('#ff9030')

    def wing(self, c, sx, sy, side, flap, rmp=None, bones=None):
        f = flap
        tips = [(sx + side * 30, sy - 20 - f * 4), (sx + side * 38, sy - 2 - f * 2), (sx + side * 34, sy + 14 - f), (sx + side * 24, sy + 24)]
        mem = [(sx, sy)] + [tips[0]]
        for i in range(1, len(tips)):
            a, b = tips[i - 1], tips[i]
            mem.append(((a[0] + b[0]) / 2 - side * 4, (a[1] + b[1]) / 2 + 3))
            mem.append(b)
        mem.append((sx + side * 6, sy + 14))
        c.part(Mask().poly(mem), rmp or self.WING)
        for tp in tips:
            c.part(Mask().line([(sx, sy), tp], 2), bones or self.HIDE, seam=False)
        c.part(Mask().poly([(tips[0][0] - 2, tips[0][1]), (tips[0][0] + 2, tips[0][1]), (tips[0][0] + side * 2, tips[0][1] - 5)]), self.HORN, seam=False)

    def horns(self, c, cx, cy, side):
        pts = [(cx + side * 4, cy), (cx + side * 9, cy - 6), (cx + side * 11, cy - 14), (cx + side * 9, cy - 21), (cx + side * 5, cy - 25)]
        for i in range(len(pts) - 1):
            c.part(Mask().line([pts[i], pts[i + 1]], 5 - i), self.HORN, seam=i == 0)

    def crown(self, c, cx, cy, t, big=0):
        m = Mask()
        for i, dx in enumerate((-6, -3, 0, 3, 6)):
            h = 5 + (3 if dx == 0 else 0) + ((t + i) % 3) + big * 2
            m.poly([(cx + dx - 1.5, cy), (cx + dx + 1.5, cy), (cx + dx + ((t + i) % 2) - .5, cy - h)])
        c.emit(m, self.LAVA, self.LAVA2, halo=(255, 120, 30, 130), radius=2)

    def sword(self, c, hand, d, burn):
        c.part(Mask().poly(local(hand, d, [(-6, -1.5), (6, -1.5), (6, 1.5), (-6, 1.5)])), self.HORN)
        c.part(Mask().poly(local(hand, d, [(3, -6), (6, -6), (6, 6), (3, 6)])), self.METAL)
        c.part(Mask().poly(local(hand, d, [(6, -3.5), (38, -2.5), (44, 0), (38, 3.5), (6, 3.5)])), self.METAL)
        c.emit(Mask().line(local(hand, d, [(8, 3.5), (38, 3.5), (44, 0)]), 1), self.LAVA, self.LAVA2,
               halo=(255, 110, 30, 120) if burn else None, radius=1)
        c.emit(Mask().line(local(hand, d, [(10, 0), (34, 0)]), 1), self.LAVA2, None)

    def legs(self, c, p, xs=(56, 72)):
        for i, x in enumerate(xs):
            lift = p.step if i == 0 else -p.step
            fy = G - max(0, lift) * 3 + p.kneel
            s = -1 if i == 0 else 1
            c.part(Mask().poly([(x - 5, 84 + p.bob), (x + 5, 84 + p.bob), (x + s * 3 + 4, 96 + p.bob), (x + s * 3 - 4, 96 + p.bob)]), self.HIDE)
            c.part(Mask().poly([(x + s * 3 - 4, 95 + p.bob), (x + s * 3 + 4, 95 + p.bob), (x + 3, fy - 3), (x - 3, fy - 3)]), self.HIDE)
            c.part(Mask().poly([(x - 4, fy - 4), (x + 4, fy - 4), (x + 5, fy), (x - 5, fy)]), self.HORN)

    def draw(self, c, v, p):
        b = p.bob + p.kneel
        if v in ('D', 'U'):
            front = v == 'D'
            ms = 1 if front else -1
            if front:
                self.wing(c, 54, 60 + b, -1, p.wing); self.wing(c, 74, 60 + b, 1, p.wing)
            # tail
            if front:
                c.part(Mask().line([(64, 86 + b), (80, 96), (88, 104), (94, 100)], 3), self.HIDE)
            self.legs(c, p)
            torso = Mask().poly([(46, 57 + b), (82, 57 + b), (78, 70 + b), (72, 86 + b), (56, 86 + b), (50, 70 + b)])
            c.part(torso, self.HIDE)
            if front:
                cr = Mask().line([(56, 62 + b), (60, 66 + b), (58, 71 + b), (62, 76 + b)]).line([(72, 62 + b), (68, 67 + b), (70, 72 + b), (66, 78 + b)]).line([(64, 66 + b), (64, 82 + b)])
                c.emit(cr, self.LAVA if p.glow else self.LAVA2, None, halo=(255, 110, 30, 90) if p.glow else None, radius=1)
            c.part(Mask().rect(54, 84 + b, 74, 88 + b), self.METAL)
            c.part(Mask().poly([(56, 88 + b), (72, 88 + b), (74, 100 + b), (68, 97 + b), (64, 101 + b), (60, 97 + b), (54, 100 + b)]), self.WING)
            # head
            c.part(Mask().ell(64, 49 + b, 7, 8).poly([(58, 52 + b), (70, 52 + b), (64, 60 + b)]), self.HIDE)
            for s in (-1, 1): self.horns(c, 64, 45 + b, s)
            self.crown(c, 64, 41 + b, p.t, p.glow)
            if front:
                c.emit(Mask().rect(60, 49 + b, 62, 49 + b).rect(66, 49 + b, 68, 49 + b), hx('#fff6c0'), None, halo=(255, 140, 40, 160), radius=1)
                c.part(Mask().poly([(61, 55 + b), (62.5, 55 + b), (61.5, 58 + b)]).poly([(66, 55 + b), (67.5, 55 + b), (66.5, 58 + b)]), self.HORN[3:], seam=False)
            # shoulders + arms
            for s in (-1, 1):
                c.part(Mask().ell(64 + s * 18, 59 + b, 6, 5), self.HIDE)
                c.part(Mask().poly([(64 + s * 18 - 2, 56 + b), (64 + s * 18 + 2, 56 + b), (64 + s * 21, 49 + b)]), self.HORN, seam=False)
            limb(c, (46 if front else 82, 62 + b), p.off, -ms, 17, 7, 6, self.HIDE, self.HIDE, 3)
            hand, d = limb(c, (82 if front else 46, 62 + b), p.arm, ms, 17, 7, 6, self.HIDE, self.HIDE, 3)
            self.sword(c, hand, d, p.glow or p.arm > 90)
            if not front:
                c.part(Mask().line([(64, 60 + b), (64, 82 + b)], 2), self.HORN)
                self.wing(c, 54, 60 + b, -1, p.wing); self.wing(c, 74, 60 + b, 1, p.wing)
        else:
            self.wing(c, 58, 60 + b, -1, p.wing, dark(self.WING), dark(self.HIDE))
            c.part(Mask().line([(58, 86 + b), (44, 96), (38, 104), (32, 100)], 3), self.HIDE)
            limb(c, (60, 62 + b), p.off, -1, 16, 6, 6, dark(self.HIDE), dark(self.HIDE), 3)
            self.legs(c, p, xs=(60, 68))
            c.part(Mask().poly([(54, 57 + b), (74, 57 + b), (74, 70 + b), (70, 86 + b), (58, 86 + b), (54, 70 + b)]), self.HIDE)
            c.emit(Mask().line([(70, 62 + b), (67, 68 + b), (70, 74 + b)]), self.LAVA2, None)
            c.part(Mask().rect(57, 84 + b, 71, 88 + b), self.METAL)
            c.part(Mask().ell(67, 49 + b, 6, 8).poly([(64, 52 + b), (75, 53 + b), (70, 60 + b)]), self.HIDE)
            self.horns(c, 63, 45 + b, -1)
            self.crown(c, 66, 41 + b, p.t, p.glow)
            c.emit(Mask().rect(70, 49 + b, 72, 49 + b), hx('#fff6c0'), None, halo=(255, 140, 40, 160), radius=1)
            c.part(Mask().ell(66, 59 + b, 6, 5), self.HIDE)
            hand, d = limb(c, (67, 62 + b), p.arm, 1, 17, 7, 6, self.HIDE, self.HIDE, 3)
            self.sword(c, hand, d, p.glow or p.arm > 90)


# ======================================================================== COLOSO DE ESCARCHA
class FrostColossus(Boss):
    key = 'BossFrostColossus'
    arm0, off0 = 14, 14
    ROCK = ramp('#10182a', '#1e2c46', '#34486a', '#506c92', '#7894b8', '#a8c0dc')
    ICE = ramp('#123e5c', '#1e6a90', '#3aa0c8', '#78d0ea', '#c8f2ff', '#ffffff')
    SNOW = ramp('#6e7e98', '#a8b8cc', '#dae4f0', '#f6faff')
    CORE, CORE2 = hx('#f0ffff'), hx('#40d0ff')
    slash = [hx('#ffffff'), hx('#c8f2ff'), hx('#60c8f0'), hx('#2a6a9a')]
    ember = hx('#a0e8ff')

    def crystals(self, c, x, y, side, n=3, s=1.0):
        for i in range(n):
            dx = side * (i * 4 - 2)
            L = (14 - i * 3) * s
            c.part(Mask().poly([(x + dx - 2.5, y), (x + dx + 2.5, y), (x + dx + side * (3 + i * 2), y - L)]), self.ICE)

    def fist(self, c, hand, d):
        c.part(Mask().ell(hand[0] + d[0] * 2, hand[1] + d[1] * 2, 7, 7), self.ROCK)
        for k in (-3, 0, 3):
            px, py = local(hand, d, [(6, k)])[0]
            c.part(Mask().poly([(px - 1.5, py), (px + 1.5, py), (px + d[0] * 4, py + d[1] * 4)]), self.ICE, seam=False)

    def legs(self, c, p, xs=(53, 75), w=13):
        for i, x in enumerate(xs):
            lift = p.step if i == 0 else -p.step
            fy = G - max(0, lift) * 3 + p.kneel
            c.part(Mask().poly([(x - w / 2, 86 + p.bob), (x + w / 2, 86 + p.bob), (x + w / 2 + 1, fy), (x - w / 2 - 1, fy)]), self.ROCK)
            c.part(Mask().poly([(x - w / 2 - 1, fy - 4), (x + w / 2 + 1, fy - 4), (x + w / 2 + 1, fy - 2), (x - w / 2 - 1, fy - 2)]), self.ICE[:4], seam=False)

    def draw(self, c, v, p):
        b = p.bob + p.kneel
        if v in ('D', 'U'):
            front = v == 'D'
            ms = 1 if front else -1
            if not front: self.crystals(c, 64, 60 + b, 1, 4, 1.3); self.crystals(c, 60, 62 + b, -1, 3, 1.1)
            self.legs(c, p)
            torso = Mask().poly([(34, 54 + b), (94, 54 + b), (88, 70 + b), (80, 88 + b), (48, 88 + b), (40, 70 + b)])
            c.part(torso, self.ROCK)
            c.part(Mask().poly([(46, 86 + b), (82, 86 + b), (78, 94 + b), (50, 94 + b)]), self.ROCK[:-1])
            if front:
                k = 1 + p.glow
                cracks = Mask().line([(64, 70 + b), (52, 62 + b), (46, 64 + b)]).line([(64, 70 + b), (76, 62 + b), (84, 63 + b)]).line([(64, 70 + b), (60, 82 + b)]).line([(64, 70 + b), (70, 84 + b)])
                c.emit(cracks, self.CORE2, None, halo=(90, 220, 255, 70) if p.glow else None, radius=1)
                c.emit(Mask().poly([(64, 64 + b - k), (69 + k, 70 + b), (64, 76 + b + k), (59 - k, 70 + b)]), self.CORE, self.CORE2, halo=(90, 220, 255, 150), radius=3)
            # snow on shoulders
            c.part(Mask().poly([(34, 54 + b), (50, 52 + b), (52, 56 + b), (44, 58 + b), (36, 58 + b)]).poly([(94, 54 + b), (78, 52 + b), (76, 56 + b), (84, 58 + b), (92, 58 + b)]), self.SNOW)
            # head sunk in the chest
            c.part(Mask().poly([(55, 40 + b), (73, 40 + b), (75, 54 + b), (53, 54 + b)]), self.ROCK)
            c.part(Mask().poly([(54, 40 + b), (74, 40 + b), (72, 37 + b), (56, 37 + b)]), self.SNOW)
            if front:
                c.emit(Mask().rect(58, 47 + b, 61, 47 + b).rect(67, 47 + b, 70, 47 + b), self.CORE, None, halo=(90, 220, 255, 160), radius=1)
            if front: self.crystals(c, 40, 54 + b, -1); self.crystals(c, 88, 54 + b, 1)
            for s, a in ((-ms, p.off), (ms, p.arm)):
                sh = (64 + s * 30, 60 + b)
                hand, d = limb(c, sh, a, s, 22, 13, 11, self.ROCK)
                self.fist(c, hand, d)
            if not front:
                self.crystals(c, 40, 54 + b, -1); self.crystals(c, 88, 54 + b, 1)
                c.emit(Mask().line([(64, 60 + b), (60, 72 + b), (66, 82 + b)]), self.CORE2, None)
        else:
            self.crystals(c, 50, 60 + b, -1, 4, 1.3)
            hand, d = limb(c, (58, 60 + b), p.off, -1, 20, 12, 10, dark(self.ROCK))
            self.fist(c, hand, d)
            self.legs(c, p, xs=(58, 70), w=12)
            c.part(Mask().poly([(48, 54 + b), (78, 54 + b), (80, 70 + b), (74, 88 + b), (52, 88 + b), (48, 70 + b)]), self.ROCK)
            c.emit(Mask().poly([(78, 66 + b), (80, 70 + b), (78, 74 + b)]), self.CORE, self.CORE2, halo=(90, 220, 255, 130), radius=2)
            c.part(Mask().poly([(60, 40 + b), (76, 42 + b), (77, 54 + b), (60, 54 + b)]), self.ROCK)
            c.part(Mask().poly([(59, 40 + b), (77, 42 + b), (75, 38 + b), (61, 37 + b)]), self.SNOW)
            c.emit(Mask().rect(72, 47 + b, 75, 47 + b), self.CORE, None, halo=(90, 220, 255, 160), radius=1)
            c.part(Mask().poly([(48, 54 + b), (66, 52 + b), (68, 56 + b), (50, 58 + b)]), self.SNOW)
            hand, d = limb(c, (66, 60 + b), p.arm, 1, 22, 13, 11, self.ROCK)
            self.fist(c, hand, d)


BOSSES = {b.key: b for b in (Invocador(), OrcWarlord(), BloodMother(), DemonLord(), FrostColossus())}


# ======================================================================== animation
class Anim:
    def __init__(self, cat, frames, fps, loop):
        self.cat, self.frames, self.fps, self.loop = cat, frames, fps, loop


def fx_point(v, kind):
    """where a melee effect lands for a facing"""
    if v == 'D': return 64, G - 10
    if v == 'U': return 64, 52
    return 88, G - 30


def slash_fx(f, v, boss, big=False, fade=False):
    cx, cy = fx_point(v, 'slash')
    r = 30 if big else 24
    if v == 'D': a0, a1 = 10, 170
    elif v == 'U': a0, a1 = 190, 350
    else: a0, a1 = 280, 80
    return arc(f, cx if v != 'R' else 66, cy if v != 'R' else G - 34, r, r - (7 if big else 5), a0, a1, boss.slash, ry=.6 if v != 'R' else 1, fade=fade)


def build(boss):
    out = {}
    views = ('D', 'U', 'R')
    name = {'D': 'Down', 'U': 'Up', 'R': 'Right'}

    def add(anim, cat, fps, loop, poses, post=None):
        for v in views:
            frames = []
            for i, pd in enumerate(poses):
                f = boss.frame(v, pd)
                if post: f = post(f, v, i)
                frames.append(f)
            out[(anim, name[v])] = Anim(cat, frames, fps, loop)
            if v == 'R':
                out[(anim, 'Left')] = Anim(cat, [np.ascontiguousarray(fr[:, ::-1]) for fr in frames], fps, loop)

    a0, o0 = boss.arm0, boss.off0
    add('Idle', 'Idle', 6, True, [dict(t=0), dict(t=1, bob=-1), dict(t=2, bob=-1, glow=1), dict(t=3)])
    add('Walk', 'Walk', 8, True, [dict(t=i, step=s, bob=bb, arm=a0 + s * 6, off=o0 - s * 6, wing=abs(s))
                                  for i, (s, bb) in enumerate(((1, 0), (1, -1), (0, -1), (-1, 0), (-1, -1), (0, -1)))])

    def atk_post(f, v, i):
        if i == 2: return slash_fx(f, v, boss)
        if i == 3: return slash_fx(f, v, boss, fade=True)
        return f
    add('Attack', 'Attack', 12, False, [dict(arm=a0 + 50, squash=1, t=0), dict(arm=165, bob=-1, t=1, wing=1),
                                        dict(arm=50, bob=1, t=2, lean=2, mouth=6), dict(arm=30, t=3, lean=1, mouth=4), dict(t=0)], atk_post)

    def heavy_post(f, v, i):
        if i == 3:
            f = slash_fx(f, v, boss, big=True)
            return ring(f, 64, G, 22, boss.slash[1], w=2)
        if i == 4:
            f = ring(f, 64, G, 32, boss.slash[2], w=2)
            return sparks(f, 64, G - 6, 14, 30, boss.slash[:3], seed=i)
        return f
    add('HeavyAttack', 'Attack', 10, False, [dict(arm=110, off=60, squash=2, t=0), dict(arm=175, off=150, bob=-3, t=1, glow=1, wing=2),
                                             dict(arm=178, off=160, bob=-4, t=2, glow=2, wing=2), dict(arm=24, off=30, bob=2, t=3, lean=2, mouth=8, squash=-2),
                                             dict(arm=20, off=20, bob=1, t=0, mouth=4), dict(t=1)], heavy_post)

    def special_post(f, v, i):
        if i in (2, 3):
            cx, cy = (64, G - 4) if v == 'D' else (64, 40) if v == 'U' else (100, G - 40)
            return sparks(f, cx, cy, 10 + i * 4, 10 + i * 3, boss.slash[:3], seed=i)
        return f
    add('SpecialAttack', 'Special', 10, False, [dict(arm=70, t=0), dict(arm=100, glow=1, t=1, mouth=4), dict(arm=92, glow=2, t=2, lean=1, mouth=8),
                                                dict(arm=88, glow=2, t=3, mouth=6), dict(arm=70, glow=1, t=0), dict(t=1)], special_post)
    add('CastSpell', 'Special', 8, False, [dict(arm=110, off=110, t=0), dict(arm=160, off=160, glow=1, bob=-1, t=1, wing=1),
                                           dict(arm=172, off=172, glow=2, bob=-2, t=2, wing=2, mouth=6), dict(arm=172, off=172, glow=2, bob=-2, t=3, wing=2, mouth=6),
                                           dict(arm=140, off=140, glow=1, bob=-1, t=0), dict(t=1)])

    def hurt_post(f, v, i):
        if i == 0: return tint(f, boss.flash, .75)
        if i == 1: return tint(shift(f, 0, 1), (255, 40, 40), .45)
        return f
    add('Hurt', 'Hurt', 12, False, [dict(t=0), dict(t=0, squash=1, lean=-1), dict(t=0)], hurt_post)

    def death_post(f, v, i):
        if i == 0: return tint(f, boss.flash, .8)
        if i >= 2: return dissolve(f, (i - 1) / 6.0, boss.ember, seed=5)
        return f
    add('Death', 'Death', 8, False, [dict(t=0, squash=1), dict(t=1, kneel=3, arm=10, off=10, squash=2), dict(t=2, kneel=5, arm=5, off=5, squash=3)]
        + [dict(t=i, kneel=6, arm=5, off=5, squash=3) for i in range(3, 8)], death_post)
    return out


def write(key):
    boss = BOSSES[key]
    out = build(boss)
    root = os.path.join(OUT, key)
    clips = []
    for (anim, d), a in sorted(out.items()):
        rel = f'{a.cat}/{key}_{anim}_{d}.png'
        save_sheet(a.frames, os.path.join(root, rel))
        clips.append(dict(name=anim, dir=d, file=rel, frames=len(a.frames), seq=list(range(len(a.frames))), fps=a.fps,
                          loop=a.loop, size=[C * len(a.frames), C]))
    with open(os.path.join(root, f'{key}_animations.json'), 'w') as fh:
        json.dump(dict(character=key, cell=C, pivot=[0.5, (C - FEET) / C], ppu=16, clips=clips), fh, indent=1)
    return out


def preview(keys, path, scale=2):
    """front/back/side idle + attack strike + cast of each boss, over a dark arena tone"""
    from PIL import Image
    rows = []
    for k in keys:
        out = build(BOSSES[k]) if not isinstance(k, dict) else k
        cells = [out[('Idle', 'Down')].frames[0], out[('Idle', 'Up')].frames[0], out[('Idle', 'Right')].frames[0],
                 out[('Attack', 'Down')].frames[2], out[('HeavyAttack', 'Right')].frames[3], out[('CastSpell', 'Down')].frames[2],
                 out[('Death', 'Down')].frames[4]]
        rows.append(cells)
    W, H = C * len(rows[0]), C * len(rows)
    sheet = Image.new('RGBA', (W, H), (30, 24, 40, 255))
    for r, cells in enumerate(rows):
        for i, f in enumerate(cells):
            sheet.alpha_composite(Image.fromarray(f, 'RGBA'), (i * C, r * C))
    sheet = sheet.resize((W * scale, H * scale), Image.NEAREST)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path)


if __name__ == '__main__':
    keys = [a for a in sys.argv[1:] if not a.startswith('-')] or list(BOSSES)
    if '--preview' in sys.argv:
        preview(keys, os.path.join(PREVIEW, 'bosses.png'))
    else:
        for k in keys:
            out = write(k)
            print(k, len(out), 'clips,', sum(len(a.frames) for a in out.values()), 'frames')
        preview(list(BOSSES), os.path.join(PREVIEW, 'bosses.png'))
