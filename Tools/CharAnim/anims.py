"""Builds every animation for one character.

Right  = original frames whenever they exist (or derived from them)
Left   = exact mirror of Right
Down/Up = hand-drawn rigs (designs.py) animated with the same timing language
Sheets store UNIQUE frames only; holds/repeats live in the clip's frame sequence.
"""
import numpy as np
from engine import *
from source import Source
from rigs import RIGS
import designs as D
import fxdraw as X

SIDE = ('Right', 'Left')
DIRS = ('Down', 'Up', 'Left', 'Right')


class Anim:
    def __init__(self, cat, frames, fps=10, loop=True, seq=None):
        self.cat, self.frames, self.fps, self.loop = cat, frames, fps, loop
        self.seq = seq if seq is not None else list(range(len(frames)))


def dedupe(frames, seq=None):
    """drop byte-identical frames, rewriting the sequence"""
    seq = seq if seq is not None else list(range(len(frames)))
    uniq, remap = [], {}
    for i, f in enumerate(frames):
        for j, u in enumerate(uniq):
            if np.array_equal(f, u):
                remap[i] = j; break
        else:
            remap[i] = len(uniq); uniq.append(f)
    return uniq, [remap[i] for i in seq]


# weapon / pose choices per character (all from the ORIGINAL strips)
CFG = {
    'Soldier': dict(attack='Attack01', heavy='Attack02', special='Attack03', guard=('Attack01', 1),
                    raised=('Attack01', 1), extras=['Interact', 'PickUp', 'Push', 'Pull', 'Climb', 'Swim', 'Sit', 'Sleep', 'ChargeEnergy'],
                    w_up=D.SOLDIER_SWORD_UP, w_down=D.SOLDIER_SWORD_DOWN, glow=X.YEL),
    'Orc': dict(attack='Attack01', heavy='Attack02', special=None, guard=('Attack01', 1), raised=('Attack02', 1),
                extras=['Sit', 'Sleep', 'ChargeEnergy'], w_up=D.ORC_AXE_UP, w_down=D.ORC_AXE_DOWN, glow=X.RED),
    'Demon': dict(attack='Attack01', heavy='Attack02', special=None, guard=('Attack02', 1), raised=('Attack02', 1),
                  extras=['CastSpell', 'Sleep', 'ChargeEnergy'], w_up=D.DEMON_BLADE_UP, w_down=D.DEMON_BLADE_DOWN, glow=X.PUR),
    'BloodMonster': dict(attack='Attack01', heavy=None, special='Attack02', guard=None, raised=('Attack01', 3),
                         extras=['Sleep', 'ChargeEnergy'], w_up=None, w_down=None, glow=X.BLD2),
}


