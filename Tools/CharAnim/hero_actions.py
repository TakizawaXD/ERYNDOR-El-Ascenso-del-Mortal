"""Actions the hand-drawn heroes did not have (2026-11-21): every Hero* character gets the clips the player uses that only
the Soldier had - combo, critical, charged attack (charge + release), charge energy, roll, knockback, pick up, interact,
sit, sleep, swim, climb, jump / fall / land, push / pull, victory and defeat.

Every frame is built from the hero's OWN drawn frames (same art, colours and weapon): crouching is the idle pose pressed
down at the feet, sleeping is the last frame of the death lying down and breathing, swimming is the walk cut at the
waist with a water line, the charged attack glows... Timings, loops and animation events copy the Soldier's clips, so
the player code (combo windows, hit frames) works the same.

  python Tools/CharAnim/hero_actions.py            -> Assets/Art/Characters/Hero*/<Folder>/<Hero>_<Clip>_<Dir>.png
                                                      + the clips appended to <Hero>_animations.json
  python Tools/CharAnim/hero_actions.py HeroWizard  (one hero)
"""
import json, math, os, sys
from PIL import Image, ImageChops, ImageEnhance, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Art', 'Characters'))
CELL = 64
FOOT = int(round(CELL * (1 - 0.1875)))        # pixel row of the feet (pivot 0.1875 from the bottom)


# ---------------------------------------------------------------------- frames in / out
class Hero:
    def __init__(self, name):
        self.name = name
        self.meta = json.load(open(os.path.join(ROOT, name, f'{name}_animations.json'), encoding='utf-8'))
        self.clips = {(c['name'], c['dir']): c for c in self.meta['clips']}

    def frames(self, clip, d):
        """frames of a clip in a direction; Left/Right fall back to the mirrored other side, Up/Down to Right"""
        flip = False
        c = self.clips.get((clip, d))
        if c is None and d in ('Left', 'Right'):
            c = self.clips.get((clip, 'Right' if d == 'Left' else 'Left')); flip = c is not None
        if c is None: c = self.clips.get((clip, 'Right')) or self.clips.get((clip, 'Down'))
        if c is None: return None
        im = Image.open(os.path.join(ROOT, self.name, c['file'])).convert('RGBA')
        out = [im.crop((i * CELL, 0, (i + 1) * CELL, CELL)) for i in range(c['frames'])]
        return [f.transpose(Image.FLIP_LEFT_RIGHT) for f in out] if flip else out


def pick(frames, n):
    """n frames evenly spread over a list"""
    if not frames: return []
    return [frames[min(len(frames) - 1, int(round(i * (len(frames) - 1) / max(1, n - 1))))] for i in range(n)]


def blank(): return Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))


def shift(f, dx=0, dy=0):
    o = blank(); o.alpha_composite(f, (0, 0)) if False else None
    o = blank(); o.paste(f, (dx, dy), f); return o


def squash(f, sy, sx=1.0):
    """scale the figure around its feet (bottom-centre)"""
    w, h = max(1, int(round(CELL * sx))), max(1, int(round(CELL * sy)))
    g = f.resize((w, h), Image.NEAREST)
    o = blank()
    o.paste(g, ((CELL - w) // 2, FOOT - int(round(FOOT * sy))), g)
    return o


def lean(f, k, facing):
    """shear the upper body forward (k px at the top of the cell)"""
    if facing not in ('Left', 'Right'): return f
    s = k / CELL * (1 if facing == 'Right' else -1)
    return f.transform(f.size, Image.AFFINE, (1, s, -s * FOOT, 0, 1, 0), Image.NEAREST)


def tint(f, rgb, k):
    """mix the visible pixels toward a colour"""
    r, g, b, a = f.split()
    col = Image.new('RGB', f.size, rgb)
    mixed = Image.blend(f.convert('RGB'), col, k)
    o = mixed.convert('RGBA'); o.putalpha(a); return o


def glow(f, rgb, strength):
    """a soft coloured aura around the figure (behind it)"""
    a = f.split()[3].filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.6))
    a = a.point(lambda v: int(v * strength))
    aura = Image.new('RGBA', f.size, rgb + (0,)); aura.putalpha(a)
    o = blank(); o.alpha_composite(aura); o.alpha_composite(f); return o


