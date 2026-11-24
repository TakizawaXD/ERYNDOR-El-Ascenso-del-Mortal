"""Player weapon sets: one full animation set per weapon type for the knight classes.

  python weaponsets.py [kind ...]      -> Assets/Art/Characters/WeaponSets/<Class>/<Kind>/<Cat>/<Class>_<Kind>_<Anim>_<Dir>.png
                                          + <Class>_<Kind>_animations.json   (Soldier, then the class recolours)

How a frame is made (integrated sheet, one SpriteRenderer in Unity):
  body pose  -> the Soldier's ORIGINAL side frames with the pack's sword stripped out (Idle, Walk, Attack01/02 arm poses,
                Hurt, Death) or the hand-drawn front/back rig of designs.py with the weapon arm raised/lowered
  weapon     -> weaponart.pose(): the weapon drawing turned around its grip, put in the hand of that pose
  fist       -> drawn over the grip, so the hand visibly holds it
  smear/FX   -> blade trail, thrust lines, dust rings, sparks, orbs, runes (same colours as the original slashes)
Only the weapon layer is turned; the body is never rotated.

The choreography of every move is written once in SIDE terms (angle 0 = up, 90 = forward) and mapped to the three drawn
views (Right, Down, Up); Left is the mirror of Right. Each clip also exports animation events (HitOn / HitOff /
Projectile / ComboWindow / Step / End) that Unity turns into Animation Events.
"""
import json, math, os, sys
import numpy as np
from PIL import Image
from engine import *
import fxdraw as X
import weaponart as WA
from source import Source
from rigs import RIGS

SETS_ROOT = os.path.join(OUT, 'WeaponSets')
SOLDIER_HAND = (hx('#607581'), hx('#425c6b'))
STRIP = [hx(c)[:3] for c in ('#e8f1f4', '#c9d5d9', '#a9c1c9', '#8fa1ae', '#805121', '#22021d', '#fff0ef', '#5e1e13',
                             '#f4edea', '#d9d8d8', '#c0bfbf')]


# =============================================================== body poses
_BODY_PAL = None


def body_palette():
    """every colour the Soldier's body uses in its weaponless original frames (Idle, Walk, Hurt, Death)"""
    global _BODY_PAL
    if _BODY_PAL is None:
        s = Source('Soldier')
        cols = set()
        for an in ('Idle', 'Walk', 'Hurt', 'Death'):
            for f in s.anims[an]:
                for px_ in f[f[:, :, 3] > 0]:
                    cols.add(tuple(int(v) for v in px_[:3]))
        _BODY_PAL = cols
    return _BODY_PAL


def strip_weapon(f):
    """remove the pack's sword / bow / slash / dust pixels and the black outline left orphaned around them"""
    g = f.copy()
    rgb = g[:, :, :3]
    pal = body_palette()
    m = np.zeros(g.shape[:2], bool)
    for y, x in zip(*np.nonzero(g[:, :, 3])):
        if tuple(int(v) for v in rgb[y, x]) not in pal:
            m[y, x] = True
    for c in STRIP:
        m |= np.all(rgb == c, axis=2)
    # pure white: the eye is one or two pixels, slashes are large blobs
    from scipy import ndimage
    white = np.all(rgb == (255, 255, 255), axis=2) & (g[:, :, 3] > 0)
    lab, n = ndimage.label(white)
    for k in range(1, n + 1):
        if (lab == k).sum() > 3:
            m |= lab == k
    m &= g[:, :, 3] > 0
    g[m] = 0
    black = np.all(g[:, :, :3] == 0, axis=2) & (g[:, :, 3] > 0)
    colored = (g[:, :, 3] > 0) & ~black
    for _ in range(2):
        nb = np.zeros_like(colored)
        nb[1:] |= colored[:-1]; nb[:-1] |= colored[1:]; nb[:, 1:] |= colored[:, :-1]; nb[:, :-1] |= colored[:, 1:]
        orphan = black & ~nb
        g[orphan] = 0
        black &= ~orphan
    return g


class Pose:
    """a body frame plus the position of the weapon hand (and the off hand)"""
    def __init__(self, body, grip, off=None):
        self.body, self.grip, self.off = body, grip, off

    def copy(self):
        return Pose(self.body.copy(), self.grip, self.off)


def _move(p, dx, dy):
    return (p[0] + dx, p[1] + dy) if p else p


def t_shift(P, dx, dy):
    return Pose(shift(P.body, dx, dy), _move(P.grip, dx, dy), _move(P.off, dx, dy))


def t_lean(P, px):
    b = bbox(P.body)
    split = b[1] + (b[3] - b[1]) // 2
    g = _move(P.grip, px, 0) if P.grip[1] < split else P.grip
    o = (_move(P.off, px, 0) if P.off[1] < split else P.off) if P.off else None
    return Pose(lean(P.body, px), g, o)


def t_squash(P, rows):
    b = bbox(P.body)
    cut = b[1] + (b[3] - b[1]) * 2 // 3
    g = _move(P.grip, 0, rows) if P.grip[1] < cut else P.grip
    o = (_move(P.off, 0, rows) if P.off[1] < cut else P.off) if P.off else None
    return Pose(squash(P.body, rows), g, o)


def t_stretch(P, rows):
    b = bbox(P.body)
    cut = b[1] + (b[3] - b[1]) * 2 // 3
    g = _move(P.grip, 0, -rows) if P.grip[1] < cut else P.grip
    o = (_move(P.off, 0, -rows) if P.off[1] < cut else P.off) if P.off else None
    return Pose(stretch(P.body, rows), g, o)


