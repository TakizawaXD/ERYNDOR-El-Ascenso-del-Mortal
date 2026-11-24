"""EL REY SEPULTADO - the boss of the Catacombs, drawn from scratch with the boss painter (bossart.py / bosses.py).

  python Tools/CharAnim/king.py            -> Assets/Art/Characters/BossReySepultado/      (armour whole: phases 1-2)
                                           -> Assets/Art/Characters/BossReySepultadoRoto/  (armour broken: phase 3)
                                           -> Documentation/CharacterPreviews/rey_sepultado.png

An undead king in deteriorated black-and-gold plate, a broken crown, violet eyes, a tattered royal cape and a cursed
greatsword with violet runes; dark energy leaks from the cracks. 128x128 cells, feet on row 112 (pivot 0.5, 16/128),
uniform grid, 4 directions (Left mirrors Right). Animations:
  Idle Walk Run Attack (horizontal sweep) AttackVertical AttackDiagonal HeavyAttack SwordSlam Dash Summon
  Hurt Stagger PhaseTransition Death   (+ SpecialAttack / CastSpell / Knockback copies for the standard animator)
"""
import json, math, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from bossart import *                                   # noqa
from bosses import P, limb, local, dark, Boss, Anim, G, OUT, PREVIEW   # noqa

VIO = [hx('#ffffff'), hx('#e6ccff'), hx('#b77cff'), hx('#7a3ad8'), hx('#431a86')]