class Builder:
    def __init__(self, key):
        self.key = key
        self.s = Source(key)
        self.r = RIGS[key]
        self.c = CFG[key]
        self.out = {}
        self.hurt = self.s.hurt_maps()

    # ----------------------------------------------------------- helpers
    def add(self, name, d, anim):
        frames, seq = dedupe(anim.frames, anim.seq)
        anim.frames, anim.seq = frames, seq
        self.out[(name, d)] = anim

    def add_side(self, name, cat, frames_r, fps=10, loop=True, seq=None):
        self.add(name, 'Right', Anim(cat, frames_r, fps, loop, seq))
        self.add(name, 'Left', Anim(cat, [flip(f) for f in frames_r], fps, loop, seq))

    def body(self, anim, i):
        return self.s.body(anim, i)

    def sh(self, body, h=0):
        return self.s.with_shadow(body, h)

    def full(self, anim, i):
        return self.s.anims[anim][i]

    def rig(self, view, **kw):
        return self.sh(self.r.frame(view, **kw))

    def rig_body(self, view, **kw):
        return self.r.frame(view, **kw)

    def weapon(self, f, spr, view, dx=0, dy=0, behind=False, feet=FEET):
        w = place(ascii_sprite(spr, self.r.pal), dx=dx, dy=dy, feet=feet)
        return over(w, f) if behind else over(f, w)

    def hurt_frames(self, base_body, recoil=(0, 0)):
        (m1, g1), (m2, g2) = self.hurt
        f0 = shift(base_body, *recoil)
        f1 = recolor(f0, m1)
        if g1: f1 = outline(f1, g1 + (255,) if len(g1) == 3 else g1)
        f2 = recolor(shift(base_body, recoil[0] // 2, recoil[1] // 2), m2)
        return [self.sh(f0), self.sh(f1), self.sh(f2), self.sh(base_body)]

    # ========================================================= directional
    def build_idle(self):
        self.add_side('Idle', 'Idle', self.s.anims['Idle'], fps=8)
        for v in ('Down', 'Up'):
            base = self.rig(v)
            breath = self.sh(squash(self.r.frame(v), 1))
            frames = [base, breath]
            seq = [0, 0, 1, 1]
            if v == 'Down':
                blink = self.sh(self._blink(self.r.frame(v)))
                frames.append(blink)
                seq = [0, 0, 1, 1, 0, 2]
            self.add('Idle', v, Anim('Idle', frames, 8, True, seq))

    def _blink(self, f):
        """close the eyes for one frame (eye colours -> darkest skin/outline tone of the same character)"""
        eyes = {'Soldier': ['#ffffff', '#621914'], 'Orc': ['#7b0808', '#d7d5d2'], 'Demon': ['#d79970'], 'BloodMonster': []}[self.key]
        lid = {'Soldier': (0x1f, 0x1a, 0x1a), 'Orc': (0x42, 0x59, 0x16), 'Demon': (0x7e, 0x22, 0x2a), 'BloodMonster': (0, 0, 0)}[self.key]
        m = {hx(e)[:3]: lid for e in eyes}
        b = bbox(f)
        g = f.copy()
        top = b[1]
        g[top:top + 12] = recolor(f, m)[top:top + 12]
        return g

    def build_walk(self):
        self.add_side('Walk', 'Walk', self.s.anims['Walk'], fps=10)
        for v in ('Down', 'Up'):
            A = self.rig(v, legs='A', swing=1)
            Asq = self.sh(squash(self.r.frame(v, legs='A', swing=1), 1))
            P = self.rig(v, bob=-1)
            B = self.rig(v, legs='B', swing=-1)
            Bsq = self.sh(squash(self.r.frame(v, legs='B', swing=-1), 1))
            self.add('Walk', v, Anim('Walk', [A, Asq, P, B, Bsq], 10, True, [0, 1, 2, 3, 4, 2]))

    def build_run(self):
        # side: original walk cycle + forward lean, higher bounce and dust on each contact
        fr = []
        bob = [0, -1, -2, -1, 0, -1, -2, -1]
        for i, f in enumerate(self.s.anims['Walk']):
            body, _ = self.s.split(f)
            body = shift(lean(body, 1), 0, bob[i])
            g = self.sh(body, -bob[i])
            if i in (0, 4):
                g = X.dust(g, 24, FEET, 1, side=-1)
            elif i in (1, 5):
                g = X.dust(g, 22, FEET - 1, 2, side=-1)
            fr.append(g)
        self.add_side('Run', 'Run', fr, fps=14)
        for v in ('Down', 'Up'):
            A = self.sh(squash(self.r.frame(v, legs='A', swing=2), 1))
            Au = self.sh(self.r.frame(v, legs='stand', swing=1, bob=-2), 2)
            B = self.sh(squash(self.r.frame(v, legs='B', swing=-2), 1))
            Bu = self.sh(self.r.frame(v, legs='stand', swing=-1, bob=-2), 2)
            dy = -1 if v == 'Down' else 1
            A = X.dust(A, 28, FEET - 1 + (2 if v == 'Up' else -0), 1)
            B = X.dust(B, 35, FEET - 1 + (2 if v == 'Up' else 0), 1)
            self.add('Run', v, Anim('Run', [A, Au, B, Bu], 12, True))

    # ------------------------------------------------------------ attacks
    def _strike_frames(self, v, heavy=False):
        """front/back melee: anticipation -> strike -> follow-through -> recovery"""
        c = self.c
        down = v == 'Down'
        R = lambda **kw: self.r.frame(v, weapon=False, **kw)
        frames = []
        if c['w_up'] is None:     # Blood Monster: claws
            raise_ = R(swing=-4 if down else 4, squash_rows=1)
            raise_ = self.weapon(raise_, D.BLOOD_CLAW, v, dx=-7, dy=-14)
            strike = R(swing=2 if down else -2)
            cy = 46 if down else 30
            strike = X.arc(strike, 31, cy, 13, 8, 20 if down else 200, 160 if down else 340, ry=.6)
            follow = X.arc(R(swing=1 if down else -1), 31, cy, 12, 9, 70 if down else 250, 160 if down else 340, ry=.6, fade=True)
            frames = [self.sh(R(squash_rows=1)), self.sh(raise_), self.sh(strike), self.sh(follow), self.sh(R())]
            if heavy:
                big = R(squash_rows=2, swing=-3 if down else 3)
                big = self.weapon(big, D.BLOOD_CLAW, v, dx=-7, dy=-12)
                big = self.weapon(big, [r[::-1] for r in D.BLOOD_CLAW], v, dx=7, dy=-12)
                jump = shift(big, 0, -4)
                slam = X.arc(R(squash_rows=1), 31, cy, 15, 9, 0 if down else 180, 180 if down else 360, ry=.6)
                slam = X.ring(slam, 31, FEET - 1, 10, X.DUST)
                frames = [self.sh(R(squash_rows=2)), self.sh(big), self.sh(jump, 4), self.sh(slam),
                          self.sh(X.ring(R(squash_rows=1), 31, FEET - 1, 13, X.DUST2)), self.sh(R())]
            return frames
        up, dn = c['w_up'], c['w_down']
        h = self.r.h - self.r.body_dy           # visual height -> weapon heights scale per character
        rx = {'Soldier': 4, 'Orc': 5, 'Demon': 7}[self.key]
        wh = len(up)
        hand_dy = -12           # hands at chest height
        if down:
            ant = self.weapon(R(squash_rows=1), up, v, dx=rx, dy=-(h - 4), behind=True)
            wind = self.weapon(R(stretch_rows=1), up, v, dx=rx, dy=-(h - 1), behind=True)
            strike = self.weapon(R(), dn, v, dx=3, dy=4)
            strike = X.arc(strike, 31, 44, 14, 9, 15, 165, ry=.55)
            follow = self.weapon(R(squash_rows=1), dn, v, dx=2, dy=5)
            follow = X.arc(follow, 31, 44, 13, 10, 70, 165, ry=.55, fade=True)
            rec = self.weapon(R(), dn, v, dx=3, dy=0)
        else:
            ant = self.weapon(R(squash_rows=1), dn, v, dx=6, dy=2, behind=True)
            wind = self.weapon(R(stretch_rows=1), up, v, dx=rx - 1, dy=-(h - 6))
            strike = self.weapon(R(), up, v, dx=1, dy=-(h + 2))
            strike = X.arc(strike, 31, 34, 14, 9, 195, 345, ry=.55)
            follow = self.weapon(R(squash_rows=1), up, v, dx=1, dy=-h)
            follow = X.arc(follow, 31, 34, 13, 10, 250, 345, ry=.55, fade=True)
            rec = self.weapon(R(), dn, v, dx=6, dy=0, behind=True)
        base = self.r.frame(v)
        if not heavy:
            return [self.sh(ant), self.sh(wind), self.sh(strike), self.sh(follow), self.sh(rec), self.sh(base)]
        # heavy: deep crouch, jump, slam with shock ring
        crouch = self.weapon(R(squash_rows=2), up, v, dx=rx, dy=-(h - 6) if down else -(h - 4), behind=down)
        jump = shift(self.weapon(R(stretch_rows=1), up, v, dx=rx, dy=-h if down else -(h - 2), behind=down), 0, -4)
        apex = shift(self.weapon(R(), up, v, dx=rx, dy=-(h + 1) if down else -h, behind=down), 0, -6)
        if down:
            slam = self.weapon(R(squash_rows=1), dn, v, dx=3, dy=5)
            slam = X.arc(slam, 31, 44, 16, 9, 0, 180, ry=.55)
        else:
            slam = self.weapon(R(squash_rows=1), up, v, dx=1, dy=-(h + 1))
            slam = X.arc(slam, 31, 34, 16, 9, 180, 360, ry=.55)
        impact = X.ring(slam, 31, FEET - 1, 11, X.DUST)
        settle = X.ring(self.weapon(R(squash_rows=1), dn if down else up, v, dx=3 if down else 1, dy=5 if down else -h), 31, FEET - 1, 14, X.DUST2)
        return [self.sh(crouch), self.sh(crouch if False else X.sparkle(crouch, 35, 22 if down else 24, 1)),
                self.sh(jump, 4), self.sh(apex, 6), self.sh(impact), self.sh(settle), self.sh(base)]

    def build_attacks(self):
        c = self.c
        # basic
        self.add_side('Attack', 'Attack', self.s.anims[c['attack']], fps=12, loop=False)
        for v in ('Down', 'Up'):
            self.add('Attack', v, Anim('Attack', self._strike_frames(v), 12, False))
        # heavy
        if c['heavy']:
            self.add_side('HeavyAttack', 'Attack', self.s.anims[c['heavy']], fps=11, loop=False)
        else:
            self.add_side('HeavyAttack', 'Attack', self._side_heavy_derived(), fps=11, loop=False)
        for v in ('Down', 'Up'):
            self.add('HeavyAttack', v, Anim('Attack', self._strike_frames(v, heavy=True), 11, False))
        # special
        self.build_special()

    def _side_heavy_derived(self):
        """Blood Monster has no second melee: body-slam built from its claw swipe"""
        a = self.s.anims['Attack01']
        crouch = squash(a[1], 2)
        leap = shift(stretch(a[2], 1), 2, -4)
        slam = X.ring(squash(a[4], 1), 34, FEET - 1, 10, X.DUST)
        return [squash(a[0], 1), crouch, leap, shift(a[3], 3, -5), slam, X.ring(a[5], 34, FEET - 1, 13, X.DUST2), a[6], a[7]]

    def build_special(self):
        k = self.key
        if k == 'Soldier':
            self.add_side('SpecialAttack', 'Special', self.s.anims['Attack03'], fps=12, loop=False)
            for v in ('Down', 'Up'):
                self.add('SpecialAttack', v, Anim('Special', self._bow(v), 12, False))
        elif k == 'Orc':      # ground slam with shockwave
            a = self.s.anims['Attack02']
            fr = [a[0], a[1], a[2], X.ring(a[3], 40, FEET - 1, 9, X.DUST), X.ring(X.ring(a[4], 40, FEET - 1, 13, X.DUST), 40, FEET - 1, 7, X.DUST2), X.ring(a[5], 40, FEET - 1, 16, X.DUST2), a[5]]
            self.add_side('SpecialAttack', 'Special', fr, fps=11, loop=False)
            for v in ('Down', 'Up'):
                hv = self._strike_frames(v, heavy=True)
                hv[4] = X.ring(hv[4], 31, FEET - 1, 17, X.DUST2)
                hv[5] = X.ring(hv[5], 31, FEET - 1, 20, X.DUST2)
                self.add('SpecialAttack', v, Anim('Special', hv, 11, False))
        elif k == 'Demon':    # hellfire orb
            raised = self.s.anims['Attack02'][1]
            fr = [self.s.anims['Idle'][0], raised]
            for i, r in enumerate((2, 3, 4)):
                fr.append(X.orb(raised, 28, 22, r, [X.PUR, X.BLD2, X.ORA, X.YEL][:2 + i]))
            fr.append(X.orb(self.s.anims['Attack01'][4], 48, 46, 3, [X.PUR, X.BLD2, X.ORA, X.YEL]))
            fr.append(X.orb(self.s.anims['Attack01'][5], 58, 46, 2, [X.BLD2, X.ORA]))
            fr.append(self.s.anims['Attack01'][6])
            self.add_side('SpecialAttack', 'Special', fr, fps=11, loop=False)
            for v in ('Down', 'Up'):
                down = v == 'Down'
                R = lambda **kw: self.r.frame(v, weapon=False, **kw)
                up_blade = lambda f, dy=-15: self.weapon(f, D.DEMON_BLADE_UP, v, dx=0, dy=dy, behind=down)
                oy = 18 if down else 18
                seq = [self.r.frame(v), up_blade(R(squash_rows=1))]
                for i, r in enumerate((2, 3, 4)):
                    seq.append(X.orb(up_blade(R()), 31, oy, r, [X.PUR, X.BLD2, X.ORA, X.YEL][:2 + i]))
                ty = (56 if down else 10)
                seq.append(X.orb(self.weapon(R(squash_rows=1), D.DEMON_BLADE_DOWN if down else D.DEMON_BLADE_UP, v, dx=0, dy=2 if down else -17), 31, ty, 3, [X.PUR, X.BLD2, X.ORA, X.YEL]))
                seq.append(self.r.frame(v))
                self.add('SpecialAttack', v, Anim('Special', [self.sh(f) for f in seq], 11, False))
        else:                 # Blood Monster: blood spit (Attack02 is the original spit)
            self.add_side('SpecialAttack', 'Special', self.s.anims['Attack02'], fps=11, loop=False)
            for v in ('Down', 'Up'):
                down = v == 'Down'
                R = lambda **kw: self.r.frame(v, **kw)
                inhale = stretch(R(), 1)
                if down:   # open the vertical mouth wide
                    gape = self._gape(R())
                else:
                    gape = squash(R(), 1)
                fr = [R(squash_rows=1), inhale, gape]
                for i, (y, r) in enumerate([(53, 2.5), (58, 2.5), (62, 1.5)] if down else [(28, 2.5), (21, 2.5), (14, 1.5)]):
                    g = gape if i == 0 else R(squash_rows=1)
                    fr.append(X.orb(g, 31, y, r, [X.SLASH3, X.SLASH, X.WHT]))
                fr.append(R())
                self.add('SpecialAttack', v, Anim('Special', fr, 11, False))

    def _gape(self, f):
        g = f.copy()
        dark = hx('#311339')
        b = bbox(f)
        for y in range(b[1] + 2, b[1] + 9):
            for x in (29, 33):
                if g[y, x, 3]:
                    g[y, x] = dark
        return g

    def _bow(self, v):
        down = v == 'Down'
        R = lambda **kw: self.r.frame(v, **kw)
        bow = D.SOLDIER_BOW_H if down else D.SOLDIER_BOW_H[::-1]
        arrow = D.SOLDIER_ARROW_V[::-1] if down else D.SOLDIER_ARROW_V
        by = -7 if down else -17
        draw = self.weapon(R(), bow, v, dy=by + 2, behind=not down)
        aim = self.weapon(R(squash_rows=1), bow, v, dy=by, behind=not down)
        nock = self.weapon(aim, arrow, v, dy=by + (8 if down else -2), behind=not down)
        frames = [R(), draw, aim, nock]
        rel = self.weapon(R(), bow, v, dy=by, behind=not down)
        for i, d in enumerate((5, 9)):
            f = self.weapon(rel, arrow, v, dy=by + (8 + d if down else -2 - d))
            frames.append(f)
        frames += [self.weapon(R(), bow, v, dy=by + 2, behind=not down), R()]
        return [self.sh(f) for f in frames]

    # ------------------------------------------------------------ hurt
    def build_hurt(self):
        self.add_side('Hurt', 'Hurt', self.s.anims['Hurt'], fps=10, loop=False)
        for v in ('Down', 'Up'):
            self.add('Hurt', v, Anim('Hurt', self.hurt_frames(self.r.frame(v), (0, -1 if v == 'Down' else 1)), 10, False))

    # ===================================================== non-directional
    def build_states(self):
        s, c = self.s, self.c
        idle0 = s.body('Idle', 0)
        H = s.anims['Hurt']
        # Death (original)
        self.add_side('Death', 'Death', s.anims['Death'], fps=8, loop=False)
        # Knockback: flash, recoil leaning back with dust, recover (in place: gameplay moves the transform)
        b1, b2, b3 = s.body('Hurt', 1), s.body('Hurt', 2), s.body('Hurt', 3)
        kb = [self.sh(shift(b1, -1, 0)), self.sh(lean(shift(b2, -2, 0), -1)),
              X.dust(self.sh(squash(lean(shift(b2, -2, 0), -1), 1)), 38, FEET - 1, 1, side=1),
              X.dust(self.sh(shift(b3, -1, 0)), 40, FEET - 1, 2, side=1), self.sh(idle0)]
        self.add_side('Knockback', 'Combat', kb, fps=12, loop=False)
        # Block
        if c['guard']:
            g = s.body(*c['guard'])
            gb = squash(g, 1)
            blk = [self.sh(g), self.sh(gb), self.sh(X.sparkle(shift(gb, -1, 0), 41, 38, 2)), self.sh(gb), self.sh(idle0)]
        else:
            gb = squash(idle0, 2)
            blk = [self.sh(squash(idle0, 1)), self.sh(gb), self.sh(X.sparkle(shift(gb, -1, 0), 41, 44, 2)), self.sh(gb), self.sh(idle0)]
        self.add_side('Block', 'Combat', blk[:2], fps=10, loop=False)            # raise guard, then hold last frame
        self.add_side('BlockHit', 'Combat', [blk[2], blk[1]], fps=12, loop=False)  # impact while guarding
        # Dodge: quick back-step, afterimages trail where he was
        lb = lean(idle0, -1)
        dg = [self.sh(squash(idle0, 1)), X.afterimage(self.sh(lb), shift(lb, 4, 0), .35),
              X.afterimage(X.afterimage(self.sh(lb), shift(lb, 6, 0), .2), shift(lb, 3, 0), .4),
              self.sh(squash(idle0, 1)), self.sh(idle0)]
        self.add_side('Dodge', 'Dodge', dg, fps=14, loop=False)
        # Roll: tuck, three lossless 90-degree turns, land
        tuck = squash(idle0, 3)
        b = bbox(tuck)
        piv = ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
        lift = FEET - b[3]
        rl = [self.sh(squash(idle0, 1)), self.sh(tuck)]
        for k in (1, 2, 3):
            rf = rot90(tuck, k, piv)
            bb = bbox(rf)
            rl.append(self.sh(shift(rf, 0, FEET - bb[3])))
        rl += [self.sh(squash(idle0, 1)), self.sh(idle0)]
        self.add_side('Roll', 'Dodge', rl, fps=14, loop=False)
        # Jump / Fall / Land (shadow stays on the ground)
        jp = [self.sh(squash(idle0, 2)), self.sh(shift(stretch(idle0, 1), 0, -2), 2),
              self.sh(shift(stretch(idle0, 1), 0, -7), 7), self.sh(shift(idle0, 0, -10), 10)]
        self.add_side('Jump', 'Jump', jp, fps=12, loop=False)
        walk2 = s.body('Walk', 2)
        fl = [self.sh(shift(stretch(walk2, 1), 0, -8), 8), self.sh(shift(stretch(walk2, 1), 0, -4), 4)]
        self.add_side('Fall', 'Jump', fl, fps=10, loop=True)
        ld = [X.dust(self.sh(squash(idle0, 2)), 26, FEET - 1, 1), X.dust(self.sh(squash(idle0, 1)), 25, FEET - 1, 2), self.sh(idle0)]
        self.add_side('Land', 'Jump', ld, fps=12, loop=False)
        # Victory / Defeat
        rz = s.body(*c['raised'])
        vc = [self.sh(idle0), self.sh(squash(rz, 1)), self.sh(shift(rz, 0, -3), 3), self.sh(X.sparkle(shift(rz, 0, -4), 40, 22, 2), 4),
              self.sh(shift(rz, 0, -1), 1), self.sh(X.sparkle(rz, 22, 28, 1))]
        self.add_side('Victory', 'Emote', vc, fps=10, loop=False)
        d1 = s.body('Death', 1)
        df = [self.sh(s.body('Death', 0)), self.sh(d1), self.sh(squash(d1, 1)), self.sh(squash(d1, 2))]
        self.add_side('Defeat', 'Emote', df, fps=7, loop=False)
        # Charged attack: charge loop + release
        ant = s.body(c['heavy'] or c['attack'], 1)
        col = c['glow']
        ch = []
        for t in range(4):
            f = squash(ant, 1) if t % 2 else ant
            f = X.glow(f, col if t % 2 == 0 else X.WHT)
            for k in range(3):
                a = (t * 40 + k * 120) * np.pi / 180
                r = 9 - (t % 2) * 3
                X.px(f, 31 + np.cos(a) * r, 40 + np.sin(a) * r * .7, col)
            ch.append(self.sh(f))
        self.add_side('ChargedAttack_Charge', 'Special', ch, fps=12, loop=True)
        hv = self.out[('HeavyAttack', 'Right')]
        rel_frames = [hv.frames[i] for i in hv.seq[2:]]
        rb, rs = self.s.split(rel_frames[0])
        rel_frames[0] = over(rs, X.glow(rb, col))
        self.add_side('ChargedAttack_Release', 'Special', rel_frames, fps=12, loop=False)
        # Combo: attack -> heavy, trimming wind-up/recovery so the chain flows
        at = self.out[('Attack', 'Right')]
        a_fr = [at.frames[i] for i in at.seq]
        h_fr = [hv.frames[i] for i in hv.seq]
        combo = a_fr[:-1] + h_fr[2:]
        self.add_side('ComboAttack', 'Special', combo, fps=13, loop=False)
        # Critical: heavy with a white impact flash + crit star
        crit = list(h_fr)
        hit = len(crit) // 2
        fb, fs = self.s.split(crit[hit])
        flash = fb.copy()
        lit = (fb[:, :, 3] > 0) & (fb[:, :, :3].sum(axis=2) > 60)   # keep the black outline, light everything else
        flash[lit] = X.WHT
        flash = over(fs, flash)
        crit.insert(hit, flash)
        crit[hit + 1] = X.sparkle(X.sparkle(crit[hit + 1], 46, 34, 3), 50, 42, 2, X.YEL, X.ORA)
        self.add_side('CriticalAttack', 'Special', crit, fps=12, loop=False)

    # ============================================================ extras
    def build_extras(self):
        s = self.s
        idle0 = s.body('Idle', 0)
        for e in self.c['extras']:
            if e == 'Interact':
                fr = [idle0, lean(idle0, 1), X.sparkle(squash(lean(idle0, 1), 1), 42, 40, 1), lean(idle0, 1), idle0]
                self.add_side(e, 'Other', [self.sh(f) for f in fr], 10, False)
            elif e == 'PickUp':
                fr = [idle0, squash(idle0, 1), lean(squash(idle0, 2), 1), lean(squash(idle0, 3), 1),
                      X.sparkle(lean(squash(idle0, 2), 1), 40, 46, 1), squash(idle0, 1), idle0]
                self.add_side(e, 'Other', [self.sh(f) for f in fr], 10, False)
            elif e == 'Push':
                fr = [self.sh(squash(lean(s.body('Walk', i), 2), 1)) for i in range(8)]
                self.add_side(e, 'Other', fr, 7, True)
            elif e == 'Pull':
                fr = [self.sh(lean(s.body('Walk', i), -1)) for i in reversed(range(8))]
                self.add_side(e, 'Other', fr, 7, True)
            elif e == 'Climb':
                R = lambda **kw: self.r.frame('Up', **kw)
                fr = [R(legs='A', swing=-3), R(legs='A', swing=-3, bob=-1), R(legs='B', swing=3), R(legs='B', swing=3, bob=-1)]
                self.add(e, 'Up', Anim('Other', fr, 8, True))
            elif e == 'Swim':
                self._swim()
            elif e == 'Sit':
                fr = [self.sh(squash(idle0, 1)), self.sh(squash(idle0, 3)), self.sh(squash(s.body('Idle', 3), 3))]
                self.add_side(e, 'Other', fr, 6, True, seq=[0, 1, 1, 2, 2, 1])
            elif e == 'Sleep':
                lay = s.body('Death', 3)
                fr = [self.sh(X.zzz(lay if t % 2 == 0 else squash(lay, 1), 36, 36, t)) for t in range(4)]
                self.add_side(e, 'Other', fr, 4, True)
            elif e == 'CastSpell':
                rz = s.body(*self.c['raised'])
                fr = [self.sh(squash(rz, 1))]
                for t in range(4):
                    f = X.orb(rz, 28, 22, 2 + (t % 2), [X.PUR, X.BLD2, X.ORA][:2 + t % 2])
                    f = X.ring(f, 31, FEET - 1, 9 + t, X.PUR if t % 2 else X.BLD2)
                    fr.append(self.sh(f))
                self.add_side(e, 'Other', fr, 10, True, seq=[0, 1, 2, 3, 4])
            elif e == 'ChargeEnergy':
                col = self.c['glow']
                fr = []
                for t in range(4):
                    f = squash(idle0, 1) if t % 2 else idle0
                    f = X.glow(f, col if t in (0, 2) else X.WHT)
                    for k in range(4):
                        a = (t * 30 + k * 90) * np.pi / 180
                        X.px(f, 31 + np.cos(a) * (12 - t * 2), 42 + np.sin(a) * (8 - t), col)
                    fr.append(self.sh(f))
                self.add_side(e, 'Other', fr, 10, True)

    def _swim(self):
        """upper body only, waterline ring + bob (side and front/back)"""
        WL = FEET - 6
        def cut(f, bob):
            g = shift(f, 0, bob).copy()
            g[WL + 1:] = 0
            g = X.ring(g, 31, WL + 1, 7, hx('#78c3e9'), .35)
            return X.ring(g, 31, WL + 1, 9, hx('#bce0f2'), .35)
        side = [cut(self.s.body('Walk', i * 2), (0, 1, 1, 0)[i] + 2) for i in range(4)]
        self.add_side('Swim', 'Other', side, 8, True)
        for v in ('Down', 'Up'):
            fr = [cut(self.r.frame(v, swing=sw), b + 2) for sw, b in ((-3, 0), (0, 1), (3, 1), (0, 0))]
            self.add('Swim', v, Anim('Other', fr, 8, True))


    # ============================================================ top-down: front / back of every side-only state
    def build_vertical(self):
        """The game is seen from above: every state that the packs only drew from the side gets its front (Down) and
        back (Up) version, made with the same hand-drawn rigs as the walk and the attacks - body, arms and the weapon
        in hand move together; nothing is a copy of the side view."""
        for v in ('Down', 'Up'):
            down = v == 'Down'
            R = lambda **kw: self.r.frame(v, **kw)
            base = R()
            back = -1 if down else 1           # pushed / stepping back: away from where you face (screen rows)
            need = lambda n: (n, 'Right') in self.out and (n, v) not in self.out
            b = bbox(base)
            piv = ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)

            def lying(f, k):
                rf = rot90(f, k, piv)
                bb = bbox(rf)
                return shift(rf, 0, FEET - bb[3])
            lie = lying(squash(base, 1), 1 if down else 3)
            if need('Death'):
                h = self.hurt_frames(base, (0, back))
                fr = [h[0], h[1], self.sh(squash(base, 2)), self.sh(squash(base, 4)), self.sh(lie), self.sh(lie)]
                self.add('Death', v, Anim('Death', fr, 8, False))
            if need('Defeat'):
                fr = [self.sh(base), self.sh(squash(base, 1)), self.sh(squash(base, 2)), self.sh(squash(base, 3))]
                self.add('Defeat', v, Anim('Emote', fr, 7, False))
            if need('Knockback'):
                h = self.hurt_frames(base, (0, back))
                fr = [h[0], self.sh(shift(h[1][:, :, :], 0, 0)) if False else h[1],
                      X.dust(self.sh(squash(shift(base, 0, 2 * back), 1)), 31, FEET - 1, 1),
                      X.dust(self.sh(shift(base, 0, back)), 31, FEET - 1, 2), self.sh(base)]
                self.add('Knockback', v, Anim('Combat', fr, 12, False))
            g1, g2 = R(squash_rows=1), R(squash_rows=2)          # guard: crouched behind the weapon in hand
            if need('Block'):
                self.add('Block', v, Anim('Combat', [self.sh(g1), self.sh(g2)], 10, False))
            if need('BlockHit'):
                hit = X.sparkle(shift(g2, 0, back), 31, 40 if down else 30, 2)
                self.add('BlockHit', v, Anim('Combat', [self.sh(hit), self.sh(g2)], 12, False))
            if need('Dodge'):
                fr = [self.sh(squash(base, 1)), X.afterimage(self.sh(base), shift(base, 0, 4 * back), .35),
                      X.afterimage(X.afterimage(self.sh(base), shift(base, 0, 6 * back), .2), shift(base, 0, 3 * back), .4),
                      self.sh(squash(base, 1)), self.sh(base)]
                self.add('Dodge', v, Anim('Dodge', fr, 14, False))
            if need('Roll'):
                tuck = squash(base, 3)
                tb = bbox(tuck); tp = ((tb[0] + tb[2]) // 2, (tb[1] + tb[3]) // 2)
                rl = [self.sh(squash(base, 1)), self.sh(tuck)]
                for k in (1, 2, 3):
                    rf = rot90(tuck, k, tp); bb = bbox(rf)
                    rl.append(self.sh(shift(rf, 0, FEET - bb[3])))
                rl += [self.sh(squash(base, 1)), self.sh(base)]
                self.add('Roll', v, Anim('Dodge', rl, 14, False))
            if need('Jump'):
                fr = [self.sh(squash(base, 2)), self.sh(shift(stretch(base, 1), 0, -2), 2),
                      self.sh(shift(stretch(base, 1), 0, -7), 7), self.sh(shift(base, 0, -10), 10)]
                self.add('Jump', v, Anim('Jump', fr, 12, False))
            if need('Fall'):
                w2 = R(legs='A', swing=2)
                self.add('Fall', v, Anim('Jump', [self.sh(shift(stretch(w2, 1), 0, -8), 8), self.sh(shift(stretch(w2, 1), 0, -4), 4)], 10, True))
            if need('Land'):
                fr = [X.dust(self.sh(squash(base, 2)), 26, FEET - 1, 1), X.dust(self.sh(squash(base, 1)), 25, FEET - 1, 2), self.sh(base)]
                self.add('Land', v, Anim('Jump', fr, 12, False))
            if need('Victory'):
                rz = R(stretch_rows=1, swing=-3)
                fr = [self.sh(base), self.sh(squash(rz, 1)), self.sh(shift(rz, 0, -3), 3), self.sh(X.sparkle(shift(rz, 0, -4), 31, 18, 2), 4),
                      self.sh(shift(rz, 0, -1), 1), self.sh(X.sparkle(rz, 24, 26, 1))]
                self.add('Victory', v, Anim('Emote', fr, 10, False))
            col = self.c['glow']
            if need('ChargedAttack_Charge'):
                ch = []
                for t in range(4):
                    f = R(squash_rows=1 + t % 2)
                    f = X.glow(f, col if t % 2 == 0 else X.WHT)
                    for k in range(3):
                        a = (t * 40 + k * 120) * np.pi / 180
                        r = 9 - (t % 2) * 3
                        X.px(f, 31 + np.cos(a) * r, 40 + np.sin(a) * r * .7, col)
                    ch.append(self.sh(f))
                self.add('ChargedAttack_Charge', v, Anim('Special', ch, 12, True))
            if need('ChargedAttack_Release') and ('HeavyAttack', v) in self.out:
                hv = self.out[('HeavyAttack', v)]
                rel = [hv.frames[i] for i in hv.seq[2:]]
                rb, rs = self.s.split(rel[0])
                rel[0] = over(rs, X.glow(rb, col))
                self.add('ChargedAttack_Release', v, Anim('Special', rel, 12, False))
            if need('ComboAttack') and ('Attack', v) in self.out and ('HeavyAttack', v) in self.out:
                at, hv = self.out[('Attack', v)], self.out[('HeavyAttack', v)]
                combo = [at.frames[i] for i in at.seq][:-1] + [hv.frames[i] for i in hv.seq][2:]
                self.add('ComboAttack', v, Anim('Special', combo, 13, False))
            if need('CriticalAttack') and ('HeavyAttack', v) in self.out:
                hv = self.out[('HeavyAttack', v)]
                crit = [hv.frames[i] for i in hv.seq]
                hi = len(crit) // 2
                fb, fs = self.s.split(crit[hi])
                flash = fb.copy()
                lit = (fb[:, :, 3] > 0) & (fb[:, :, :3].sum(axis=2) > 60)
                flash[lit] = X.WHT
                crit.insert(hi, over(fs, flash))
                crit[hi + 1] = X.sparkle(X.sparkle(crit[hi + 1], 36, 40 if down else 30, 3), 28, 44 if down else 26, 2, X.YEL, X.ORA)
                self.add('CriticalAttack', v, Anim('Special', crit, 12, False))
            # everyday actions
            if need('Interact'):
                fr = [base, squash(base, 1), X.sparkle(squash(base, 1), 31, 44 if down else 30, 1), squash(base, 1), base]
                self.add('Interact', v, Anim('Other', [self.sh(f) for f in fr], 10, False))
            if need('PickUp'):
                fr = [base, squash(base, 1), squash(base, 2), squash(base, 3), X.sparkle(squash(base, 2), 31, 50 if down else 40, 1), squash(base, 1), base]
                self.add('PickUp', v, Anim('Other', [self.sh(f) for f in fr], 10, False))
            if need('Push'):
                fr = [self.sh(squash(R(legs='A' if i % 4 < 2 else 'B', swing=0, bob=-(i % 2)), 1)) for i in range(8)]
                self.add('Push', v, Anim('Other', fr, 7, True))
            if need('Pull'):
                fr = [self.sh(R(legs='B' if i % 4 < 2 else 'A', swing=0, bob=-(i % 2))) for i in range(8)]
                self.add('Pull', v, Anim('Other', fr, 7, True))
            if need('Sit'):
                fr = [self.sh(squash(base, 1)), self.sh(squash(base, 3)), self.sh(squash(R(bob=0), 3))]
                self.add('Sit', v, Anim('Other', fr, 6, True, [0, 1, 1, 2, 2, 1]))
            if need('Sleep'):
                fr = [self.sh(X.zzz(lie if t % 2 == 0 else squash(lie, 1), 38, 36, t)) for t in range(4)]
                self.add('Sleep', v, Anim('Other', fr, 4, True))
            if need('CastSpell'):
                rz = R(stretch_rows=1)
                fr = [self.sh(squash(rz, 1))]
                for t in range(4):
                    f = X.orb(rz, 31, 18 if down else 18, 2 + (t % 2), [X.PUR, X.BLD2, X.ORA][:2 + t % 2])
                    f = X.ring(f, 31, FEET - 1, 9 + t, X.PUR if t % 2 else X.BLD2)
                    fr.append(self.sh(f))
                self.add('CastSpell', v, Anim('Other', fr, 10, True, [0, 1, 2, 3, 4]))
            if need('ChargeEnergy'):
                fr = []
                for t in range(4):
                    f = squash(base, 1) if t % 2 else base.copy()
                    f = X.glow(f, col if t in (0, 2) else X.WHT)
                    for k in range(4):
                        a = (t * 30 + k * 90) * np.pi / 180
                        X.px(f, 31 + np.cos(a) * (12 - t * 2), 42 + np.sin(a) * (8 - t), col)
                    fr.append(self.sh(f))
                self.add('ChargeEnergy', v, Anim('Other', fr, 10, True))

    # ------------------------------------------------------------------
    def build_all(self):
        self.build_idle(); self.build_walk(); self.build_run()
        self.build_attacks(); self.build_hurt(); self.build_states(); self.build_extras()
        self.build_vertical()
        return self.out
