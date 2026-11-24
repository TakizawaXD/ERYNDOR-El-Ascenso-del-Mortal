"""Front/back 'rigs': hand-drawn views + leg poses + arm swing + weapon layers -> 64x64 frames."""
import numpy as np
from engine import *
import designs as D


class Rig:
    def __init__(self, front, back, pal, legs, arms, weapon_front=None, weapon_back=None,
                 weapon_front_off=(0, 0), weapon_back_off=(0, 0), weapon_behind_front=False,
                 weapon_behind_back=True, tail_front=None, tail_front_off=(0, 0), body_dy=0):
        self.views = {'Down': front, 'Up': back}
        self.pal, self.legs, self.arms = pal, legs, arms
        self.weapon = {'Down': weapon_front, 'Up': weapon_back}
        self.woff = {'Down': weapon_front_off, 'Up': weapon_back_off}
        self.wbehind = {'Down': weapon_behind_front, 'Up': weapon_behind_back}
        self.tail_front, self.tail_off = tail_front, tail_front_off
        self.body_dy = body_dy
        self.h = len(front)
        self.w = len(front[0])

    def body_rows(self, view, legs='stand'):
        rows = list(self.views[view])
        lg = self.legs[legs]
        if view == 'Up' and legs in ('A', 'B'):
            lg = self.legs['B' if legs == 'A' else 'A']  # seen from behind the planted leg swaps sides
        rows[-len(lg):] = lg
        return rows

    def body(self, view, legs='stand', swing=0):
        spr = ascii_sprite(self.body_rows(view, legs), self.pal)
        if swing:
            (l0, l1), (r0, r1), (y0, y1) = self.arms
            out = spr.copy()
            for (c0, c1, s) in ((l0, l1, swing), (r0, r1, -swing)):
                block = spr[y0:y1, c0:c1].copy()
                out[y0:y1, c0:c1] = 0
                ny0, ny1 = max(0, y0 + s), min(spr.shape[0], y1 + s)
                src0 = ny0 - (y0 + s)
                out[ny0:ny1, c0:c1] = np.where(block[src0:src0 + ny1 - ny0, :, 3:4] > 0,
                                               block[src0:src0 + ny1 - ny0], out[ny0:ny1, c0:c1])
            spr = out
        return spr

    def frame(self, view, legs='stand', bob=0, swing=0, weapon=True, wdx=0, wdy=0, squash_rows=0, stretch_rows=0):
        body = place(self.body(view, legs, swing), dy=bob + self.body_dy)
        if squash_rows:
            body = squash(body, squash_rows)
        if stretch_rows:
            body = stretch(body, stretch_rows)
        out = blank()
        layers = []
        w = self.weapon.get(view)
        if weapon and w is not None:
            ox, oy = self.woff[view]
            wspr = place(ascii_sprite(w, self.pal), dx=ox + wdx, dy=oy + bob + wdy + squash_rows - stretch_rows)
            layers.append(('w', wspr))
        if view == 'Down' and self.tail_front is not None:
            tx, ty = self.tail_off
            layers.append(('t', place(ascii_sprite(self.tail_front, self.pal), dx=tx, dy=ty + bob + self.body_dy)))
        behind = [l for k, l in layers if k == 't' or (k == 'w' and self.wbehind[view])]
        front = [l for k, l in layers if k == 'w' and not self.wbehind[view]]
        for l in behind:
            out = over(out, l)
        out = over(out, body)
        for l in front:
            out = over(out, l)
        return out


RIGS = {
    'Soldier': Rig(D.SOLDIER_FRONT, D.SOLDIER_BACK, D.SOLDIER_PAL, D.SOLDIER_LEGS, D.SOLDIER_ARMS),
    'Orc': Rig(D.ORC_FRONT, D.ORC_BACK, D.ORC_PAL, D.ORC_LEGS, D.ORC_ARMS,
               weapon_front=D.ORC_AXE_UP, weapon_back=[r[::-1] for r in D.ORC_AXE_UP],
               weapon_front_off=(8, -4), weapon_back_off=(-8, -4), weapon_behind_front=False, weapon_behind_back=False),
    'Demon': Rig(D.DEMON_FRONT, D.DEMON_BACK, D.DEMON_PAL, D.DEMON_LEGS, D.DEMON_ARMS,
                 weapon_front=D.DEMON_BLADE_FRONT, weapon_back=D.DEMON_BLADE_FRONT,
                 weapon_front_off=(0, 0), weapon_back_off=(0, -1), weapon_behind_front=False, weapon_behind_back=True,
                 tail_front=D.DEMON_TAIL_FRONT, tail_front_off=(-7, -3), body_dy=D.DEMON_BODY_DY),
    'BloodMonster': Rig(D.BLOOD_FRONT, D.BLOOD_BACK, D.BLOOD_PAL, D.BLOOD_LEGS, D.BLOOD_ARMS),
}