def waist_water(f, phase):
    """swimming: the figure sinks to the waist, a light water line with a ripple crosses it"""
    g = shift(f, 0, 3)
    px = g.load()
    line = FOOT - 3
    for y in range(line, CELL):
        for x in range(CELL):
            if px[x, y][3] > 0: px[x, y] = (0, 0, 0, 0)
    xs = [x for x in range(CELL) for y in range(line - 14, line) if px[x, y][3] > 0]
    if xs:
        x0, x1 = min(xs) - 3, max(xs) + 3
        for x in range(x0, x1 + 1):
            yy = line + (1 if (x + phase) % 4 < 2 else 0)
            if 0 <= x < CELL:
                px[x, yy] = (190, 228, 255, 230)
                if yy + 1 < CELL: px[x, yy + 1] = (90, 150, 210, 160)
    return g


def zzz(f, t):
    """sleeping: a little z floats up and fades"""
    o = f.copy(); px = o.load()
    zx, zy = 40 + t, 18 - t * 2
    for (dx, dy) in [(0, 0), (1, 0), (2, 0), (1, 1), (0, 2), (1, 2), (2, 2)]:
        x, y = zx + dx, zy + dy
        if 0 <= x < CELL and 0 <= y < CELL: px[x, y] = (230, 236, 255, 220 - t * 40)
    return o


def lying(f):
    """the last frame of the death rotated / settled so it reads as lying on the ground"""
    bb = f.getbbox()
    if not bb: return f
    return f


# ---------------------------------------------------------------------- recipes (Soldier clip name -> frames)
def build(h, clip, d, n):
    F = h.frames
    idle = F('Idle', d) or F('Idle', 'Down')
    walk = F('Walk', d) or F('Walk', 'Down')
    if clip == 'ChargeEnergy':
        src = pick(F('CastSpell', d) or idle, n)
        return [glow(f, (120, 200, 255), 0.5 + 0.4 * math.sin(i / n * math.pi * 2)) for i, f in enumerate(src)]
    if clip == 'ChargedAttack_Charge':
        src = pick(F('PrepareAttack', d) or idle, n)
        return [glow(shift(f, (i % 2) * (1 if d == 'Right' else -1), 0), (255, 190, 80), 0.45 + 0.35 * (i % 2)) for i, f in enumerate(src)]
    if clip == 'ChargedAttack_Release':
        src = pick(F('HeavyAttack', d) or F('Attack', d), n)
        return [glow(f, (255, 200, 90), 0.6) if i in (1, 2) else f for i, f in enumerate(src)]
    if clip == 'ComboAttack':
        a, hv = F('Attack', d) or [], F('HeavyAttack', d) or []
        return pick(a + hv, n)
    if clip == 'CriticalAttack':
        src = pick(F('SpecialAttack', d) or F('HeavyAttack', d), n)
        return [tint(f, (255, 255, 255), 0.55) if i == 3 else f for i, f in enumerate(src)]
    if clip == 'Climb':
        return pick(F('Walk', 'Up') or walk, n)
    if clip == 'Defeat':
        return pick(F('Death', d) or idle, n)
    if clip == 'Jump':
        base = idle[0]
        return [squash(base, 0.9, 1.06), shift(base, 0, -4), shift(squash(base, 1.06, 0.96), 0, -10), shift(base, 0, -12)][:n]
    if clip == 'Fall':
        base = idle[0]
        return [shift(squash(base, 1.04, 0.97), 0, -8), shift(base, 0, -6)][:n]
    if clip == 'Land':
        base = idle[0]
        return [squash(base, 0.86, 1.08), squash(base, 0.94, 1.03), base][:n]
    if clip == 'Interact':
        return pick(F('CastSpell', d) or idle, n)
    if clip == 'Knockback':
        src = pick(F('Hurt', d) or idle, n)
        bx = -1 if d == 'Right' else 1 if d == 'Left' else 0
        by = 1 if d == 'Up' else -1 if d == 'Down' else 0          # facing down (toward the camera) = pushed up the screen
        k = lambda i: int(round(6 * math.sin(i / max(1, n - 1) * math.pi * 0.9)))
        return [shift(f, bx * k(i), by * k(i)) for i, f in enumerate(src)]
    if clip == 'PickUp':
        base = idle[0]
        ks = [1.0, 0.92, 0.82, 0.76, 0.8]
        return [lean(squash(base, k, 1 + (1 - k) * 0.25), int((1 - k) * 30), d) for k in ks[:n]]
    if clip in ('Push', 'Pull'):
        src = pick(walk, n)
        k = 7 if clip == 'Push' else -5
        return [lean(f, k, d) for f in src]
    if clip == 'Roll':
        return pick(F('Dodge', d) or idle, n)
    if clip == 'Sit':
        base = idle[0]
        return [squash(base, 0.8, 1.06), squash(base, 0.79, 1.06), squash(base, 0.81, 1.05)][:n]
    if clip == 'Sleep':
        # dozing sitting up: the sitting pose slumped forward, breathing slowly, a z floating up
        base = idle[0]
        out = []
        for i in range(n):
            o = lean(squash(base, 0.78 - 0.015 * (i % 2), 1.06), 4, d)
            out.append(zzz(o, i))
        return out
    if clip == 'Swim':
        src = pick(walk, n)
        return [waist_water(f, i) for i, f in enumerate(src)]
    if clip == 'Victory':
        src = pick(F('CastSpell', d) or idle, n)
        hop = [0, -2, -5, -6, -3, 0]
        return [shift(f, 0, hop[i % len(hop)]) for i, f in enumerate(src)]
    return None