class Bodies:
    """every body pose of one character in the three drawn views"""
    SIDE = {                     # name: (original strip, frame, grip, off-hand)
        'idle': ('Idle', 0, (35, 47), (27, 47)),
        'raise': ('Attack01', 1, (38, 42), (28, 45)),
        'raise2': ('Attack01', 2, (39, 43), (28, 45)),
        'mid': ('Attack01', 3, (37, 46), (28, 46)),
        'mid2': ('Attack01', 4, (35, 48), (28, 46)),
        'low': ('Attack01', 5, (31, 50), (27, 47)),
        'hraise': ('Attack02', 1, (38, 40), (29, 44)),
        'hraise2': ('Attack02', 2, (39, 41), (29, 44)),
        'hlow': ('Attack02', 3, (38, 50), (28, 47)),
        'aim': ('Attack03', 4, (41, 45), (34, 44)),
        'aim0': ('Attack03', 2, (38, 44), (33, 44)),
        'hurt': ('Hurt', 1, (34, 47), (27, 47)),
        'hurt2': ('Hurt', 2, (34, 47), (27, 47)),
    }
    # front/back: how far the weapon arm (viewer right) moves up (-) / down (+), grip and off-hand
    VERT = {
        'idle': (0, (37, 47), (26, 47)),
        'raise': (-6, (37, 41), (26, 46)),
        'raise2': (-7, (37, 40), (26, 46)),
        'mid': (-3, (37, 44), (26, 47)),
        'mid2': (-1, (37, 46), (26, 47)),
        'low': (1, (36, 49), (26, 47)),
        'hraise': (-7, (36, 40), (27, 44)),
        'hraise2': (-8, (36, 39), (27, 44)),
        'hlow': (1, (35, 49), (27, 48)),
        'aim': (-3, (34, 44), (28, 44)),
        'aim0': (-2, (36, 45), (27, 45)),
        'hurt': (0, (37, 47), (26, 47)),
        'hurt2': (0, (37, 47), (26, 47)),
    }

    def __init__(self, key='Soldier'):
        self.s = Source(key)
        self.r = RIGS[key]
        self._side = {}
        for n, (an, i, g, o) in self.SIDE.items():
            self._side[n] = Pose(strip_weapon(self.s.body(an, i)), g, o)

    def side(self, name):
        if name.startswith('walk'):
            i = int(name[4:])
            b = strip_weapon(self.s.body('Walk', i))
            bob = (bbox(b)[1] - bbox(self.s.body('Idle', 0))[1])
            sw = (0, 1, 1, 0, 0, -1, -1, 0)[i]
            return Pose(b, (35 + sw, 47 + bob), (27 - sw, 47 + bob))
        if name.startswith('idle') and name != 'idle':
            i = int(name[4:])
            b = strip_weapon(self.s.body('Idle', i))
            bob = (bbox(b)[1] - bbox(self.s.body('Idle', 0))[1])
            return Pose(b, (35, 47 + max(0, bob)), (27, 47 + max(0, bob)))
        if name.startswith('death'):
            i = int(name[5:])
            return Pose(strip_weapon(self.s.body('Death', i)), (35, 49), None)
        return self._side[name].copy()

    def vert(self, view, name, legs='stand', bob=0):
        base = name
        if name.startswith('walk') or name.startswith('idle') and name != 'idle':
            base = 'idle'
        if name.startswith('death'):
            base = 'idle'
        rdy, g, o = self.VERT[base]
        legs_ = legs
        if name.startswith('walk'):
            i = int(name[4:])
            legs_ = ('A', 'A', 'stand', 'B', 'B', 'stand')[i % 6]
            bob = (0, 1, -1, 0, 1, -1)[i % 6] if False else (0, 0, -1, 0, 0, -1)[i % 6]
        body = self._rig(view, legs_, rdy, ldy=(-rdy // 2 if base in ('hraise', 'hraise2', 'aim', 'aim0') else 0))
        body = place(body, dy=bob + self.r.body_dy)
        return Pose(body, _move(g, 0, bob), _move(o, 0, bob))

    def _rig(self, view, legs, rdy, ldy=0):
        """rig sprite with the viewer-right arm block moved by rdy rows and the left one by ldy"""
        r = self.r
        spr = ascii_sprite(r.body_rows(view, legs), r.pal)
        (l0, l1), (r0, r1), (y0, y1) = r.arms
        out = spr.copy()
        for (c0, c1, s) in ((l0, l1, ldy), (r0, r1, rdy)):
            if not s:
                continue
            block = spr[y0:y1, c0:c1].copy()
            out[y0:y1, c0:c1] = np.where(block[:, :, 3:4] > 0, 0, out[y0:y1, c0:c1])
            H = spr.shape[0]
            for yy in range(y1 - y0):
                ny = y0 + yy + s
                if 0 <= ny < H:
                    row = block[yy]
                    m = row[:, 3] > 0
                    out[ny, c0:c1][m] = row[m]
            # keep a sleeve between shoulder and the raised hand so the arm stays attached
            if s < 0:
                for yy in range(y0 + s + (y1 - y0), y0 + (y1 - y0)):
                    if 0 <= yy < H:
                        for xx in range(c0, c1):
                            if out[yy, xx, 3] == 0 and spr[y0, xx, 3] > 0:
                                out[yy, xx] = spr[y0, xx]
        return out


# =============================================================== choreography
def K(pose, a=None, **kw):
    kw['pose'] = pose; kw['a'] = a
    return kw


def map_angle(a, view):
    """side angle (0 up, 90 forward, 180 down, negative = back) -> drawn angle in the view"""
    if a is None:
        return None
    if view == 'Right':
        return a
    s = -1 if a < 0 else 1
    m = abs(a)
    v = 2 * m if m <= 90 else 180 + (m - 90) * 0.5
    v *= s
    return v if view == 'Down' else 180 - v


def behind_for(view, a_view, kf):
    if 'behind' in kf:
        b = kf['behind']
        return b if isinstance(b, bool) else b.get(view, False)
    if a_view is None:
        return False
    v = ((a_view + 180) % 360) - 180          # -180..180, 0 = up
    if view == 'Right':
        return v < -75                         # pointing back (over the shoulder) goes behind the body
    return abs(v) < 80                         # front/back views: blades pointing up are behind the head/back


class Kind:
    """visual + timing description of one weapon type"""
    def __init__(self, key, weapon, rest, trail=WA.WHITE_TRAIL, two_hand=False, off_weapon=None, flipx=False, scale=1.0,
                 glow=None, fps=12, rest_v=25):
        self.key, self.weapon, self.rest, self.trail, self.two_hand = key, weapon, rest, trail, two_hand
        self.rest_v = rest_v
        self.off_weapon, self.flipx, self.scale, self.glow, self.fps = off_weapon, flipx, scale, glow, fps


KINDS = {
    'Sword': Kind('Sword', 'sword', 60),
    'Greatsword': Kind('Greatsword', 'greatsword', 30, two_hand=True, fps=10),
    'Katana': Kind('Katana', 'katana', 60, flipx=True, fps=14),
    'Rapier': Kind('Rapier', 'rapier', 70, fps=14),
    'Dagger': Kind('Dagger', 'dagger', 100, off_weapon='dagger', fps=15, rest_v=120),
    'Spear': Kind('Spear', 'spear', 30, two_hand=True, fps=12, rest_v=10),
    'Axe': Kind('Axe', 'axe', 50, fps=11),
    'HeavyAxe': Kind('HeavyAxe', 'heavyaxe', 20, two_hand=True, fps=9, rest_v=15),
    'Hammer': Kind('Hammer', 'hammer', 20, two_hand=True, fps=9, rest_v=15),
    'Staff': Kind('Staff', 'staff', 10, fps=11, glow=X.YEL, rest_v=5),
    'Legendary': Kind('Legendary', 'legendary', 60, trail=WA.GLOW_TRAIL, fps=13, glow=hx('#64c8f8')),
}
BOWS = {
    'Bow': 'bow', 'Longbow': 'longbow', 'Crossbow': 'crossbow',
}


def moves(k):
    """{clip: (keyframes, fps, loop)} for weapon kind k (side terms)"""
    R = k.rest
    W = k.key
    T = k.trail
    f = k.fps
    M = {}
    # ------------------------------------------------ locomotion and states (weapon carried at its rest angle)
    M['Idle'] = ([K('idle', R), K('idle1', R), K('idle2', R), K('idle1', R)], 6, True)
    M['Walk'] = ([K(f'walk{i}', R + (0, 4, 6, 4, 0, -4, -6, -4)[i]) for i in range(8)], 10, True)
    M['Run'] = ([K(f'walk{i}', R - 25 + (0, 6, 10, 6, 0, -6, -10, -6)[i], lean=1, lift=(0, 1, 2, 1, 0, 1, 2, 1)[i],
                   fx=['dust'] if i in (0, 4) else []) for i in range(8)], 14, True)
    M['Hurt'] = ([K('hurt', R + 20, flash=1), K('hurt2', R + 30, lunge=-1), K('idle', R)], 10, False)
    M['Knockback'] = ([K('hurt', R + 30, flash=1, lunge=-1), K('hurt2', R + 45, lunge=-2, lean=-1), K('hurt2', R + 45, lunge=-2, lean=-1, squash=1, fx=['dust']),
                       K('idle', R, lunge=-1), K('idle', R)], 12, False)
    M['Dodge'] = ([K('idle', R, squash=1), K('idle', R + 10, lean=-1, lunge=-3, ghost=1), K('idle', R + 10, lean=-1, lunge=-4, ghost=2),
                   K('idle', R, squash=1), K('idle', R)], 14, False)
    M['Roll'] = ([K('idle', R, squash=1), K('roll', None, roll=0), K('roll', None, roll=1), K('roll', None, roll=2), K('roll', None, roll=3),
                  K('idle', R, squash=1), K('idle', R)], 14, False)
    M['Death'] = ([K('death0', R + 10), K('death1', None, drop=1), K('death2', None, drop=2), K('death3', None, drop=2)], 8, False)
    # guard (weapons with a guard: everything but the bow; the staff and daggers parry with the weapon crossed)
    g = 20 if W not in ('Spear', 'Staff') else 45
    M['Block'] = ([K('raise', g, squash=1), K('raise', g, squash=1)], 10, False)
    M['BlockHit'] = ([K('raise', g + 10, squash=1, lunge=-1, fx=['spark']), K('raise', g, squash=1)], 12, False)

    # ------------------------------------------------ attacks
    def swing(a0, a1, pose_w='raise2', pose_s='mid', pose_f='low', big=False, fps=f, lunge=1, extra=None, heavy_fx=False):
        r_out = WA.reach_px(k.weapon) * k.scale + (2 if big else 1)
        r_in = max(3, r_out - (8 if big else 6))
        seq = [K('raise' if pose_w == 'raise2' else pose_w, a0 + 15, squash=1),
               K(pose_w, a0, ev=['Anticipation']),
               K(pose_s, a1 - 30, lunge=lunge, trail=(a0, a1 - 30, r_in, r_out), ev=['HitOn']),
               K(pose_f, a1, lunge=lunge, trail=(a0 + 40, a1, r_in, r_out, 'fade'), fx=(['dust', 'ring'] if heavy_fx else []), ev=['HitOff']),
               K(pose_f, a1, ev=['ComboWindow']),
               K('idle', R, ev=['End'])]
        if extra:
            seq[3:3] = extra
        return seq, fps, False

    def thrust(a=90, reach=4, fps=f, pose_w='raise', pose_s='idle', ret=True, double=False):
        seq = [K(pose_w, a, lunge=-1, squash=1, ev=['Anticipation']),
               K(pose_s, a, lunge=reach, lean=1, reach=reach, thrust=reach + 6, ev=['HitOn']),
               K(pose_s, a, lunge=reach, lean=1, reach=reach - 1, ev=['HitOff']), ]
        if double:
            seq += [K(pose_s, a, lunge=1, reach=0), K(pose_s, a, lunge=reach, lean=1, reach=reach, thrust=reach + 6, ev=['HitOn']),
                    K(pose_s, a, lunge=reach - 1, reach=reach - 1, ev=['HitOff'])]
        seq += [K(pose_s, a, lunge=1, ev=['ComboWindow']), K('idle', R, ev=['End'])]
        return seq, fps, False

    if W in ('Sword', 'Legendary', 'Axe'):
        M['Attack'] = swing(-40, 140)
        M['Attack2'] = ([K('low', 165, squash=1, ev=['Anticipation']), K('mid', 120, lunge=1, trail=(165, 120, 4, 13), ev=['HitOn']),
                         K('raise', 40, lunge=1, trail=(165, 40, 5, 13), ev=[]), K('raise2', 15, trail=(120, 15, 5, 13, 'fade'), ev=['HitOff']),
                         K('raise', 20, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        M['Attack3'] = thrust(90, 4) if W != 'Axe' else swing(-60, 150, 'hraise2', 'mid', 'hlow', big=True, heavy_fx=True)
        M['ComboAttack'] = swing(-70, 160, 'hraise2', 'mid2', 'hlow', big=True, lunge=2, heavy_fx=True,
                                 extra=[K('hlow', 160, lunge=2, fx=['ring2'])])
        M['HeavyAttack'] = ([K('hraise', -30, squash=2, ev=['Anticipation']), K('hraise2', -60, stretch=1, lift=2),
                             K('hraise2', -70, lift=4), K('mid', 100, lunge=2, trail=(-70, 100, 5, 15), ev=['HitOn']),
                             K('hlow', 165, lunge=2, squash=1, trail=(-10, 165, 5, 15, 'fade'), fx=['ring', 'dust']),
                             K('hlow', 165, lunge=2, fx=['ring2'], ev=['HitOff']), K('idle', R, ev=['End'])], f - 1, False)
    elif W in ('Greatsword', 'HeavyAxe', 'Hammer'):
        big_fx = W != 'Greatsword'
        M['Attack'] = swing(-50, 150, 'hraise2', 'mid', 'hlow', big=True, fps=f, heavy_fx=big_fx)
        M['Attack2'] = ([K('hlow', 170, squash=1, ev=['Anticipation']), K('mid', 120, lunge=1, trail=(170, 120, 6, 16)),
                         K('raise', 50, lunge=2, trail=(170, 50, 6, 16), ev=['HitOn']), K('raise2', 10, lunge=1, trail=(120, 10, 6, 16, 'fade'), ev=['HitOff']),
                         K('raise2', 10, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        # spin: the weapon goes all the way round behind the body
        M['Attack3'] = ([K('hraise', 60, squash=1, ev=['Anticipation']), K('hraise2', 130, lunge=1, trail=(60, 130, 6, 16), ev=['HitOn']),
                         K('low', 200, behind=True, trail=(60, 200, 6, 16)), K('low', 260, behind=True), K('raise', 330, behind=True),
                         K('mid', 100, lunge=2, trail=(-30, 100, 6, 16, 'fade'), ev=['HitOff']), K('mid', 100, ev=['ComboWindow']), K('idle', R, ev=['End'])], f + 2, False)
        M['ComboAttack'] = ([K('hraise', -20, squash=2, ev=['Anticipation']), K('hraise2', -60, stretch=1, lift=3), K('hraise2', -75, lift=6),
                             K('mid', 110, lunge=3, lift=2, trail=(-75, 110, 6, 17), ev=['HitOn']),
                             K('hlow', 170, lunge=3, squash=2, trail=(0, 170, 6, 17, 'fade'), fx=['ring', 'dust', 'crack']),
                             K('hlow', 170, lunge=3, squash=1, fx=['ring2'], ev=['HitOff']), K('hlow', 170, lunge=2, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        M['HeavyAttack'] = ([K('hraise', -30, squash=2, ev=['Anticipation']), K('hraise2', -70, squash=1), K('hraise2', -80, stretch=1),
                             K('mid', 110, lunge=2, trail=(-80, 110, 6, 17), ev=['HitOn']),
                             K('hlow', 175, lunge=2, squash=2, trail=(-10, 175, 6, 17, 'fade'), fx=['ring', 'dust', 'crack']),
                             K('hlow', 175, lunge=2, squash=1, fx=['ring2', 'crack'], ev=['HitOff']), K('hlow', 175, lunge=1), K('idle', R, ev=['End'])], f - 1, False)
    elif W == 'Katana':
        M['Attack'] = ([K('low', 200, behind=True, squash=1, ev=['Anticipation']), K('mid', 70, lunge=2, trail=(160, 70, 4, 14), ev=['HitOn']),
                        K('raise', 30, lunge=2, trail=(160, 30, 4, 14, 'fade'), ev=['HitOff']), K('raise', 30, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        M['Attack2'] = ([K('raise2', -20, ev=['Anticipation']), K('mid', 110, lunge=2, trail=(-20, 110, 4, 14), ev=['HitOn']),
                         K('low', 160, lunge=2, trail=(30, 160, 4, 14, 'fade'), ev=['HitOff']), K('low', 160, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        M['Attack3'] = thrust(90, 5, pose_w='raise', pose_s='idle')
        M['ComboAttack'] = ([K('idle', R, squash=1, ev=['Anticipation']), K('idle', 90, lunge=6, ghost=2, thrust=12, ev=['HitOn']),
                             K('mid', 120, lunge=8, trail=(0, 170, 4, 14), ghost=1), K('low', 170, lunge=8, ev=['HitOff']),
                             K('low', 170, lunge=8, fx=['spark'], ev=['ComboWindow']), K('idle', R, lunge=8, ev=['End'])], f, False)
        M['HeavyAttack'] = ([K('low', 210, behind=True, squash=2, ev=['Anticipation']), K('low', 210, behind=True, squash=2, fx=['glint']),
                             K('mid', 80, lunge=3, trail=(200, 80, 3, 15), ev=['HitOn']), K('raise2', -10, lunge=3, trail=(200, -10, 3, 15, 'fade')),
                             K('raise', 10, lunge=3, ev=['HitOff']), K('idle', R, ev=['End'])], f, False)
    elif W == 'Rapier':
        M['Attack'] = thrust(90, 4, pose_w='raise', pose_s='raise')
        M['Attack2'] = thrust(80, 4, pose_w='raise', pose_s='raise', double=True)
        M['Attack3'] = ([K('raise', 40, ev=['Anticipation']), K('mid', 110, lunge=1, trail=(40, 110, 5, 14), ev=['HitOn']),
                         K('low', 150, trail=(40, 150, 5, 14, 'fade'), ev=['HitOff']), K('low', 150, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        M['ComboAttack'] = ([K('raise', 90, squash=2, lunge=-1, ev=['Anticipation']), K('raise', 90, lunge=5, lean=1, ghost=1, thrust=12, reach=3, ev=['HitOn']),
                             K('raise', 90, lunge=8, lean=1, ghost=2, thrust=14, reach=4), K('raise', 90, lunge=8, reach=3, ev=['HitOff']),
                             K('raise', 90, lunge=8, ev=['ComboWindow']), K('idle', R, lunge=8, ev=['End'])], f, False)
        M['HeavyAttack'] = ([K('raise', 90, squash=2, lunge=-2, fx=['glint'], ev=['Anticipation']), K('raise', 90, squash=2, lunge=-2),
                             K('raise', 90, lunge=6, lean=2, reach=5, thrust=14, ghost=2, ev=['HitOn']), K('raise', 90, lunge=6, lean=1, reach=4, fx=['spark']),
                             K('raise', 90, lunge=5, reach=2, ev=['HitOff']), K('idle', R, lunge=4, ev=['End'])], f - 2, False)
    elif W == 'Dagger':
        M['Attack'] = ([K('raise', 90, lunge=-1, ev=['Anticipation']), K('raise', 90, lunge=3, reach=3, thrust=7, ev=['HitOn']),
                        K('raise', 90, lunge=3, reach=2, ev=['HitOff']), K('idle', R, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        M['Attack2'] = ([K('idle', R, off_a=90, ev=['Anticipation']), K('idle', R, off_a=90, off_reach=4, lunge=3, thrust=7, ev=['HitOn']),
                         K('idle', R, off_a=90, off_reach=3, lunge=3, ev=['HitOff']), K('idle', R, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        M['Attack3'] = ([K('raise2', -30, ev=['Anticipation']), K('mid', 100, lunge=2, trail=(-30, 100, 3, 9), off_a=200, ev=['HitOn']),
                         K('low', 160, lunge=2, trail=(30, 160, 3, 9, 'fade'), off_a=60), K('raise', 60, lunge=2, trail=(160, 60, 3, 9), off_a=150, ev=['HitOff']),
                         K('raise', 60, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        # flurry: spin with both blades out
        M['ComboAttack'] = ([K('idle', 90, off_a=270, squash=1, ev=['Anticipation']), K('mid', 120, off_a=300, lunge=1, trail=(0, 120, 3, 10), ev=['HitOn']),
                             K('low', 200, off_a=20, behind=True, lunge=2, trail=(60, 200, 3, 10)), K('raise', 300, off_a=120, behind=True, lunge=3),
                             K('raise2', 60, off_a=200, lunge=4, trail=(300, 420, 3, 10), ev=['HitOff']), K('idle', R, lunge=4, ev=['ComboWindow']), K('idle', R, lunge=4, ev=['End'])], f, False)
        M['HeavyAttack'] = ([K('raise', 90, off_a=90, squash=2, lunge=-1, ev=['Anticipation']), K('raise', 90, off_a=90, squash=1, lunge=-1),
                             K('raise', 90, off_a=90, off_reach=3, lunge=5, reach=3, thrust=9, ghost=2, ev=['HitOn']),
                             K('raise', 90, off_a=90, off_reach=2, lunge=5, reach=2, fx=['spark'], ev=['HitOff']), K('idle', R, lunge=4, ev=['End'])], f - 2, False)
    elif W == 'Spear':
        M['Attack'] = thrust(90, 5, pose_w='aim0', pose_s='aim')
        M['Attack2'] = ([K('aim0', 40, ev=['Anticipation']), K('mid', 100, lunge=1, trail=(40, 100, 8, 15), ev=['HitOn']),
                         K('low', 150, lunge=1, trail=(40, 150, 8, 15, 'fade'), ev=['HitOff']), K('low', 150, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        M['Attack3'] = thrust(90, 5, pose_w='aim0', pose_s='aim', double=True)
        M['ComboAttack'] = ([K('aim0', 60, squash=2, ev=['Anticipation']), K('aim0', 45, lift=5, stretch=1), K('aim', 120, lift=4, lunge=3),
                             K('aim', 135, lunge=5, reach=3, thrust=10, ev=['HitOn']), K('aim', 135, lunge=5, reach=3, fx=['ring', 'dust'], ev=['HitOff']),
                             K('aim0', 90, lunge=4, ev=['ComboWindow']), K('idle', R, lunge=4, ev=['End'])], f, False)
        M['HeavyAttack'] = ([K('aim0', 90, squash=2, lunge=-3, ev=['Anticipation']), K('aim0', 90, squash=2, lunge=-3, fx=['glint']),
                             K('aim', 90, lunge=6, lean=1, reach=6, thrust=16, ghost=2, ev=['HitOn']), K('aim', 90, lunge=6, lean=1, reach=5),
                             K('aim', 90, lunge=5, reach=2, ev=['HitOff']), K('idle', R, lunge=4, ev=['End'])], f - 2, False)
    elif W == 'Staff':
        M['Attack'] = swing(-30, 120, lunge=1)
        M['Attack2'] = thrust(90, 3, pose_w='raise', pose_s='raise')
        # Attack3: a magic bolt leaves the crystal on the Projectile frame
        M['Attack3'] = ([K('raise', 0, squash=1, keep=1, ev=['Anticipation']), K('raise2', -5, orb=1), K('raise2', -5, orb=2),
                         K('raise', 80, lunge=1, orb=3, ev=['Projectile']), K('raise', 85, fx=['spark']), K('raise', 80, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        M['ComboAttack'] = ([K('hraise', 0, squash=1, ev=['Anticipation']), K('hraise2', 0, orb=2, fx=['runes']), K('hraise2', 0, orb=3, fx=['runes']),
                             K('hlow', 180, squash=2, fx=['ring', 'ring2', 'runes'], ev=['HitOn']), K('hlow', 180, squash=1, fx=['ring2'], ev=['HitOff']),
                             K('hlow', 180, ev=['ComboWindow']), K('idle', R, ev=['End'])], f, False)
        M['HeavyAttack'] = ([K('raise', 0, squash=1, keep=1, ev=['Anticipation']), K('raise2', -5, orb=1, fx=['runes']), K('raise2', -5, orb=2, fx=['runes']),
                             K('raise2', -5, orb=3, fx=['runes']), K('raise', 85, lunge=2, orb=3, ev=['Projectile']), K('raise', 90, lunge=1, fx=['spark']),
                             K('idle', R, ev=['End'])], f - 1, False)
    # ------------------------------------------------ charged attack (hold the heavy button) + riposte
    M['ChargedAttack_Charge'] = ([K('hraise', -40, squash=t % 2, charge=t) for t in range(4)], 12, True)
    rel = M['HeavyAttack'][0][2:] if W not in ('Staff',) else [K('hraise2', 0, orb=3, fx=['runes']), K('raise', 90, lunge=2, orb=3, ev=['Projectile']),
                                                                 K('raise', 90, fx=['ring', 'spark']), K('idle', R, ev=['End'])]
    rel = [dict(r) for r in rel]
    for r in rel:
        r['fx'] = list(r.get('fx', [])) + (['runes'] if W == 'Legendary' else [])
        if 'trail' in r and r['trail'] and W != 'Staff':
            a0, a1, ri, ro = r['trail'][:4]
            r['trail'] = (a0, a1, ri, ro + 2) + tuple(r['trail'][4:])
    if W == 'Legendary':
        rel.insert(2, K('hlow', 170, lunge=2, fx=['wave', 'runes'], ev=[]))
    M['ChargedAttack_Release'] = (rel, f, False)
    M['CriticalAttack'] = ([K('raise', 90, lunge=-1, squash=1, ev=['Anticipation']), K('raise', 90, lunge=4, lean=1, reach=4, thrust=10, flashw=1, ev=['HitOn']),
                            K('raise', 90, lunge=4, reach=4, fx=['crit']), K('mid', 140, lunge=3, ev=['HitOff']), K('idle', R, ev=['End'])], 12, False)
    return M


def bow_moves(name):
    """SpecialAttack (shot) and BowCharged for a bow kind; the arrow leaves on the Projectile frame"""
    cross = name == 'crossbow'
    if cross:
        shot = [K('aim0', 90, ev=['Anticipation']), K('aim', 90, bow=1), K('aim', 90, bow=2), K('aim', 90, lunge=-1, bow=3, fx=['spark'], ev=['Projectile']),
                K('aim', 90, lunge=-1, bow=0), K('aim0', 90, bow=0, ev=['End'])]
    else:
        shot = [K('aim0', 0, bow=0, ev=['Anticipation']), K('aim', 0, bow=1), K('aim', 0, bow=2, squash=1), K('aim', 0, bow=3, ev=['Projectile']),
                K('aim', 0, bow=4), K('aim0', 0, bow=0, ev=['End'])]
    return {'SpecialAttack': (shot, 12, False)}


# =============================================================== rendering
class Renderer:
    def __init__(self, key='Soldier'):
        self.B = Bodies(key)
        self.s = self.B.s
        self.hand = SOLDIER_HAND

    def pose_for(self, view, kf):
        name = kf['pose']
        if name == 'roll':
            return None
        if view == 'Right':
            P = self.B.side(name)
        else:
            P = self.B.vert(view, name)
        if kf.get('squash'):
            P = t_squash(P, kf['squash'])
        if kf.get('stretch'):
            P = t_stretch(P, kf['stretch'])
        if kf.get('lean') and view == 'Right':
            P = t_lean(P, kf['lean'])
        return P

    def offset(self, view, kf):
        """whole-figure displacement: lunge (forward), lift (up)"""
        L, up = kf.get('lunge', 0), kf.get('lift', 0)
        if view == 'Right':
            return L, -up
        return 0, (L if view == 'Down' else -L) - up

    CARRY = ('idle', 'idle1', 'idle2', 'idle3', 'hurt', 'hurt2')

    def view_angle(self, k, view, kf, a):
        p = kf.get('pose', '')
        if (kf.get('orb') or kf.get('keep')) and abs(a) <= 10:
            return a                                 # a staff raised to cast stays upright in every view
        busy = kf.get('reach') or kf.get('thrust') or kf.get('lunge') or kf.get('trail') or             set(kf.get('ev', [])) & {'HitOn', 'HitOff', 'Anticipation', 'Projectile'}
        if view != 'Right' and (p in self.CARRY or p.startswith('walk') or p.startswith('death')) and abs(a - k.rest) <= 35                 and (not busy or p.startswith('walk')):
            return k.rest_v + (a - k.rest) * 0.5
        return map_angle(a, view)

    def weapon_layer(self, k, view, a, grip, reach=0, flip=False, kf=None):
        av = self.view_angle(k, view, kf or {}, a)
        gx, gy = grip
        if reach:
            th = math.radians(av)
            gx += round(math.sin(th) * reach); gy -= round(math.cos(th) * reach)
        fl = k.flipx if view != 'Up' else not k.flipx
        return WA.pose(k.weapon, av, gx, gy, flipx=fl, scale=k.scale), (gx, gy), av

    def frame(self, k, view, kf, bow=None):
        """renders one keyframe; lunges and reaches are shortened until the weapon fits inside the 64 px cell"""
        if bow is None and kf.get('a') is not None and kf.get('pose') != 'roll':
            kf = dict(kf)
            if view != 'Right':
                kf['lunge'] = max(-2, min(2, kf.get('lunge', 0)))
            for _ in range(16):
                P = self.pose_for(view, kf)
                dx, dy = self.offset(view, kf)
                av = self.view_angle(k, view, kf, kf['a'])
                gx, gy = P.grip
                r = kf.get('reach', 0)
                th = math.radians(av)
                gx += math.sin(th) * r; gy -= math.cos(th) * r
                tx, ty = WA.tip(k.weapon, av, gx, gy)
                tx += dx; ty += dy
                if 3 <= tx <= 60 and 3 <= ty <= 61:
                    break
                if kf.get('reach', 0) > 0:
                    kf['reach'] -= 1
                elif abs(kf.get('lunge', 0)) > 0:
                    kf['lunge'] -= 1 if kf['lunge'] > 0 else -1
                else:
                    break
        return self._frame(k, view, kf, bow)

    def _frame(self, k, view, kf, bow=None):
        P = self.pose_for(view, kf)
        dx, dy = self.offset(view, kf)
        if P is None:                                   # roll: the base rolled body, weapon tucked away
            idle0 = strip_weapon(self.s.body('Idle', 0)) if view == 'Right' else self.B.vert(view, 'idle').body
            tuck = squash(idle0, 3)
            b = bbox(tuck); piv = ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
            r = kf['roll']
            rf = rot90(tuck, r if view == 'Right' else 0, piv) if r else tuck
            if view != 'Right':
                rf = shift(squash(idle0, 3 + (r % 2)), 0, 0)
            bb = bbox(rf)
            out = shift(rf, 0, FEET - bb[3])
            return self.s.with_shadow(out, 0)
        body = P.body
        layers_back, layers_front = [], []
        tipxy = None
        a = kf['a']
        if bow is not None:
            body, tipxy = self._bow(view, kf, P, bow)
        elif a is not None:
            wl, g2, av = self.weapon_layer(k, view, a, P.grip, kf.get('reach', 0), kf=kf)
            if kf.get('flashw'):
                wl = X.glow(wl, X.WHT)
            if k.glow is not None and (kf.get('charge') is not None or kf.get('orb')):
                wl = X.glow(wl, k.glow)
            (layers_back if behind_for(view, av, kf) else layers_front).append(wl)
            tipxy = WA.tip(k.weapon, av, *g2)
            hand_at = g2
            # off-hand weapon (dual daggers)
            if k.off_weapon:
                oa = kf.get('off_a', (k.rest + 10))
                og = P.off or (P.grip[0] - 8, P.grip[1])
                stab = kf.get('off_reach', 0) > 0
                if stab and view == 'Right':          # the back hand comes across the body for its stab
                    og = (P.grip[0] - 1, P.grip[1] + 1)
                ol, og2, oav = (lambda r: r)(self.weapon_layer(Kind('o', k.off_weapon, 0), view, oa, og, kf.get('off_reach', 0)))
                off_behind = (not stab) if view == 'Right' else behind_for(view, oav, {})
                (layers_back if off_behind else layers_front).append(ol)
                if not off_behind:
                    layers_front.append(('hand', og2))
            if k.two_hand and view == 'Right' and P.off:
                pass
            layers_front.append(('hand', hand_at))
        out = blank()
        for l in layers_back:
            out = over(out, l)
        out = over(out, body)
        for l in layers_front:
            if isinstance(l, tuple):
                out = WA.hand(out, l[1][0] - 1, l[1][1] - 1, self.hand) if not self._hand_hidden(view, kf) else out
            else:
                out = over(out, l)
        # trails and effects
        tr = kf.get('trail')
        if tr and bow is None:
            a0, a1, ri, ro = tr[:4]
            fade = len(tr) > 4
            g = P.grip
            cols = k.trail
            if view == 'Right':
                out = WA.trail(out, g[0], g[1], ri * k.scale, ro * k.scale, a0, a1, cols, fade, behind=True)
            else:
                m0, m1 = map_angle(a0, view), map_angle(a1, view)
                out = WA.trail(out, g[0], g[1], ri * k.scale, ro * k.scale, m0, m1, cols, fade, ry=.75, behind=True)
        if kf.get('thrust') and tipxy is not None:
            L = kf['thrust']
            tx, ty = int(round(tipxy[0])), int(round(tipxy[1]))
            if view == 'Right':
                out = WA.thrust_lines(out, tx - 2, tx - 2 - L, ty, k.trail)
            elif view == 'Down':
                out = WA.vthrust_lines(out, tx, ty - 2, ty - 2 - L, k.trail)
            else:
                out = WA.vthrust_lines(out, tx, ty + 2, ty + 2 + L, k.trail)
        for fx in kf.get('fx', []):
            out = self._fx(out, fx, view, tipxy, k)
        if kf.get('orb') and tipxy is not None:
            r = kf['orb']
            out = X.orb(out, tipxy[0], tipxy[1], 1 + r * .7, [hx('#64c8f8'), hx('#c8f4ff'), X.WHT][:1 + min(r, 2)])
        if kf.get('charge') is not None:
            t = kf['charge']
            col = k.glow or X.YEL
            out = X.glow(out, col if t % 2 == 0 else X.WHT)
            for j in range(3):
                ang = (t * 40 + j * 120) * math.pi / 180
                rr = 10 - (t % 2) * 3
                X.px(out, 31 + math.cos(ang) * rr, 42 + math.sin(ang) * rr * .6, col)
        if kf.get('flash'):
            (m1, g1), _ = self.s.hurt_maps()
            out = recolor(out, m1)
            if g1:
                out = outline(out, g1 + (255,) if len(g1) == 3 else g1)
        if kf.get('drop'):
            # the weapon lies on the ground next to the fallen body
            wl = WA.pose(k.weapon, 95 if view != 'Up' else 85, 40 if view == 'Right' else 38, 51 - (1 if kf['drop'] == 1 else 0))
            out = over(wl, out) if view == 'Up' else over(out, wl)
        out = shift(out, dx, dy)
        if kf.get('ghost'):
            gdx = -2 * kf['ghost'] if view == 'Right' else 0
            gdy = 0 if view == 'Right' else (-2 * kf['ghost'] if view == 'Down' else 2 * kf['ghost'])
            out = X.afterimage(out, shift(out, gdx, gdy), .3)
        return self.s.with_shadow(out, max(0, kf.get('lift', 0)))

    def _hand_hidden(self, view, kf):
        return view == 'Up' and kf['pose'] in ('idle',) and False

    def _fx(self, f, fx, view, tipxy, k):
        cx = 31 + (8 if view == 'Right' else 0)
        cy = FEET - 1 + (6 if view == 'Down' else -6 if view == 'Up' else 0)
        if fx == 'dust':
            return X.dust(f, 27 if view == 'Right' else 31, FEET - 1, 1, side=-1)
        if fx == 'ring':
            return X.ring(f, cx, cy, 9, X.DUST)
        if fx == 'ring2':
            return X.ring(f, cx, cy, 13, X.DUST2)
        if fx == 'crack':
            out = f.copy()
            for i in range(-5, 6):
                X.px(out, cx + i, cy + (abs(i) % 3 == 0), hx('#3a2a22'))
            return out
        if fx == 'spark' and tipxy is not None:
            return X.sparkle(f, int(tipxy[0]), int(tipxy[1]), 2, X.WHT, X.YEL)
        if fx == 'glint' and tipxy is not None:
            return X.sparkle(f, int(tipxy[0]), int(tipxy[1]), 1, X.WHT, X.WHT)
        if fx == 'crit':
            return X.sparkle(X.sparkle(f, cx + 6, 38, 3, X.YEL, X.ORA), cx + 10, 44, 2)
        if fx == 'runes':
            out = X.ring(f, 31, FEET - 1, 11, hx('#64c8f8'))
            for j in range(4):
                ang = j * math.pi / 2 + .4
                X.px(out, 31 + math.cos(ang) * 11, FEET - 1 + math.sin(ang) * 5, hx('#c8f4ff'))
            return out
        if fx == 'wave':
            col = k.trail[1]
            out = f.copy()
            if view == 'Right':
                for i in range(6):
                    out = X.ring(out, 44 + i, FEET - 6, 6 - i // 2, col, ry=1.4)
            else:
                out = X.ring(out, 31, cy + (6 if view == 'Down' else -6), 10, col, ry=.5)
            return out
        return f

    def _bow(self, view, kf, P, name):
        """bow kinds: bow held out in front, arrow nocked and drawn (stage 1..3), released (4)"""
        stage = kf.get('bow', 0)
        body = P.body
        g = P.grip
        out_front, out_back = [], []
        cross = name == 'crossbow'
        if view == 'Right':
            a = 90 if cross else 0
            gx, gy = g
            wl = WA.pose(name, a, gx, gy)
            out_front.append(wl)
            if stage in (1, 2, 3) and not cross:
                pull = (0, 1, 3, 4)[stage]
                out_front.append(WA.pose('arrow', 90, gx - 3 - pull, gy))
            if cross and stage in (1, 2):
                out_front.append(WA.pose('bolt', 90, gx - 1, gy - 2))
            tip = (gx + 8, gy)
        else:
            down = view == 'Down'
            a = (180 if down else 0) if cross else (90 if down else 270)
            gx, gy = 31 + (0 if down else 0), (g[1] + 1 if down else g[1] - 2)
            wl = WA.pose(name, a, gx, gy)
            (out_front if down else out_back).append(wl)
            if stage in (1, 2, 3) and not cross:
                pull = (0, 1, 3, 4)[stage]
                aa = 180 if down else 0
                out_front.append(WA.pose('arrow', aa, gx, gy - (4 + pull - 6) * (1 if down else -1))) if down else out_back.append(WA.pose('arrow', aa, gx, gy + (4 + pull - 6)))
            tip = (gx, gy + 8 if down else gy - 8)
        out = blank()
        for l in out_back:
            out = over(out, l)
        out = over(out, body)
        for l in out_front:
            out = over(out, l)
        if view == 'Right':
            out = WA.hand(out, g[0] - 1, g[1] - 1, self.hand)
        return out, tip


# =============================================================== output
def render_set(R, k, clips=None):
    """-> {(clip, dir): (frames, seq, fps, loop, events)}"""
    out = {}
    mv = moves(k) if isinstance(k, Kind) else k
    for clip, (kfs, fps, loop) in mv.items():
        if clips and clip not in clips:
            continue
        right = []
        for view in ('Right', 'Down', 'Up'):
            frames = [R.frame(k, view, kf) for kf in kfs]
            ev = []
            for i, kf in enumerate(kfs):
                for e in kf.get('ev', []):
                    ev.append(dict(frame=i, fn='AnimEvent', arg=e))
            if view == 'Right':
                right = frames
            out[(clip, view)] = (frames, fps, loop, ev)
        out[(clip, 'Left')] = ([flip(f) for f in right], fps, loop, out[(clip, 'Right')][3])
        if clip == 'Death':          # the fall is only drawn from the side: front/back deaths topple sideways
            out[(clip, 'Down')] = (right, fps, loop, out[(clip, 'Right')][3])
            out[(clip, 'Up')] = out[(clip, 'Left')]
    return out


def render_bow(R, bow):
    k = Kind('b', bow, 0)
    out = {}
    for clip, (kfs, fps, loop) in bow_moves(bow).items():
        for view in ('Right', 'Down', 'Up'):
            frames = [R.frame(k, view, kf, bow=bow) for kf in kfs]
            ev = [dict(frame=i, fn='AnimEvent', arg=e) for i, kf in enumerate(kfs) for e in kf.get('ev', [])]
            out[(clip, view)] = (frames, fps, loop, ev)
        r = out[(clip, 'Right')]
        out[(clip, 'Left')] = ([flip(f) for f in r[0]], fps, loop, r[3])
    return out


CAT = {'Idle': 'Idle', 'Walk': 'Walk', 'Run': 'Run', 'Hurt': 'Hurt', 'Knockback': 'Combat', 'Block': 'Combat', 'BlockHit': 'Combat',
       'Dodge': 'Dodge', 'Roll': 'Dodge', 'Death': 'Death', 'SpecialAttack': 'Special', 'ChargedAttack_Charge': 'Special',
       'ChargedAttack_Release': 'Special', 'ComboAttack': 'Special', 'CriticalAttack': 'Special'}


def dedupe_frames(frames):
    uniq, seq = [], []
    for f in frames:
        for j, u in enumerate(uniq):
            if np.array_equal(f, u):
                seq.append(j); break
        else:
            seq.append(len(uniq)); uniq.append(f)
    return uniq, seq


def write_set(cls, kind, data, recolor_map=None, meta=None):
    name = f'{cls}_{kind}'
    root = os.path.join(SETS_ROOT, cls, kind)
    clips = []
    for (clip, d), (frames, fps, loop, ev) in sorted(data.items()):
        uniq, seq = dedupe_frames(frames)
        if recolor_map:
            uniq = [recolor_np(f, recolor_map) for f in uniq]
        rel = f"{CAT.get(clip, 'Attack')}/{name}_{clip}_{d}.png"
        save_sheet(uniq, os.path.join(root, rel))
        clips.append(dict(name=clip, dir=d, file=rel, frames=len(uniq), seq=seq, fps=fps, loop=loop,
                          size=[CELL * len(uniq), CELL], events=ev))
    man = dict(character=name, base=cls, weapon=kind, cell=CELL, pivot=[0.5, (CELL - FEET) / CELL], ppu=16, clips=clips)
    if meta:
        man.update(meta)
    with open(os.path.join(root, f'{name}_animations.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    return len(clips)


def recolor_np(f, cmap):
    out = f.copy()
    for src, dst in cmap.items():
        m = np.all(f[:, :, :3] == src, axis=2) & (f[:, :, 3] > 0)
        out[m, :3] = dst
    return out


def class_maps():
    import variants as V
    return {c: V.build_map('Soldier', V.VARIANTS[c][1]) for c in ('KnightPaladin', 'KnightDark', 'KnightRanger', 'KnightSamurai')}


def main(kinds=None):
    R = Renderer('Soldier')
    maps = class_maps()
    kinds = kinds or list(KINDS) + list(BOWS)
    for kind in kinds:
        if kind in KINDS:
            k = KINDS[kind]
            data = render_set(R, k)
            meta = dict(reach_px=round(WA.reach_px(k.weapon) * k.scale, 1), set_type='melee')
        else:
            data = render_bow(R, BOWS[kind])
            meta = dict(reach_px=0, set_type='bow')
        n = write_set('Soldier', kind, data, meta=meta)
        for cls, cm in maps.items():
            write_set(cls, kind, data, cm, meta=meta)
        print(kind, n, 'clips x 4 classes')


if __name__ == '__main__':
    main(sys.argv[1:] or None)
