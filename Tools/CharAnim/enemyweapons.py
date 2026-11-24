"""Roster figures (33 monsters + 9 town heroes) with a REAL weapon layer and attack phases.

  python enemyweapons.py [Name ...]   -> Assets/Art/Characters/<Name>/... (replaces roster.py's clips, same layout)
                                         Documentation/CombatAnimations/enemies_<page>.png

The roster figures are single drawings with the weapon painted in. Here every armed figure gets its weapon CUT OUT
(rectangles in WEAPON_SPEC, measured on the figure's 64 px cell), the hole in the body is filled from its neighbours,
and the weapon becomes its own layer that is turned around the fist (weaponart-style 4x4 splat + outline). The body
keeps its own drawing (squash / lean / step / lunge), so the weapon finally follows the attack:

  Idle, Walk, Run, PrepareAttack, Attack, AttackRecovery, HeavyAttack, SpecialAttack, CastSpell, Hurt, Block,
  BlockHit, Dodge, Death   x  Right / Left (mirror) / Down / Up

The attack depends on the weapon (swing for swords, axes, maces, scythes and flails; thrust for spears and tridents;
draw-and-release for bows and crossbows; raise-and-cast for staves; shield bash; claws / bite for the unarmed) and on
the anatomy (flyers hover, the swing radius comes from the weapon length, the fist position from the drawing).

Directions: only the side view of these figures exists (original sheets). Down/Up reuse the side body and aim the
weapon, the trail and the projectile down/up (the weapon goes behind the body when attacking upwards). Drawing true
front/back bodies is listed as a production spec in Documentation/ANIMACIONES_COMBATE.md.

Animation events (HitOn, HitOff, Projectile, Telegraph, ComboWindow, End) go into the manifest for Unity.
"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from engine import *
import fxdraw as X
import weaponart as WA
import roster as RO

# name: dict(kind, rects=[(x0,y0,x1,y1) inclusive], grip=(x,y), tip=(x,y) optional, filt='light' optional,
#            erase=[rects of junk], hover=bool)
WEAPON_SPEC = {
    'WolfWarrior':     dict(kind='sword', rects=[(37, 44, 46, 50)], grip=(37, 48)),
    'GoblinAxe':       dict(kind='axe', rects=[(34, 42, 44, 50)], grip=(35, 47)),
    'GoblinViking':    dict(kind='mace', rects=[(37, 36, 47, 46)], grip=(37, 46)),
    'GoblinShaman':    dict(kind='staff', rects=[(36, 40, 47, 56)], grip=(38, 50), tip=(40, 42)),
    'GoblinRider':     dict(kind='spear', rects=[(35, 30, 45, 41)], grip=(35, 41), tip=(43, 31)),
    'Skeleton':        dict(kind='sword', rects=[(37, 42, 48, 49)], grip=(37, 47)),
    'SkeletonSpear':   dict(kind='spear', rects=[(30, 39, 35, 64)], grip=(31, 52), tip=(31, 40), erase=[(33, 55, 51, 63)]),
    'SkeletonWarrior': dict(kind='shield', rects=[], grip=(33, 46)),
    'SkeletonAxe':     dict(kind='axe', rects=[(35, 41, 44, 52)], grip=(35, 50)),
    'Reaper':          dict(kind='scythe', rects=[(21, 18, 27, 49)], grip=(24, 38), tip=(24, 19)),
    'ImpBlade':        dict(kind='sword', rects=[(31, 46, 44, 54)], grip=(31, 49)),
    'ImpCrossbow':     dict(kind='crossbow', rects=[(31, 40, 41, 53)], grip=(33, 49), filt='light'),
    'ImpTrident':      dict(kind='spear', rects=[(31, 39, 48, 48)], grip=(31, 44)),
    'DemonAxe':        dict(kind='axe', rects=[(35, 28, 42, 52)], grip=(35, 45), tip=(38, 30)),
    'ScytheCultist':   dict(kind='scythe', rects=[(37, 38, 46, 64)], grip=(37, 52), tip=(44, 41)),
    'ImpChain':        dict(kind='flail', rects=[(37, 37, 44, 47)], grip=(37, 38)),
    'Minotaur':        dict(kind='axe', rects=[(37, 54, 49, 62)], grip=(37, 57)),
    'DarkSpearman':    dict(kind='spear', rects=[(35, 35, 41, 64)], grip=(37, 52), tip=(37, 36)),
    'ShieldBrute':     dict(kind='shieldbash', rects=[(23, 37, 32, 51)], grip=(28, 44)),
    'DemonQueen':      dict(kind='staff', rects=[(36, 30, 42, 52)], grip=(37, 44), tip=(38, 32)),
    # heroes in the towns (they spar with the training dummies)
    'HeroSwordswoman': dict(kind='sword', rects=[(37, 46, 47, 53)], grip=(37, 47)),
    'HeroWizard':      dict(kind='staff', rects=[(36, 33, 40, 52)], grip=(36, 44), tip=(37, 35)),
    'HeroKnight':      dict(kind='sword', rects=[(36, 43, 47, 50)], grip=(36, 46)),
    'HeroCrusader':    dict(kind='spear', rects=[(35, 42, 49, 51)], grip=(35, 46)),
    'HeroAxeKnight':   dict(kind='axe', rects=[(36, 31, 45, 52)], grip=(36, 45), tip=(39, 33)),
    'HeroRider':       dict(kind='spear', rects=[(35, 17, 39, 34)], grip=(36, 33), tip=(36, 18)),
    'HeroPriestess':   dict(kind='staff', rects=[(38, 37, 41, 52)], grip=(38, 45), tip=(39, 38)),
    'HeroRanger':      dict(kind='bow', rects=[(37, 38, 44, 49)], grip=(37, 44)),
}
UNARMED = {   # how the creatures without a weapon attack
    'Werewolf': 'claw', 'SlimeGreen': 'body', 'Bat': 'bite', 'Hellhound': 'bite', 'DemonGreat': 'claw', 'FireSlug': 'body',
    'FlameSkull': 'body', 'HellBat': 'bite', 'Tentacle': 'whip', 'Maw': 'bite', 'EyeWatcher': 'body', 'ImpSwarm': 'claw',
    'LavaGolem': 'slam', 'HeroSoldier': 'claw',
}
SWING = {'sword', 'axe', 'mace', 'scythe', 'flail'}
THRUST = {'spear'}


# ------------------------------------------------------------------ cutting the weapon out
def base_of(name):
    base, flyer = RO.cut(name)
    base = RO.repair(name, base)
    spec = WEAPON_SPEC.get(name, {})
    for (x0, y0, x1, y1) in spec.get('erase', []):
        base[y0:y1 + 1, x0:x1 + 1] = 0
    return base, flyer


def weapon_mask(f, spec):
    m = np.zeros(f.shape[:2], bool)
    for (x0, y0, x1, y1) in spec['rects']:
        m[y0:y1 + 1, x0:x1 + 1] = True
    m &= f[:, :, 3] > 0
    if spec.get('filt') == 'light':
        lum = f[:, :, :3].astype(int) @ np.array([30, 59, 11]) / 100
        light = (lum > 120) & m
        near = ndimage.binary_dilation(light, iterations=1)
        black = np.all(f[:, :, :3] < 30, axis=2)
        m = light | (near & black & m)
    return m


def fill_holes(body, hole):
    """paint the pixels the weapon covered with the most common neighbouring body colour (2 passes)"""
    out = body.copy()
    todo = hole.copy()
    for _ in range(3):
        nxt = todo.copy()
        for y, x in zip(*np.nonzero(todo)):
            cols = {}
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X_, Y_ = x + ox, y + oy
                if 0 <= X_ < CELL and 0 <= Y_ < CELL and out[Y_, X_, 3] > 0 and not todo[Y_, X_]:
                    k = tuple(int(v) for v in out[Y_, X_])
                    cols[k] = cols.get(k, 0) + 1
            if sum(cols.values()) >= 3 or (sum(cols.values()) >= 2 and _opposite(out, todo, x, y)):
                out[y, x] = max(cols.items(), key=lambda kv: kv[1])[0]
                nxt[y, x] = False
        todo = nxt
    return out


def _opposite(f, todo, x, y):
    def on(X_, Y_):
        return 0 <= X_ < CELL and 0 <= Y_ < CELL and f[Y_, X_, 3] > 0 and not todo[Y_, X_]
    return (on(x - 1, y) and on(x + 1, y)) or (on(x, y - 1) and on(x, y + 1))


class Fig:
    """one roster figure split into body + weapon"""
    def __init__(self, name):
        self.name = name
        base, self.flyer = base_of(name)
        self.spec = WEAPON_SPEC.get(name)
        self.col = RO.ROSTER[name][3]
        self.kind = self.spec['kind'] if self.spec else UNARMED.get(name, 'claw')
        if self.spec and self.spec['rects']:
            m = weapon_mask(base, self.spec)
            self.weapon = np.zeros_like(base); self.weapon[m] = base[m]
            body = base.copy(); body[m] = 0
            # orphan outline pixels of the weapon left on the body
            body = fill_holes(body, m & self._inside(body, m))
            # black outline pixels of the weapon that now float free of the body
            black = np.all(body[:, :, :3] < 24, axis=2) & (body[:, :, 3] > 0)
            for _ in range(2):
                col_ = (body[:, :, 3] > 0) & ~black
                nb = np.zeros_like(col_)
                nb[1:] |= col_[:-1]; nb[:-1] |= col_[1:]; nb[:, 1:] |= col_[:, :-1]; nb[:, :-1] |= col_[:, 1:]
                orphan = black & ~nb
                body[orphan] = 0; black &= ~orphan
            self.body = body
        else:
            self.weapon, self.body = None, base
        # re-ground walkers whose feet were placed too low by the sheet's shadow (pre-existing cut bug)
        if not self.flyer:
            ys = np.nonzero(self.body[:, :, 3])[0]
            dy = (FEET - 1) - ys.max()
            if dy < 0:
                self.body = shift(self.body, 0, dy)
                if self.weapon is not None:
                    self.weapon = shift(self.weapon, 0, dy)
                self._dy = dy
            else:
                self._dy = 0
        else:
            self._dy = 0
        if self.spec:
            g = self.spec['grip']; self.grip = (g[0], g[1] + self._dy)
            t = self.spec.get('tip')
            if self.weapon is not None:
                if t:
                    self.tip0 = (t[0], t[1] + self._dy)
                else:
                    ys, xs = np.nonzero(self.weapon[:, :, 3])
                    d = (xs - self.grip[0]) ** 2 + (ys - self.grip[1]) ** 2
                    i = int(np.argmax(d)); self.tip0 = (int(xs[i]), int(ys[i]))
                self.rest = math.degrees(math.atan2(self.tip0[0] - self.grip[0], -(self.tip0[1] - self.grip[1])))
                self.length = math.hypot(self.tip0[0] - self.grip[0], self.tip0[1] - self.grip[1])
        b = bbox(self.body)
        self.h = b[3] - b[1]
        self.cx = (b[0] + b[2]) / 2
        self.hand_cols = self._hand_colours()

    def _inside(self, body, m):
        """weapon pixels that sat over the body (surrounded by body on two opposite sides) -> to be filled"""
        out = np.zeros_like(m)
        for y, x in zip(*np.nonzero(m)):
            l = any(body[y, xx, 3] > 0 for xx in range(max(0, x - 3), x))
            r = any(body[y, xx, 3] > 0 for xx in range(x + 1, min(CELL, x + 4)))
            u = any(body[yy, x, 3] > 0 for yy in range(max(0, y - 3), y))
            d = any(body[yy, x, 3] > 0 for yy in range(y + 1, min(CELL, y + 4)))
            out[y, x] = (l and r) or (u and d)
        return out

    def _hand_colours(self):
        if not self.spec:
            return None
        gx, gy = self.spec['grip'][0], self.spec['grip'][1] + self._dy
        cols = {}
        for y in range(gy - 3, gy + 4):
            for x in range(gx - 4, gx + 2):
                if 0 <= x < CELL and 0 <= y < CELL and self.body[y, x, 3] and self.body[y, x, :3].sum() > 90:
                    k = tuple(int(v) for v in self.body[y, x])
                    cols[k] = cols.get(k, 0) + 1
        if not cols:
            return (hx('#9a8a80'), hx('#5a4a44'))
        main = max(cols, key=cols.get)
        dark = tuple(int(v * .7) for v in main[:3]) + (255,)
        return (main, dark)

    # -------------------------------------------------------------- weapon posing
    def weapon_at(self, angle, grip):
        """weapon layer turned so its tip points to `angle` (our convention), fist on `grip`"""
        if self.weapon is None:
            return blank()
        delta = angle - self.rest
        src = self.weapon.copy()
        src[np.all(src[:, :, :3] < 24, axis=2)] = 0          # drop the old outline, it is redrawn after turning
        th = math.radians(delta); c, s = math.cos(th), math.sin(th)
        gx0, gy0 = self.grip
        votes = {}
        N = 4
        for y, x in zip(*np.nonzero(src[:, :, 3])):
            col = tuple(int(v) for v in src[y, x])
            for j in range(N):
                for i in range(N):
                    dx = x + (i + .5) / N - (gx0 + .5); dy = y + (j + .5) / N - (gy0 + .5)
                    rx, ry = dx * c - dy * s, dx * s + dy * c
                    tx, ty = int(math.floor(grip[0] + .5 + rx)), int(math.floor(grip[1] + .5 + ry))
                    d = votes.setdefault((tx, ty), {})
                    d[col] = d.get(col, 0) + 1
        out = blank()
        for (tx, ty), d in votes.items():
            if 0 <= tx < CELL and 0 <= ty < CELL and sum(d.values()) >= N * N * .28:
                out[ty, tx] = max(d.items(), key=lambda kv: kv[1])[0]
        return WA._outline(out)

    def tip(self, angle, grip, frac=1.0):
        th = math.radians(angle)
        return grip[0] + math.sin(th) * self.length * frac, grip[1] - math.cos(th) * self.length * frac


# ------------------------------------------------------------------ choreography
def K(**kw):
    return kw


def plan(fig):
    """{clip: (keyframes, fps, loop)}; angles absolute in SIDE terms (0 up, 90 forward)"""
    k = fig.kind
    R = getattr(fig, 'rest', 90)
    P = {}
    hov = fig.flyer
    bob = (lambda i: -(0, 1, 2, 1)[i % 4]) if hov else (lambda i: 0)
    P['Idle'] = ([K(a=R, dy=bob(0)), K(a=R + 3, dy=bob(1), sq=0 if hov else 1), K(a=R + 3, dy=bob(2), sq=0 if hov else 1), K(a=R, dy=bob(3))], 5, True)
    P['Walk'] = ([K(a=R + (0, 6, 0, -6, 0, 6)[i], legs=(1, 1, 0, -1, -1, 0)[i] if not hov else 0, dy=-(0, 1, 0, 0, 1, 0)[i] if not hov else bob(i))
                  for i in range(6)], 10, True)
    P['Run'] = ([K(a=R - 20 + (0, 8, 0, -8)[i], legs=(2, 0, -2, 0)[i] if not hov else 0, lean=1, dy=-(0, 2, 0, 2)[i] if not hov else bob(i),
                   fx=['dust'] if i in (0, 2) and not hov else []) for i in range(4)], 14, True)
    if k in SWING:
        up = -40 if k != 'flail' else -90
        P['PrepareAttack'] = ([K(a=R - 20, sq=1, ev=['Telegraph']), K(a=up, lean=-1, grip=(-1, -2)), K(a=up - 10, lean=-1, grip=(-1, -3), glint=1)], 10, False)
        P['Attack'] = ([K(a=100, lean=2, dx=2, grip=(2, 0), trail=(up - 10, 100), ev=['HitOn']), K(a=150, lean=2, dx=2, grip=(1, 2), trail=(up + 30, 150, 'fade')),
                        K(a=160, lean=1, dx=2, grip=(1, 2), ev=['HitOff'])], 12, False)
        P['AttackRecovery'] = ([K(a=150, dx=1, sq=1), K(a=(150 + R) / 2, dx=1), K(a=R, ev=['End'])], 9, False)
        P['HeavyAttack'] = ([K(a=R - 30, sq=2, ev=['Telegraph']), K(a=up - 20, st=1, grip=(-2, -3)), K(a=up - 30, st=1, dy=-2, grip=(-2, -4), glint=1),
                             K(a=110, lean=2, dx=3, grip=(2, 1), trail=(up - 30, 110, 'big'), ev=['HitOn']),
                             K(a=170, sq=1, dx=3, grip=(1, 3), trail=(-10, 170, 'fade'), fx=['ring', 'dust']),
                             K(a=170, dx=3, grip=(1, 3), fx=['ring2'], ev=['HitOff']), K(a=R, dx=1), K(a=R, ev=['End'])], 10, False)
        # special: spinning sweep
        P['SpecialAttack'] = ([K(a=R, sq=1, ev=['Telegraph']), K(a=100, dx=1, trail=(R - 60, 100), ev=['HitOn']), K(a=200, behind=1, dx=1, trail=(60, 200)),
                               K(a=300, behind=1), K(a=420, dx=1, trail=(300, 420, 'fade'), ev=['HitOff']), K(a=R, ev=['End'])], 12, False)
    elif k in THRUST:
        P['PrepareAttack'] = ([K(a=R, sq=1, ev=['Telegraph']), K(a=90, grip=(-3, 0), lean=-1), K(a=90, grip=(-4, 0), lean=-1, glint=1)], 10, False)
        P['Attack'] = ([K(a=90, grip=(5, 0), lean=1, dx=2, thrust=1, ev=['HitOn']), K(a=90, grip=(6, 0), lean=1, dx=2, thrust=1),
                        K(a=90, grip=(4, 0), dx=2, ev=['HitOff'])], 12, False)
        P['AttackRecovery'] = ([K(a=90, grip=(1, 0), dx=1), K(a=(90 + R) / 2), K(a=R, ev=['End'])], 9, False)
        P['HeavyAttack'] = ([K(a=90, sq=2, grip=(-4, 0), lean=-1, ev=['Telegraph']), K(a=90, sq=2, grip=(-5, 0), lean=-1, glint=1),
                             K(a=90, grip=(7, 0), lean=2, dx=4, thrust=2, ghost=1, ev=['HitOn']), K(a=90, grip=(7, 0), lean=1, dx=4, thrust=1),
                             K(a=90, grip=(4, 0), dx=4, ev=['HitOff']), K(a=R, dx=2, ev=['End'])], 11, False)
        P['SpecialAttack'] = ([K(a=50, sq=1, ev=['Telegraph']), K(a=110, dx=1, trail=(30, 110), ev=['HitOn']), K(a=160, dx=1, trail=(30, 160, 'fade')),
                               K(a=90, grip=(5, 0), thrust=1, dx=2), K(a=R, ev=['HitOff', 'End'])], 11, False)
    elif k in ('staff',):
        P['PrepareAttack'] = ([K(a=R, sq=1, ev=['Telegraph']), K(a=R - 10, grip=(0, -3), orb=1), K(a=R - 10, grip=(0, -4), orb=2)], 9, False)
        P['Attack'] = ([K(a=80, grip=(2, -1), dx=1, orb=3, ev=['HitOn', 'Projectile']), K(a=85, grip=(2, 0), dx=1, spark=1), K(a=85, grip=(1, 0), ev=['HitOff'])], 11, False)
        P['AttackRecovery'] = ([K(a=70), K(a=(70 + R) / 2), K(a=R, ev=['End'])], 9, False)
        P['HeavyAttack'] = ([K(a=R, sq=1, ev=['Telegraph']), K(a=0, grip=(0, -4), orb=1, fx=['runes']), K(a=0, grip=(0, -5), orb=2, fx=['runes']),
                             K(a=0, grip=(0, -5), orb=3, fx=['runes']), K(a=150, sq=2, fx=['ring', 'ring2'], ev=['HitOn']), K(a=150, sq=1, fx=['ring2'], ev=['HitOff']),
                             K(a=R, ev=['End'])], 10, False)
        P['SpecialAttack'] = ([K(a=R, sq=1, ev=['Telegraph']), K(a=R - 10, grip=(0, -3), orb=2), K(a=80, grip=(2, -1), orb=3, ev=['Projectile']),
                               K(a=85, spark=1), K(a=R, ev=['End'])], 10, False)
    elif k in ('bow', 'crossbow'):
        P['PrepareAttack'] = ([K(a=R, sq=1, ev=['Telegraph']), K(a=R, draw=1, grip=(-1, 0)), K(a=R, draw=2, grip=(-1, 0), glint=1)], 9, False)
        P['Attack'] = ([K(a=R, draw=0, grip=(-2, 0), dx=-1, spark=1, ev=['HitOn', 'Projectile']), K(a=R, grip=(-1, 0), dx=-1), K(a=R, ev=['HitOff'])], 12, False)
        P['AttackRecovery'] = ([K(a=R, sq=1), K(a=R), K(a=R, ev=['End'])], 9, False)
        P['HeavyAttack'] = ([K(a=R, sq=1, ev=['Telegraph']), K(a=R, draw=1), K(a=R, draw=2, glint=1), K(a=R, draw=2, glint=1),
                             K(a=R, grip=(-2, 0), dx=-2, spark=1, ev=['HitOn', 'Projectile']), K(a=R, dx=-1, ev=['HitOff']), K(a=R, ev=['End'])], 10, False)
        P['SpecialAttack'] = ([K(a=R, sq=1, ev=['Telegraph']), K(a=R, draw=1), K(a=R, draw=2), K(a=R, grip=(-2, 0), dx=-1, spark=1, ev=['Projectile']),
                               K(a=R, ev=['End'])], 11, False)
    elif k in ('shield', 'shieldbash'):
        P['PrepareAttack'] = ([K(a=R, sq=1, ev=['Telegraph']), K(a=R, lean=-1, dx=-1, wgrip=(-2, 0)), K(a=R, lean=-1, dx=-2, wgrip=(-3, 0), glint=1)], 9, False)
        P['Attack'] = ([K(a=R, lean=2, dx=4, wgrip=(13, 0), front=1, impact=1, ev=['HitOn']), K(a=R, lean=1, dx=4, wgrip=(13, 0), front=1),
                        K(a=R, dx=3, wgrip=(9, 0), front=1, ev=['HitOff'])], 12, False)
        P['AttackRecovery'] = ([K(a=R, dx=2, wgrip=(3, 0)), K(a=R, dx=1), K(a=R, ev=['End'])], 9, False)
        P['HeavyAttack'] = ([K(a=R, sq=2, ev=['Telegraph']), K(a=R, sq=2, dx=-2, glint=1), K(a=R, lean=2, dx=6, wgrip=(14, 0), front=1, ghost=1, ev=['HitOn']),
                             K(a=R, dx=6, wgrip=(14, 0), front=1, fx=['ring', 'dust'], impact=1), K(a=R, dx=5, wgrip=(5, 0), ev=['HitOff']), K(a=R, dx=3, ev=['End'])], 11, False)
        P['SpecialAttack'] = P['HeavyAttack']
    else:   # unarmed: claws, bites, body slams, whips
        P['PrepareAttack'] = ([K(sq=1, ev=['Telegraph']), K(lean=-1, dx=-1, sq=1), K(lean=-2, dx=-2, glint=1)], 10, False)
        P['Attack'] = ([K(lean=2, dx=4, claw=k, ev=['HitOn']), K(lean=2, dx=4, claw=k, fade=1), K(lean=1, dx=3, ev=['HitOff'])], 12, False)
        P['AttackRecovery'] = ([K(dx=2, sq=1), K(dx=1), K(ev=['End'])], 9, False)
        P['HeavyAttack'] = ([K(sq=2, ev=['Telegraph']), K(st=1, dy=-3), K(dy=-5, glint=1), K(lean=2, dx=5, claw=k, big=1, ev=['HitOn']),
                             K(sq=2, dx=5, fx=['ring', 'dust']), K(dx=5, fx=['ring2'], ev=['HitOff']), K(dx=3, ev=['End'])], 11, False)
        P['SpecialAttack'] = ([K(sq=1, ev=['Telegraph']), K(glowc=1), K(glowc=1, spark=1, ev=['Projectile']), K(lean=1), K(ev=['End'])], 10, False)
    P['CastSpell'] = ([K(a=R if fig.weapon is not None else None, st=1, ev=['Telegraph']), K(a=R, glowc=1, st=1), K(a=R, glowc=1, fx=['ring'], ev=['Projectile']),
                       K(a=R, fx=['ring2']), K(a=R, ev=['End'])], 8, False)
    P['Hurt'] = ([K(a=R + 15, flash=1), K(a=R + 25, dx=-1, tint=1), K(a=R)], 12, False)
    guard = (20 if k in SWING else 60 if k in THRUST else R)
    P['Block'] = ([K(a=guard, sq=1, wgrip=(3, 0) if k.startswith('shield') else (0, 0), front=1), K(a=guard, sq=1, wgrip=(3, 0) if k.startswith('shield') else (0, 0), front=1)], 10, False)
    P['BlockHit'] = ([K(a=guard + 10, sq=1, dx=-1, wgrip=(3, 0) if k.startswith('shield') else (0, 0), front=1, spark=1), K(a=guard, sq=1, front=1)], 12, False)
    P['Dodge'] = ([K(a=R, sq=1), K(a=R + 10, dx=-3, lean=-1, ghost=1, dy=-1), K(a=R + 10, dx=-5, lean=-1, ghost=1), K(a=R, dx=-5, sq=1), K(a=R, dx=-5)], 14, False)
    P['Death'] = ([K(a=R, flash=1), K(a=R + 30, lean=-2, sq=2, drop=0), K(a=None, sq=4, dy=1, drop=1), K(a=None, sq=4, dy=1, drop=1, fadek=.3),
                   K(a=None, sq=4, dy=1, drop=1, fadek=.6), K(a=None, sq=4, dy=1, drop=1, fadek=.9)], 8, False)
    for clip, (kfs, fps, loop) in P.items():
        for kf in kfs:
            if 'a' not in kf:
                kf['a'] = R if fig.weapon is not None else None
    return P


# ------------------------------------------------------------------ rendering
def view_angle(a, view):
    if a is None:
        return None
    if view == 'Right':
        return a
    m = abs(a)
    v = 2 * m if m <= 90 else 180 + (m - 90) * .5
    v = v if a >= 0 else -v
    return v if view == 'Down' else 180 - v


AIMED = {'PrepareAttack', 'Attack', 'AttackRecovery', 'HeavyAttack', 'SpecialAttack', 'Block', 'BlockHit'}


def render(fig, kf, view, clip='Attack'):
    body = fig.body
    if kf.get('legs'):
        body = RO.legs(body, kf['legs'])
    if kf.get('sq'):
        body = squash(body, kf['sq'])
    if kf.get('st'):
        body = stretch(body, kf['st'])
    if kf.get('lean'):
        body = lean(body, kf['lean'])
    a = kf.get('a')
    layers_b, layers_f = [], []
    tipxy = None
    if fig.weapon is not None and a is not None and kf.get('drop') is None:
        gx, gy = fig.grip
        dg = kf.get('grip', (0, 0))
        wg = kf.get('wgrip', (0, 0))
        if view == 'Right':
            g = (gx + dg[0] + wg[0], gy + dg[1] + wg[1])
        else:      # front/back: forward motion of the hand becomes down/up
            s = 1 if view == 'Down' else -1
            g = (gx + wg[0] // 2, gy + dg[1] + s * (dg[0] + wg[0]) // 2)
        if kf.get('sq') and g[1] < bbox(fig.body)[1] + fig.h * 2 // 3:
            g = (g[0], g[1] + kf['sq'])
        if fig.kind.startswith('shield'):
            av = fig.rest                                        # the shield is never turned, only pushed
        elif clip not in AIMED or abs(a - fig.rest) < 1:
            av = a                                               # carried as drawn: the body is the side drawing
        else:
            av = view_angle(a, view)
        if kf.get('draw') and fig.kind in ('bow', 'crossbow'):
            pass
        wl = fig.weapon_at(av, g)
        if kf.get('orb') or kf.get('glowc'):
            wl = X.glow(wl, fig.col)
        tipxy = fig.tip(av, g)
        if kf.get('behind') or (view == 'Up' and not kf.get('front')) or (fig.kind == 'scythe' and view == 'Right' and av % 360 > 200):
            layers_b.append(wl)
        else:
            layers_f.append(wl)
        if not fig.kind.startswith('shield') and fig.hand_cols:
            layers_f.append(('hand', g))
        if kf.get('draw') and fig.kind == 'bow':
            pull = (0, 2, 4)[kf['draw']]
            ar = WA.pose('arrow', 90 if view == 'Right' else (180 if view == 'Down' else 0), g[0] - 3 - pull, g[1]) if view == 'Right' else \
                WA.pose('arrow', 180 if view == 'Down' else 0, g[0], g[1] - (3 + pull) * (1 if view == 'Down' else -1))
            layers_f.append(ar)
        if kf.get('draw') and fig.kind == 'crossbow':
            layers_f.append(WA.pose('bolt', 90 if view == 'Right' else (180 if view == 'Down' else 0), g[0] + 1, g[1] - 1))
    out = blank()
    for l in layers_b:
        out = over(out, l)
    out = over(out, body)
    for l in layers_f:
        if isinstance(l, tuple):
            out = WA.hand(out, l[1][0] - 1, l[1][1] - 1, fig.hand_cols)
        else:
            out = over(out, l)
    # effects
    col = fig.col
    trail_cols = (WA.SLASH, WA.SLASH2, WA.SLASH3) if col in (X.SLASH,) else (col, WA.SLASH2, WA.SLASH3)
    if kf.get('trail') and fig.weapon is not None:
        t0, t1 = kf['trail'][0], kf['trail'][1]
        fade = 'fade' in kf['trail'][2:]
        big = 'big' in kf['trail'][2:]
        g = fig.grip
        ro = fig.length + (2 if big else 1); ri = max(3, ro - (7 if big else 5))
        if view == 'Right':
            out = WA.trail(out, g[0], g[1], ri, ro, t0, t1, trail_cols, fade, behind=True)
        else:
            out = WA.trail(out, g[0], g[1], ri, ro, view_angle(t0, view), view_angle(t1, view), trail_cols, fade, ry=.75, behind=True)
    if kf.get('thrust') and tipxy is not None:
        tx, ty = int(round(tipxy[0])), int(round(tipxy[1]))
        L = 6 + 3 * kf['thrust']
        if view == 'Right':
            out = WA.thrust_lines(out, tx - 2, tx - 2 - L, ty)
        elif view == 'Down':
            out = WA.vthrust_lines(out, tx, ty - 2, ty - 2 - L)
        else:
            out = WA.vthrust_lines(out, tx, ty + 2, ty + 2 + L)
    if kf.get('claw'):
        out = claw_fx(out, fig, kf, view)
    if kf.get('impact'):
        x = int(fig.cx + fig.h * .5) if view == 'Right' else int(fig.cx)
        out = X.sparkle(out, x + 4, FEET - fig.h // 2, 2, X.WHT, X.YEL)
    if kf.get('orb') and tipxy is not None:
        r = kf['orb']
        out = X.orb(out, tipxy[0], tipxy[1], 1 + r * .7, [col, X.WHT][:1 + (r > 1)])
    if kf.get('spark') and tipxy is not None:
        out = X.sparkle(out, int(tipxy[0]), int(tipxy[1]), 2, X.WHT, col)
    if kf.get('glint'):
        if tipxy is not None:
            out = X.sparkle(out, int(tipxy[0]), int(tipxy[1]), 1, X.WHT, X.WHT)
        else:
            b = bbox(out)
            out = X.sparkle(out, (b[0] + b[2]) // 2 + 4, b[1] + 3, 1, X.WHT, X.WHT)
    if kf.get('glowc'):
        out = X.glow(out, col)
    for fx in kf.get('fx', []):
        cx = int(fig.cx) + (6 if view == 'Right' else 0)
        cy = FEET - 1 + (5 if view == 'Down' else -5 if view == 'Up' else 0)
        if fx == 'ring': out = X.ring(out, cx, cy, 9, X.DUST)
        elif fx == 'ring2': out = X.ring(out, cx, cy, 13, X.DUST2)
        elif fx == 'dust': out = X.dust(out, int(fig.cx) - 4, FEET - 1, 1, side=-1)
        elif fx == 'runes':
            out = X.ring(out, int(fig.cx), FEET - 1, 11, col)
    if kf.get('flash'):
        out = RO.tint(out, X.WHT, .8)
    if kf.get('tint'):
        out = RO.tint(out, X.RED, .45)
    if kf.get('drop') is not None and fig.weapon is not None:
        wl = fig.weapon_at(95 if view != 'Up' else 85, (int(fig.cx) + 6, FEET - 2))
        out = over(wl, out) if view == 'Up' else over(out, wl)
    # whole-figure motion
    dx, dy = kf.get('dx', 0), kf.get('dy', 0)
    if view == 'Right':
        out = shift(out, dx, dy)
    else:
        s = 1 if view == 'Down' else -1
        out = shift(out, 0, dy + s * max(-2, min(2, dx)))
    if kf.get('ghost'):
        gd = (-3, 0) if view == 'Right' else (0, -3 if view == 'Down' else 3)
        out = X.afterimage(out, shift(out, *gd), .3)
    if kf.get('fadek'):
        out = RO.fade(out, kf['fadek'])
    return out


def claw_fx(f, fig, kf, view):
    """three claw rakes / a bite flash / a body-slam ring in front of the creature"""
    k = kf['claw']
    out = f.copy()
    b = bbox(fig.body)
    big = kf.get('big')
    col = WA.SLASH3 if kf.get('fade') else WA.SLASH
    if view == 'Right':
        x0, y0 = b[2] + 1, b[1] + fig.h // 3
    elif view == 'Down':
        x0, y0 = int(fig.cx) - 3, b[3] - 2
    else:
        x0, y0 = int(fig.cx) - 3, b[1] - 3
    if k in ('claw', 'whip'):
        n = 3 if k == 'claw' else 1
        L = 6 + (3 if big else 0)
        for i in range(n):
            for t in range(L):
                if view == 'Right':
                    X.px(out, x0 + t // 2 + i * 2, y0 + t + i, col)
                else:
                    X.px(out, x0 + t + i, y0 + (t // 2 + i * 2) * (1 if view == 'Down' else -1), col)
    elif k == 'bite':
        for t in range(5):
            X.px(out, x0 + (t if view == 'Right' else t - 2), y0 + 2 + (0 if t % 2 else 1), WA.SLASH)
            X.px(out, x0 + (t if view == 'Right' else t - 2), y0 + 6 - (0 if t % 2 else 1), WA.SLASH)
    elif k in ('slam', 'body'):
        out = X.ring(out, int(fig.cx) + (5 if view == 'Right' else 0), FEET - 1, 9 + (4 if big else 0), X.DUST)
    return out


# ------------------------------------------------------------------ output
CAT = {'Idle': 'Idle', 'Walk': 'Walk', 'Run': 'Walk', 'PrepareAttack': 'Attack', 'Attack': 'Attack', 'AttackRecovery': 'Attack',
       'HeavyAttack': 'Attack', 'SpecialAttack': 'Special', 'CastSpell': 'Special', 'Hurt': 'Hurt', 'Block': 'Combat', 'BlockHit': 'Combat',
       'Dodge': 'Dodge', 'Death': 'Death'}


def build(name):
    fig = Fig(name)
    P = plan(fig)
    root = os.path.join(OUT, name)
    clips = []
    data = {}
    for clip, (kfs, fps, loop) in P.items():
        ev = [dict(frame=i, fn='AnimEvent', arg=e) for i, kf in enumerate(kfs) for e in kf.get('ev', [])]
        right = [render(fig, kf, 'Right', clip) for kf in kfs]
        views = {'Right': right, 'Left': [flip(f) for f in right], 'Down': [render(fig, kf, 'Down', clip) for kf in kfs],
                 'Up': [render(fig, kf, 'Up', clip) for kf in kfs]}
        for d, frames in views.items():
            uniq, seq = RO.dedupe(frames)
            rel = f'{CAT[clip]}/{name}_{clip}_{d}.png'
            save_sheet(uniq, os.path.join(root, rel))
            clips.append(dict(name=clip, dir=d, file=rel, frames=len(uniq), seq=seq, fps=fps, loop=loop,
                              size=[CELL * len(uniq), CELL], events=ev))
            data[(clip, d)] = (frames, fps, loop, ev)
    # reach of the weapon at the impact frame, measured from the body centre (px) -> hitbox data in Unity
    reach = (getattr(fig, 'length', 0) + abs(fig.grip[0] - fig.cx) + 2) if fig.weapon is not None else fig.h * .6 + 4
    with open(os.path.join(root, f'{name}_animations.json'), 'w') as fh:
        json.dump(dict(character=name, cell=CELL, pivot=[0.5, (CELL - FEET) / CELL], ppu=16, weapon=fig.kind,
                       reach_px=round(float(reach), 1), body_px=int(fig.h), clips=clips), fh, indent=1)
    return fig, data


def page(datas, path, clips=('Idle', 'PrepareAttack', 'Attack', 'AttackRecovery', 'HeavyAttack'), dirs=('Right', 'Down', 'Up')):
    """review sheet: one row per figure x direction, frames of the attack chain side by side"""
    from PIL import ImageDraw
    rows = [(n, d) for n in datas for d in dirs]
    x0, y0, x1, y1 = 4, 12, 60, 62
    k = 3
    cw, ch = (x1 - x0) * k, (y1 - y0) * k
    ncol = sum(1 for c in clips for _ in datas[next(iter(datas))].get((c, 'Right'), ([],))[0]) + len(clips)
    im = Image.new('RGBA', (120 + ncol * (cw + 1), len(rows) * (ch + 1)), (40, 48, 44, 255))
    dr = ImageDraw.Draw(im)
    for r, (n, d) in enumerate(rows):
        dr.text((4, r * (ch + 1) + 4), f'{n}\n{d}', fill=(255, 255, 255, 255))
        c = 0
        for clip in clips:
            frames = datas[n].get((clip, d), ([],))[0]
            for f in frames:
                cell = Image.fromarray(f[y0:y1, x0:x1], 'RGBA').resize((cw, ch), Image.NEAREST)
                bg = Image.new('RGBA', (cw, ch), (96, 120, 96, 255) if clip in ('Attack', 'Idle', 'HeavyAttack') else (84, 104, 88, 255))
                bg.alpha_composite(cell)
                im.paste(bg, (120 + c * (cw + 1), r * (ch + 1)))
                c += 1
            c += 1
    im.save(path)


if __name__ == '__main__':
    names = sys.argv[1:] or list(RO.ROSTER)
    docs = os.path.join(ROOT, 'Documentation', 'CombatAnimations')
    os.makedirs(docs, exist_ok=True)
    datas = {}
    for n in names:
        fig, data = build(n)
        datas[n] = data
        print(n, fig.kind, 'grounded' if fig._dy else '')
    if len(names) > 1:
        keys = list(datas)
        for i in range(0, len(keys), 6):
            page({k: datas[k] for k in keys[i:i + 6]}, os.path.join(docs, f'enemies_{i // 6 + 1}.png'))
