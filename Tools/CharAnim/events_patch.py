"""Adds animation events to the manifests of the characters whose attacks come from the original packs / older
generators (Soldier, Orc, Demon, BloodMonster, their palette variants, NPCs, bosses). Idempotent.

  python events_patch.py

The impact frame is measured, not guessed: the frames of an attack clip are scanned for the slash colours of the
originals (#f4edea / #d9d8d8 / #c0bfbf / white); HitOn goes on the first frame with a real slash, HitOff after the
last one. Clips without slashes (claws without trail, spit, fireballs) use the frame where the silhouette reaches
furthest forward. SpecialAttack / CastSpell get a Projectile event on that frame; every one-shot attack ends with End.
Clips that already carry events (weapon sets, roster figures) are left alone.
"""
import glob, json, os
import numpy as np
from PIL import Image
from engine import OUT, CELL

SLASH = [(0xf4, 0xed, 0xea), (0xd9, 0xd8, 0xd8), (0xc0, 0xbf, 0xbf), (255, 255, 255)]
ATTACKS = {'Attack', 'HeavyAttack', 'ComboAttack', 'CriticalAttack', 'ChargedAttack_Release', 'SpecialAttack', 'CastSpell'}


def frames_of(path, cell):
    im = np.array(Image.open(path).convert('RGBA'))
    return [im[:, i * cell:(i + 1) * cell] for i in range(im.shape[1] // cell)]


def events_for(clip, frames, seq):
    seqf = [frames[i] for i in seq]
    counts = []
    reach = []
    for f in seqf:
        m = np.zeros(f.shape[:2], bool)
        for c in SLASH:
            m |= np.all(f[:, :, :3] == c, axis=2)
        m &= f[:, :, 3] > 0
        counts.append(int(m.sum()))
        xs = np.nonzero(f[:, :, 3])[1]
        reach.append(int(xs.max()) if len(xs) else 0)
    n = len(seqf)
    big = max(counts)
    if big >= 12:
        hot = [i for i, c in enumerate(counts) if c >= big * .3]
        on, off = hot[0], min(n - 1, hot[-1] + 1)
    else:
        on = int(np.argmax(reach[1:])) + 1 if n > 1 else 0
        off = min(n - 1, on + 1)
    ev = []
    if on > 0:
        ev.append(dict(frame=max(0, on - 1), fn='AnimEvent', arg='Anticipation'))
    if clip in ('SpecialAttack', 'CastSpell'):
        ev.append(dict(frame=on, fn='AnimEvent', arg='Projectile'))
    ev.append(dict(frame=on, fn='AnimEvent', arg='HitOn'))
    ev.append(dict(frame=off, fn='AnimEvent', arg='HitOff'))
    if clip in ('Attack', 'ComboAttack'):
        ev.append(dict(frame=off, fn='AnimEvent', arg='ComboWindow'))
    ev.append(dict(frame=n - 1, fn='AnimEvent', arg='End'))
    return ev


def patch(man_path):
    man = json.load(open(man_path))
    root = os.path.dirname(man_path)
    cell = man.get('cell', CELL)
    changed = 0
    for c in man['clips']:
        if c['name'] not in ATTACKS or c.get('events'):
            continue
        p = os.path.join(root, c['file'])
        if not os.path.exists(p):
            continue
        fr = frames_of(p, cell)
        seq = c.get('seq') or list(range(len(fr)))
        c['events'] = events_for(c['name'], fr, seq)
        changed += 1
    if changed:
        with open(man_path, 'w') as fh:
            json.dump(man, fh, indent=1)
    return changed


if __name__ == '__main__':
    total = 0
    for m in sorted(glob.glob(os.path.join(OUT, '*', '*_animations.json'))):
        n = patch(m)
        if n:
            print(os.path.basename(m), n)
        total += n
    print('clips patched:', total)