class King(Boss):
    key = 'BossReySepultado'
    arm0, off0 = 24, 18
    broken = False
    PLATE = ramp('#06060a', '#0f0e15', '#1b1a24', '#2b2936', '#423f50', '#5e5a6e')
    GOLD = ramp('#2a1806', '#5a3a10', '#8c6420', '#bc9238', '#e2c066', '#fff0b0')
    CAPE = ramp('#08040e', '#160a24', '#26123c', '#381c52', '#4c2a68')
    BONE = ramp('#3c3226', '#6e624e', '#a49882', '#d0c6b0', '#efe8d6')
    STEEL = ramp('#0c0c12', '#24232e', '#3e3c4c', '#63607a', '#9a96b0', '#d4d0e6')
    EYE = hx('#f2dcff')
    slash = [hx('#ffffff'), hx('#e6ccff'), hx('#b77cff'), hx('#6a2ccc')]
    ember = hx('#c890ff')
    flash = hx('#ffffff')

    def frame(self, v, d):
        p = P(d, self)
        p.two = d.get('two', 0); p.crack = d.get('crack', 0); p.sword_up = d.get('sword_up', 0)
        c = Canvas()
        self.draw(c, v, p)
        f = c.finish()
        if p.lean:
            top = f.copy(); top[FEET - 34:] = 0
            f[:FEET - 34] = 0
            f = over(f, shift(top, p.lean if v != 'U' else 0, 0 if v == 'R' else abs(p.lean) // 2 * (1 if v == 'D' else -1)))
        return f

    # ------------------------------------------------------------ parts
    def cape(self, c, v, p, b):
        flare = p.wing
        rag = lambda x0, x1, y: [(x, y + (3 if (i % 2) else 0) + ((p.t + i) % 3) - (4 if self.broken and i % 3 == 0 else 0))
                                 for i, x in enumerate(np.linspace(x1, x0, 9))]
        if v == 'D':
            for s in (-1, 1):
                x0 = 64 + s * 16
                pts = [(x0, 58 + b), (x0 + s * (8 + flare * 3), 72 + b), (x0 + s * (10 + flare * 4), 100 + b)] + \
                      [(x0 + s * (10 + flare * 4) - s * 4, 106 + b), (x0 + s * 2, 102 + b)]
                c.part(Mask().poly(pts), self.CAPE)
        elif v == 'U':
            pts = [(46, 56 + b), (82, 56 + b), (86 + flare * 3, 80 + b), (88 + flare * 4, 104 + b)] + rag(40 - flare * 4, 88 + flare * 4, 104 + b) + [(40 - flare * 4, 104 + b), (42 - flare * 3, 80 + b)]
            c.part(Mask().poly(pts), self.CAPE)
            c.part(Mask().line([(52, 60 + b), (50, 100 + b)], 1).line([(64, 60 + b), (64, 104 + b)], 1).line([(76, 60 + b), (78, 100 + b)], 1), dark(self.CAPE, 1), seam=False)
            if not self.broken:
                c.part(Mask().poly([(58, 70 + b), (70, 70 + b), (64, 82 + b)]), self.GOLD, seam=False)    # the royal crest on the back
        else:
            pts = [(60, 56 + b), (66, 58 + b), (58 - flare * 6, 80 + b), (48 - flare * 8, 104 + b)] + \
                  [(48 - flare * 8 + i * 3, 104 + b + (3 if i % 2 else 0)) for i in range(1, 5)] + [(62, 96 + b)]
            c.part(Mask().poly(pts), dark(self.CAPE))

    def legs(self, c, p, xs=(56, 72), dk=False):
        P_ = dark(self.PLATE) if dk else self.PLATE
        G_ = dark(self.GOLD) if dk else self.GOLD
        for i, x in enumerate(xs):
            lift = p.step if i == 0 else -p.step
            fy = G - max(0, lift) * 3 + p.kneel
            s = -1 if i == 0 else 1
            hy = 86 + p.bob
            c.part(Mask().poly([(x - 6, hy), (x + 6, hy), (x + s * 2 + 5, 98 + p.bob), (x + s * 2 - 5, 98 + p.bob)]), P_)
            c.part(Mask().ell(x + s * 2, 98 + p.bob, 4, 3), G_, seam=False)                             # knee cop
            c.part(Mask().poly([(x + s * 2 - 5, 99 + p.bob), (x + s * 2 + 5, 99 + p.bob), (x + 4, fy - 4), (x - 4, fy - 4)]), P_)
            c.part(Mask().poly([(x - 5, fy - 5), (x + 5, fy - 5), (x + 7, fy), (x - 6, fy)]), P_)
            c.part(Mask().line([(x - 5, fy - 5), (x + 5, fy - 5)]), G_, seam=False)
            if self.broken and i == 0:
                c.part(Mask().line([(x - 1, 100 + p.bob), (x + 1, fy - 6)], 2), self.BONE, seam=False)   # shin bone through the plate

    def crown(self, c, cx, cy, side=False):
        m = Mask().rect(cx - 8 if not side else cx - 6, cy, cx + 8 if not side else cx + 6, cy + 3)
        c.part(m, self.GOLD)
        spikes = (-7, -3.5, 0, 3.5, 7) if not side else (-5, -1, 3, 6)
        for i, dx in enumerate(spikes):
            h = (7, 4, 9, 2, 6)[i % 5] if not side else (5, 7, 2, 5)[i]
            if self.broken and i in (1, 3): h = 1                                    # snapped spikes
            if h <= 1: continue
            c.part(Mask().poly([(cx + dx - 1.5, cy), (cx + dx + 1.5, cy), (cx + dx + (0.5 if i % 2 else -0.5), cy - h)]), self.GOLD, seam=False)
        c.pixels([(cx + 1, cy + 1), (cx + 2, cy + 2), (cx + 2, cy + 3)], hx('#1a0c06'))                 # the crack
        c.emit(Mask().rect(cx - 1, cy + 1, cx, cy + 2), VIO[1], VIO[2], halo=(180, 120, 255, 120), radius=1)

    def head(self, c, v, p, b):
        if v == 'D':
            c.part(Mask().ell(64, 48 + b, 8, 9).poly([(57, 50 + b), (71, 50 + b), (68, 58 + b), (60, 58 + b)]), self.PLATE)
            # skull faceplate: the visor is gone, the king's skull shows
            c.part(Mask().ell(64, 51 + b, 5, 5).rect(61, 53 + b, 67, 57 + b), self.BONE, seam=False)
            c.flat(Mask().rect(60, 49 + b, 62, 51 + b).rect(66, 49 + b, 68, 51 + b), hx('#05030a'))
            eye = VIO[0] if p.glow else self.EYE
            c.emit(Mask().rect(61, 50 + b, 61, 50 + b).rect(67, 50 + b, 67, 50 + b), eye, None, halo=(170, 100, 255, 190), radius=2)
            c.pixels([(62, 56 + b), (64, 56 + b), (66, 56 + b)], hx('#120c10'))
            c.part(Mask().poly([(56, 44 + b), (58, 40 + b), (60, 44 + b)]).poly([(68, 44 + b), (70, 40 + b), (72, 44 + b)]), self.PLATE, seam=False)
            self.crown(c, 64, 37 + b)
            if self.broken:
                c.pixels([(58, 46 + b), (59, 47 + b), (59, 48 + b), (60, 49 + b)], hx('#05030a'))
        elif v == 'U':
            c.part(Mask().ell(64, 48 + b, 8, 9), self.PLATE)
            c.part(Mask().line([(58, 52 + b), (70, 52 + b)]), self.GOLD, seam=False)
            self.crown(c, 64, 37 + b)
        else:
            c.part(Mask().ell(66, 48 + b, 7, 9).poly([(63, 52 + b), (73, 52 + b), (71, 58 + b)]), dark(self.PLATE, 0))
            c.part(Mask().ell(69, 51 + b, 4, 5), self.BONE, seam=False)
            c.flat(Mask().rect(70, 49 + b, 72, 51 + b), hx('#05030a'))
            c.emit(Mask().rect(71, 50 + b, 71, 50 + b), VIO[0] if p.glow else self.EYE, None, halo=(170, 100, 255, 190), radius=2)
            self.crown(c, 65, 37 + b, side=True)

    def torso(self, c, v, p, b):
        if v in ('D', 'U'):
            t = Mask().poly([(46, 57 + b), (82, 57 + b), (79, 72 + b), (73, 87 + b), (55, 87 + b), (49, 72 + b)])
            c.part(t, self.PLATE)
            if v == 'D':
                if self.broken:
                    # the left half of the breastplate is gone: ribs and the cursed heart show
                    c.flat(Mask().poly([(50, 60 + b), (64, 60 + b), (64, 84 + b), (56, 84 + b), (51, 72 + b)]), hx('#0a0612'))
                    for ry in range(63, 82, 4):
                        c.part(Mask().line([(52, ry + b), (63, ry + 1 + b)], 2), self.BONE, seam=False)
                    c.part(Mask().line([(64, 60 + b), (64, 85 + b)], 2), self.BONE, seam=False)
                    c.emit(Mask().ell(59, 70 + b, 3, 3), VIO[1], VIO[2], halo=(170, 90, 255, 200), radius=3)
                else:
                    c.part(Mask().poly([(60, 60 + b), (68, 60 + b), (66, 80 + b), (62, 80 + b)]), self.GOLD, seam=False)   # gold filigree
                    c.part(Mask().line([(50, 64 + b), (58, 70 + b)]).line([(78, 64 + b), (70, 70 + b)]), self.GOLD[:4], seam=False)
                    if p.crack:
                        cr = Mask().line([(70, 62 + b), (73, 68 + b), (70, 74 + b), (74, 80 + b)])
                        if p.crack > 1: cr.line([(56, 62 + b), (53, 69 + b), (57, 76 + b)])
                        c.emit(cr, VIO[1], VIO[2], halo=(170, 90, 255, 150), radius=1)
            c.part(Mask().rect(53, 84 + b, 75, 88 + b), self.GOLD)
            c.part(Mask().poly([(54, 88 + b), (74, 88 + b), (77, 99 + b), (70, 96 + b), (64, 100 + b), (58, 96 + b), (51, 99 + b)]), self.PLATE)
            c.part(Mask().line([(54, 89 + b), (74, 89 + b)]), self.GOLD[:4], seam=False)
        else:
            c.part(Mask().poly([(54, 57 + b), (75, 57 + b), (75, 72 + b), (71, 87 + b), (58, 87 + b), (54, 72 + b)]), self.PLATE)
            if not self.broken:
                c.part(Mask().line([(73, 60 + b), (72, 80 + b)], 2), self.GOLD[:5], seam=False)
            else:
                c.flat(Mask().poly([(66, 62 + b), (75, 62 + b), (74, 78 + b), (67, 78 + b)]), hx('#0a0612'))
                for ry in range(64, 78, 4): c.part(Mask().line([(67, ry + b), (74, ry + b)]), self.BONE, seam=False)
                c.emit(Mask().ell(70, 70 + b, 2, 2), VIO[1], VIO[2], halo=(170, 90, 255, 200), radius=2)
            if p.crack and not self.broken:
                c.emit(Mask().line([(64, 62 + b), (67, 70 + b), (63, 78 + b)]), VIO[1], VIO[2], halo=(170, 90, 255, 140), radius=1)
            c.part(Mask().rect(56, 84 + b, 73, 88 + b), self.GOLD)
            c.part(Mask().poly([(56, 88 + b), (73, 88 + b), (75, 99 + b), (55, 99 + b)]), self.PLATE)

    def pauldron(self, c, x, y, s, gone=False):
        if gone:
            c.part(Mask().ell(x, y, 4, 3), self.BONE)
            return
        c.part(Mask().ell(x, y, 9, 7), self.PLATE)
        c.part(Mask().ell(x, y + 3, 9, 4), self.PLATE)
        c.part(Mask().line([(x - 8, y + 4), (x + 8, y + 4)]), self.GOLD, seam=False)
        c.part(Mask().poly([(x + s * 3 - 2, y - 5), (x + s * 3 + 2, y - 5), (x + s * 7, y - 13)]), self.GOLD, seam=False)

    def sword(self, c, hand, d, glow, length=50):
        c.part(Mask().poly(local(hand, d, [(-8, -2), (2, -2), (2, 2), (-8, 2)])), self.PLATE)                 # grip
        c.part(Mask().ell(*local(hand, d, [(-10, 0)])[0], 3, 3), self.BONE)                                     # skull pommel
        c.part(Mask().poly(local(hand, d, [(2, -9), (6, -9), (6, 9), (2, 9)])), self.GOLD)                     # crossguard
        c.part(Mask().poly(local(hand, d, [(6, -4.5), (length - 6, -3.5), (length, 0), (length - 6, 3.5), (6, 4.5)])), self.STEEL)
        c.part(Mask().poly(local(hand, d, [(length - 14, -3.5), (length - 10, -5.5), (length - 9, -3)])), self.STEEL, seam=False)  # a notch
        rune = Mask().line(local(hand, d, [(10, 0), (length - 10, 0)]), 1)
        c.emit(rune, VIO[1] if glow else VIO[2], VIO[3], halo=(160, 90, 255, 150) if glow else None, radius=2 if glow else 1)

    def arm_rmp(self, gone=False):
        return self.BONE if gone else self.PLATE

    def aura(self, c, v, p, b):
        if not (p.glow or self.broken):
            return
        n = 6 + 4 * p.glow + (6 if self.broken else 0)
        for i in range(n):
            a = (i * 2.399 + p.t * 0.7)
            r = 26 + (i % 4) * 4
            x = 64 + math.cos(a) * r * 0.8
            y = 74 + b + math.sin(a) * r * 0.9
            c.emit(Mask().px(x, y).px(x, y - 1), VIO[1 + (i % 3)], None)

    # ------------------------------------------------------------ figure
    def draw(self, c, v, p):
        b = p.bob + p.kneel
        if v in ('D', 'U'):
            front = v == 'D'
            ms = 1 if front else -1
            if front: self.cape(c, v, p, b)
            self.legs(c, p)
            self.torso(c, v, p, b)
            if not front: self.cape(c, v, p, b)
            self.head(c, v, p, b)
            gone_l = self.broken
            self.pauldron(c, 64 - 19, 58 + b, -1, gone=gone_l and front)
            self.pauldron(c, 64 + 19, 58 + b, 1, gone=gone_l and not front)
            sw_sh = (82 if front else 46, 63 + b)
            of_sh = (46 if front else 82, 63 + b)
            if p.two:
                # both hands on the hilt: the off arm reaches across to the sword hand
                hand, d = limb(c, sw_sh, p.arm, ms, 17, 8, 7, self.PLATE, self.GOLD, 3)
                limb(c, of_sh, p.arm if p.arm < 150 else 175, -ms if p.arm < 150 else ms, 17 if p.arm < 150 else 16, 7, 6,
                     self.arm_rmp(gone_l and front), self.GOLD, 3)
            else:
                limb(c, of_sh, p.off, -ms, 16, 7, 6, self.arm_rmp(gone_l and front), self.GOLD, 3)
                hand, d = limb(c, sw_sh, p.arm, ms, 17, 8, 7, self.PLATE, self.GOLD, 3)
            self.sword(c, hand, d, p.glow or p.arm > 120)
        else:
            self.cape(c, v, p, b)
            limb(c, (61, 63 + b), p.off, -1, 15, 6, 6, dark(self.arm_rmp(self.broken)), dark(self.GOLD), 3)
            self.legs(c, p, xs=(60, 68), dk=False)
            self.torso(c, v, p, b)
            self.head(c, v, p, b)
            self.pauldron(c, 66, 58 + b, 1)
            hand, d = limb(c, (67, 63 + b), p.arm, 1, 17, 8, 7, self.PLATE, self.GOLD, 3)
            self.sword(c, hand, d, p.glow or p.arm > 120)
        self.aura(c, v, p, b)


class KingBroken(King):
    key = 'BossReySepultadoRoto'
    broken = True
    PLATE = ramp('#07060b', '#121019', '#201d2a', '#302c3c', '#463f55', '#5e566e')
    CAPE = ramp('#06030c', '#12081e', '#200e34', '#2e1646', '#40205a')


# ======================================================================== effects
def layer_rot(fx, ang, cx=64, cy=72):
    im = Image.fromarray(fx, 'RGBA').rotate(ang, resample=Image.NEAREST, center=(cx, cy))
    return np.array(im)


def blank():
    return np.zeros((C, C, 4), np.uint8)


def sweep(f, v, king, kind, fade=False, big=False):
    """slash trails: horizontal sweep, vertical chop, diagonal cut"""
    cols = king.slash
    fx = blank()
    if v == 'R':
        cx, cy = 74, G - 34
    elif v == 'U':
        cx, cy = 64, 54
    else:
        cx, cy = 64, G - 18
    r = 34 if big else 28
    if kind == 'h':
        fx = arc(fx, cx, cy, r, r - (8 if big else 6), 200 if v != 'U' else 20, 340 if v != 'U' else 160, cols, ry=0.42, fade=fade) if v != 'R' else \
            arc(fx, cx, cy, r, r - 6, 300, 60, cols, ry=0.5, fade=fade)
    elif kind == 'v':
        fx = arc(fx, cx + (12 if v == 'R' else 0), cy - 6, r, r - 6, 250, 110, cols, ry=1.5, fade=fade) if v != 'R' else \
            arc(fx, cx, cy, r, r - 6, 250, 100, cols, ry=1.0, fade=fade)
    else:
        fx = arc(fx, cx, cy, r, r - 6, 210, 30, cols, ry=0.7, fade=fade)
        fx = layer_rot(fx, -35 if v != 'U' else 35, cx, cy)
    return over(f, fx)


def ghost(f, k=0.45, dx=-10):
    g = shift(tint(f, (150, 90, 255), 0.7), dx, 0)
    g[:, :, 3] = (g[:, :, 3] * k).astype(np.uint8)
    return over(g, f)


# ======================================================================== animation table
def build(king):
    out = {}
    views = ('D', 'U', 'R')
    name = {'D': 'Down', 'U': 'Up', 'R': 'Right'}

    def add(anim, cat, fps, loop, poses, post=None, alias=()):
        for v in views:
            frames = []
            for i, pd in enumerate(poses):
                f = king.frame(v, pd)
                if post: f = post(f, v, i)
                frames.append(f)
            for nm in (anim,) + tuple(alias):
                out[(nm, name[v])] = Anim(cat, frames, fps, loop)
                if v == 'R':
                    out[(nm, 'Left')] = Anim(cat, [np.ascontiguousarray(fr[:, ::-1]) for fr in frames], fps, loop)

    a0, o0 = king.arm0, king.off0
    g = 1 if king.broken else 0
    add('Idle', 'Idle', 5, True, [dict(t=0, glow=g), dict(t=1, bob=-1, glow=g), dict(t=2, bob=-1, glow=1), dict(t=3, glow=g)])
    add('Walk', 'Walk', 7, True, [dict(t=i, step=s, bob=bb, arm=a0 + s * 5, off=o0 - s * 6, wing=abs(s), glow=g)
                                  for i, (s, bb) in enumerate(((1, 0), (1, -1), (0, -1), (-1, 0), (-1, -1), (0, -1)))])
    add('Run', 'Run', 11, True, [dict(t=i, step=s * 2, bob=bb, arm=62, off=40 + s * 10, wing=2, lean=2, glow=g)
                                 for i, (s, bb) in enumerate(((1, 0), (1, -2), (0, -1), (-1, 0), (-1, -2), (0, -1)))])

    def post_h(f, v, i):
        return sweep(f, v, king, 'h') if i == 2 else sweep(f, v, king, 'h', fade=True) if i == 3 else f
    add('Attack', 'Attack', 11, False, [dict(arm=125, off=30, t=0, squash=1), dict(arm=105, off=40, bob=-1, t=1, wing=1),
                                        dict(arm=70, off=20, bob=1, t=2, lean=3, glow=1), dict(arm=45, t=3, lean=2), dict(t=0)], post_h)

    def post_v(f, v, i):
        return sweep(f, v, king, 'v') if i == 2 else sweep(f, v, king, 'v', fade=True) if i == 3 else f
    add('AttackVertical', 'Attack', 10, False, [dict(arm=150, two=1, t=0), dict(arm=178, two=1, bob=-2, t=1, glow=1, wing=1),
                                                dict(arm=35, two=1, bob=2, t=2, lean=2, squash=-1), dict(arm=20, two=1, bob=1, t=3), dict(t=0)], post_v)

    def post_d(f, v, i):
        return sweep(f, v, king, 'd') if i == 2 else sweep(f, v, king, 'd', fade=True) if i == 3 else f
    add('AttackDiagonal', 'Attack', 11, False, [dict(arm=160, off=60, t=0), dict(arm=170, off=80, bob=-1, t=1, wing=1),
                                                dict(arm=50, off=20, bob=1, t=2, lean=3, glow=1), dict(arm=30, t=3, lean=1), dict(t=0)], post_d,
        alias=('SpecialAttack',))

    def post_heavy(f, v, i):
        if i == 3: return sweep(f, v, king, 'h', big=True)
        if i == 4: return sparks(sweep(f, v, king, 'h', fade=True, big=True), 64, G - 10, 16, 30, king.slash[:3], seed=i)
        if i in (1, 2): return sparks(f, 64, 60, 6 + i * 4, 24, VIO[1:4], seed=i)
        return f
    add('HeavyAttack', 'Attack', 9, False, [dict(arm=110, off=70, squash=2, t=0), dict(arm=165, off=140, two=1, bob=-3, t=1, glow=1, wing=2),
                                            dict(arm=172, off=160, two=1, bob=-4, t=2, glow=2, wing=2), dict(arm=60, two=1, bob=2, t=3, lean=3, squash=-2, glow=1),
                                            dict(arm=30, off=20, bob=1, t=0), dict(t=1)], post_heavy)

    def post_slam(f, v, i):
        if i == 4:
            f = ring(f, 64, G, 20, VIO[1], w=2)
            return sparks(f, 64, G - 4, 18, 26, VIO[0:3], seed=4)
        if i == 5:
            f = ring(f, 64, G, 30, VIO[2], w=2)
            return ring(f, 64, G, 40, VIO[3], w=1)
        if i in (1, 2, 3): return sparks(f, 64, 44, 6 * i, 18, VIO[1:4], seed=i)
        return f
    add('SwordSlam', 'Special', 9, False, [dict(arm=120, two=1, t=0), dict(arm=172, two=1, bob=-2, t=1, glow=1, wing=1),
                                           dict(arm=178, two=1, bob=-4, t=2, glow=2, wing=2), dict(arm=178, two=1, bob=-4, t=3, glow=2, wing=2),
                                           dict(arm=8, two=1, kneel=3, squash=-2, t=0, glow=2), dict(arm=8, two=1, kneel=3, t=1, glow=1),
                                           dict(arm=20, two=1, kneel=1, t=2)], post_slam)

    def post_dash(f, v, i):
        if i in (1, 2): return ghost(ghost(f, 0.35, -16 if v == 'R' else 0), 0.5, -8 if v == 'R' else 0) if v == 'R' else ghost(f, 0.4, 0)
        return f
    add('Dash', 'Special', 12, False, [dict(arm=70, off=50, lean=2, squash=1, t=0), dict(arm=80, off=60, lean=5, step=2, wing=3, t=1, glow=1),
                                       dict(arm=80, off=60, lean=5, step=-2, wing=3, t=2, glow=1), dict(arm=40, lean=1, t=3)], post_dash)

    def post_summon(f, v, i):
        if i >= 2:
            f = ring(f, 64, G, 14 + i * 5, VIO[2 if i % 2 else 1], w=1)
            return sparks(f, 64, 40 - i * 2, 6 + i * 3, 20, VIO[0:3], seed=i)
        return f
    add('Summon', 'Special', 8, False, [dict(arm=120, two=1, t=0), dict(arm=178, two=1, bob=-1, t=1, glow=1),
                                        dict(arm=178, two=1, bob=-2, t=2, glow=2, wing=2), dict(arm=178, two=1, bob=-2, t=3, glow=2, wing=2),
                                        dict(arm=178, two=1, bob=-2, t=0, glow=2, wing=1), dict(arm=140, two=1, bob=-1, t=1, glow=1)], post_summon,
        alias=('CastSpell',))

    def post_hurt(f, v, i):
        if i == 0: return tint(f, king.flash, .75)
        if i == 1: return tint(shift(f, 0, 1), (160, 60, 255), .35)
        return f
    add('Hurt', 'Hurt', 12, False, [dict(t=0, glow=g), dict(t=0, squash=1, lean=-1), dict(t=0, glow=g)], post_hurt)

    def post_stagger(f, v, i):
        if i == 0: return tint(f, king.flash, .6)
        if i in (1, 2, 3): return sparks(f, 52 + i * 6, 40, 3, 6, [hx('#fff3a0'), hx('#ffffff')], seed=i)    # stars
        return f
    add('Stagger', 'Hurt', 8, False, [dict(t=0, lean=-2, arm=10, off=60), dict(t=1, lean=-3, kneel=1, arm=8, off=90, squash=1),
                                      dict(t=2, lean=-1, kneel=2, arm=6, off=40), dict(t=3, lean=1, kneel=2, arm=6, off=30),
                                      dict(t=0, kneel=1, arm=14)], post_stagger, alias=('Knockback',))

    def post_phase(f, v, i):
        if i >= 5:
            f = ring(f, 64, G, 18 + (i - 5) * 12, VIO[1], w=2)
            f = sparks(f, 64, 70, 20, 34, VIO[0:3], seed=i)
        if i == 7:
            f = tint(f, VIO[1], 0.35)
        return f
    add('PhaseTransition', 'Special', 7, False, [dict(t=0, arm=20, glow=1), dict(t=1, kneel=2, arm=10, off=10, glow=1, crack=1),
                                                 dict(t=2, kneel=4, arm=6, off=6, squash=1, glow=2, crack=1), dict(t=3, kneel=5, arm=6, off=6, squash=2, glow=2, crack=2),
                                                 dict(t=0, kneel=5, arm=6, off=6, squash=2, glow=2, crack=2), dict(t=1, kneel=2, arm=120, off=120, two=1, glow=2, crack=2, wing=2),
                                                 dict(t=2, bob=-2, arm=176, two=1, glow=2, crack=2, wing=3), dict(t=3, bob=-1, arm=150, two=1, glow=2, crack=2, wing=2)], post_phase)

    def post_death(f, v, i):
        if i == 0: return tint(f, king.flash, .8)
        if i >= 2: return dissolve(f, (i - 1) / 6.0, king.ember, seed=7)
        return f
    add('Death', 'Death', 7, False, [dict(t=0, squash=1, glow=1), dict(t=1, kneel=3, arm=10, off=10, squash=2), dict(t=2, kneel=5, arm=5, off=5, squash=3)]
        + [dict(t=i, kneel=6, arm=5, off=5, squash=3) for i in range(3, 8)], post_death)
    return out


def write(king):
    out = build(king)
    root = os.path.join(OUT, king.key)
    clips = []
    for (anim, d), a in sorted(out.items()):
        rel = f'{a.cat}/{king.key}_{anim}_{d}.png'
        save_sheet(a.frames, os.path.join(root, rel))
        clips.append(dict(name=anim, dir=d, file=rel, frames=len(a.frames), seq=list(range(len(a.frames))), fps=a.fps,
                          loop=a.loop, size=[C * len(a.frames), C]))
    with open(os.path.join(root, f'{king.key}_animations.json'), 'w') as fh:
        json.dump(dict(character=king.key, cell=C, pivot=[0.5, (C - FEET) / C], ppu=16, clips=clips), fh, indent=1)
    return out


def preview(sets, path, scale=2):
    rows = []
    for out in sets:
        rows.append([out[('Idle', 'Down')].frames[0], out[('Idle', 'Up')].frames[0], out[('Idle', 'Right')].frames[0],
                     out[('Attack', 'Down')].frames[2], out[('AttackVertical', 'Right')].frames[2], out[('AttackDiagonal', 'Down')].frames[2],
                     out[('SwordSlam', 'Down')].frames[4], out[('Dash', 'Right')].frames[1], out[('Summon', 'Down')].frames[3],
                     out[('Stagger', 'Down')].frames[2], out[('PhaseTransition', 'Down')].frames[5], out[('Death', 'Down')].frames[4]])
    W, H = C * len(rows[0]), C * len(rows)
    sheet = Image.new('RGBA', (W, H), (34, 28, 40, 255))
    for r, cells in enumerate(rows):
        for i, f in enumerate(cells):
            sheet.alpha_composite(Image.fromarray(f, 'RGBA'), (i * C, r * C))
    sheet = sheet.resize((W * scale, H * scale), Image.NEAREST)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path)


if __name__ == '__main__':
    sets = []
    for k in (King(), KingBroken()):
        out = write(k)
        sets.append(out)
        print(k.key, len(set(a for a, _ in out)), 'animations,', len(out), 'clips,', sum(len(a.frames) for a in out.values()), 'frames')
    preview(sets, os.path.join(PREVIEW, 'rey_sepultado.png'))