def make(name, soldier):
    h = Hero(name)
    added = 0
    templates = {}
    for c in soldier['clips']: templates.setdefault(c['name'], c)
    jobs = []
    for clip, t in templates.items():
        dirs = ['Up'] if clip == 'Climb' else ['Down', 'Up', 'Left', 'Right']   # top-down game: every action faces 4 ways
        for d in dirs:
            if (clip, d) in h.clips: continue
            c = dict(t); c['dir'] = d
            src = next((x for x in soldier['clips'] if x['name'] == clip and x['dir'] == d), None)
            if src: c = dict(src)
            jobs.append(c)
    for c in jobs:
        clip, d = c['name'], c['dir']
        frames = build(h, clip, d, c['frames'])
        if not frames: continue
        frames = (frames + [frames[-1]] * c['frames'])[:c['frames']]
        sheet = Image.new('RGBA', (CELL * len(frames), CELL), (0, 0, 0, 0))
        for i, f in enumerate(frames): sheet.alpha_composite(f, (i * CELL, 0))
        folder = c['file'].split('/')[0]
        rel = f'{folder}/{name}_{clip}_{d}.png'
        os.makedirs(os.path.join(ROOT, name, folder), exist_ok=True)
        sheet.save(os.path.join(ROOT, name, rel))
        entry = dict(c); entry['file'] = rel; entry['size'] = [CELL * len(frames), CELL]
        h.meta['clips'] = [x for x in h.meta['clips'] if not (x['name'] == clip and x['dir'] == d)] + [entry]
        added += 1
    json.dump(h.meta, open(os.path.join(ROOT, name, f'{name}_animations.json'), 'w', encoding='utf-8'), indent=1)
    return added


def preview(names, out):
    rows = []
    for n in names:
        h = Hero(n)
        strip = []
        for clip in ('PickUp', 'Sit', 'Sleep', 'Swim', 'ChargedAttack_Charge', 'ComboAttack', 'Victory', 'Jump'):
            fr = h.frames(clip, 'Right')
            if fr: strip.append(fr[len(fr) // 2])
        rows.append(strip)
    W = max(len(r) for r in rows) * CELL
    sheet = Image.new('RGBA', (W, CELL * len(rows)), (58, 92, 64, 255))
    for j, r in enumerate(rows):
        for i, f in enumerate(r): sheet.alpha_composite(f, (i * CELL, j * CELL))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(out)


if __name__ == '__main__':
    soldier = json.load(open(os.path.join(ROOT, 'Soldier', 'Soldier_animations.json'), encoding='utf-8'))
    heroes = sys.argv[1:] or sorted(d for d in os.listdir(ROOT) if d.startswith('Hero') and os.path.isdir(os.path.join(ROOT, d)))
    for n in heroes:
        print(n, make(n, soldier), 'new clips')
    docs = os.path.join(ROOT, '..', '..', '..', 'Documentation', 'CharacterPreviews')
    os.makedirs(docs, exist_ok=True)
    preview(heroes, os.path.join(docs, 'hero_actions.png'))
    print('preview', os.path.join(docs, 'hero_actions.png'))
