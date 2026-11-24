"""Loads the ORIGINAL Tiny RPG strips (read-only) and normalises them to the shared 64x64 frame."""
import glob, os
from collections import Counter, defaultdict
import numpy as np
from engine import *

P1 = os.path.join(ROOT, 'Tiny RPG Character Asset Pack 01 v2.0 -Free Soldier&Orc', 'Characters(100x100 split)')
P2 = os.path.join(ROOT, 'Tiny RPG Character Asset Pack 02 -Free Demon_A&Blood Monster_A', 'Characters(100x100 split)')

CHARS = {
    'Soldier': (os.path.join(P1, 'Soldier', 'Soldier'), 'Soldier'),
    'Orc': (os.path.join(P1, 'Orc', 'Orc'), 'Orc'),
    'Demon': (os.path.join(P2, 'Demon_A', 'Demon_A'), 'Demon_A'),
    'BloodMonster': (os.path.join(P2, 'Blood Monster_A', 'Blood Monster_A'), 'Blood Monster_A'),
}
SHADOW_RGB = (0x53, 0x45, 0x45)   # Soldier's baked ground shadow (appears nowhere else on him)


def _is_shadow(px):
    return px[3] and tuple(int(v) for v in px[:3]) == SHADOW_RGB


class Source:
    def __init__(self, key):
        folder, prefix = CHARS[key]
        self.key = key
        self.has_shadow = key == 'Soldier'
        raw = {}
        for p in sorted(glob.glob(os.path.join(folder, prefix + '_*.png'))):
            name = os.path.basename(p)[len(prefix) + 1:-4]
            raw[name] = load_strip(p)
        self.raw = raw
        idle0 = raw['Idle'][0].copy()
        if self.has_shadow:
            m = np.all(idle0[:, :, :3] == SHADOW_RGB, axis=2)
            idle0[m] = 0
        ys, xs = np.nonzero(idle0[:, :, 3])
        self.feet = ys.max() + 1
        legs = xs[ys >= self.feet - 3]
        self.cx = (legs.min() + legs.max()) / 2.0
        # weapons hang into the leg rows for some characters: use the measured body centre instead
        self.cx = {'Orc': 50.0, 'Demon': 51.5}.get(key, self.cx)
        self.anims = {k: [normalise(c, self.cx, self.feet) for c in v] for k, v in raw.items()}
        self.shadow = self._shadow_sprite()

    # ------------------------------------------------------------------
    def split(self, f):
        """-> (body, shadow) layers"""
        if not self.has_shadow:
            return f.copy(), blank()
        m = np.all(f[:, :, :3] == SHADOW_RGB, axis=2) & (f[:, :, 3] > 0)
        body, sh = f.copy(), blank()
        body[m] = 0
        sh[m] = f[m]
        return body, sh

    def _shadow_sprite(self):
        if not self.has_shadow:
            return blank()
        # Attack02 frame 1: the soldier is airborne, so the full ground shadow is visible
        _, sh = self.split(self.anims['Attack02'][1])
        return sh

    def body(self, anim, i):
        return self.split(self.anims[anim][i])[0]

    def with_shadow(self, body, height=0):
        """ground shadow (shrinks while airborne) under a body layer"""
        if not self.has_shadow:
            return body
        sh = self.shadow
        if height >= 6:   # smaller shadow when high in the air
            b = bbox(sh)
            sh = sh.copy()
            sh[:, :b[0] + 2] = 0; sh[:, b[2] - 2:] = 0
        return over(sh, body)

    def palette(self):
        c = Counter()
        for fr in self.anims.values():
            for f in fr:
                for px in f[f[:, :, 3] > 0]:
                    c[tuple(int(v) for v in px[:3])] += 1
        return c

    def hurt_maps(self):
        """learn the original 'hurt' colour treatment: frame0 colour -> frame1/frame2 colour"""
        h = self.anims['Hurt']
        base = self.split(h[0])[0]
        maps = []
        for k in (1, 2):
            tgt = self.split(h[k])[0]
            votes = defaultdict(Counter)
            both = opaque(base) & opaque(tgt)
            for y, x in zip(*np.nonzero(both)):
                votes[tuple(int(v) for v in base[y, x][:3])][tuple(int(v) for v in tgt[y, x][:3])] += 1
            m = {a: b.most_common(1)[0][0] for a, b in votes.items()}
            # pixels of the hurt frame that sit outside the base silhouette = glow colour
            extra = opaque(tgt) & ~opaque(base)
            glow = Counter(tuple(int(v) for v in tgt[y, x][:3]) for y, x in zip(*np.nonzero(extra)))
            maps.append((m, glow.most_common(1)[0][0] if glow else None))
        return maps


if __name__ == '__main__':
    for k in CHARS:
        s = Source(k)
        print(k, 'cx', s.cx, 'feet', s.feet, {a: len(v) for a, v in s.anims.items()})
        for i, (m, g) in enumerate(s.hurt_maps()):
            print('  hurt', i + 1, 'mapped', len(m), 'glow', g)
