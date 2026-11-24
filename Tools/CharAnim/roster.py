"""The new character roster (the two sheets the user added to Assets/Scripts) cut out and animated.

  python roster.py [Name ...]  -> Assets/Art/Characters/<Name>/<Cat>/<Name>_<Anim>_<Dir>.png + <Name>_animations.json
                                  Documentation/CharacterPreviews/roster.png

The sheets are previews drawn at x4 on a grey background: they are read (never changed), scaled back to 1:1, and every
figure is cut out by its box keeping only the pixel islands that mostly belong to it (neighbours overlap a little).
The baked ground shadow is dropped (the game draws its own). Every figure goes into the shared 64x64 cell with its
ground on row 51, so the existing CharacterAnimationBuilder makes its clips and controller.

Animations (4 directions; Right = the drawing, Left = mirror, Down/Up = the drawing with direction-correct effects):
  Idle (breathing, or hovering for flyers), Walk (step + bob), Attack (wind-up, lunge, slash), HeavyAttack (rise and
  slam with a shock ring), SpecialAttack + CastSpell (charge glow and sparks), Hurt (white flash, red, recoil),
  Death (topple and fade).
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from engine import *
import fxdraw as X

SRC = os.path.join(ROOT, 'Assets', 'Scripts')
SHEETS = ['+6Q38I.png', 'LdBfCI.png']
PREVIEW = os.path.join(ROOT, 'Documentation', 'CharacterPreviews', 'roster.png')
BG = (110, 110, 110)
SHADOW = (83, 69, 69)

# name: (sheet, box x0,y0,x1,y1 at 1:1, flyer, effect colour)
ROSTER = {
    # ---------------------------------------------------------------- sheet 0: heroes, goblins, undead
    'HeroSwordswoman': (0, (56, 5, 82, 27), False, X.SLASH),
    'HeroWizard':      (0, (84, 3, 104, 26), False, X.YEL),
    'HeroSoldier':     (0, (12, 30, 31, 51), False, X.SLASH),
    'HeroKnight':      (0, (40, 30, 68, 52), False, X.SLASH),
    'HeroCrusader':    (0, (71, 30, 100, 52), False, X.YEL),
    'HeroAxeKnight':   (0, (99, 29, 122, 52), False, X.SLASH),
    'HeroRider':       (0, (122, 12, 154, 54), False, X.SLASH),
    'HeroPriestess':   (0, (13, 53, 33, 78), False, X.YEL),
    'HeroRanger':      (0, (39, 54, 64, 77), False, X.SLASH),
    'Werewolf':        (0, (69, 54, 92, 74), False, X.SLASH),
    'WolfWarrior':     (0, (96, 53, 125, 72), False, X.SLASH),
    'SlimeGreen':      (0, (125, 59, 147, 76), False, hx('#9cdb43')),
    'GoblinAxe':       (0, (13, 78, 38, 99), False, X.SLASH),
    'GoblinViking':    (0, (41, 76, 68, 99), False, X.SLASH),
    'GoblinShaman':    (0, (68, 72, 97, 99), False, hx('#9cdb43')),
    'GoblinRider':     (0, (95, 68, 123, 100), False, X.SLASH),
    'Bat':             (0, (126, 73, 149, 87), True, X.PUR),
    'Skeleton':        (0, (11, 102, 41, 123), False, X.SLASH),
    'SkeletonSpear':   (0, (43, 95, 76, 122), False, X.SLASH),
    'SkeletonWarrior': (0, (73, 97, 89, 122), False, X.SLASH),
    'SkeletonAxe':     (0, (94, 98, 116, 123), False, X.SLASH),
    'Reaper':          (0, (119, 88, 148, 121), True, hx('#8ad8f0')),
    # ---------------------------------------------------------------- sheet 1: hellspawn
    'ImpBlade':        (1, (15, 22, 38, 44), False, X.SLASH),
    'ImpCrossbow':     (1, (43, 22, 63, 43), False, X.SLASH),
    'ImpTrident':      (1, (66, 15, 100, 39), True, X.ORA),
    'DemonAxe':        (1, (100, 19, 131, 47), False, X.SLASH),
    'Hellhound':       (1, (128, 25, 152, 46), False, X.ORA),
    'DemonGreat':      (1, (4, 44, 41, 71), False, X.ORA),
    'ScytheCultist':   (1, (40, 41, 70, 69), False, hx('#8ad8f0')),
    'ImpChain':        (1, (64, 43, 91, 69), True, X.ORA),
    'FireSlug':        (1, (97, 50, 122, 67), False, X.ORA),
    'FlameSkull':      (1, (129, 37, 146, 64), True, X.ORA),
    'HellBat':         (1, (124, 64, 148, 78), True, X.ORA),
    'Tentacle':        (1, (12, 71, 33, 90), False, hx('#e070b4')),
    'Maw':             (1, (44, 68, 60, 86), True, hx('#e070b4')),
    'Minotaur':        (1, (64, 66, 97, 91), False, X.SLASH),
    'EyeWatcher':      (1, (101, 71, 121, 88), False, hx('#c48cff')),
    'DarkSpearman':    (1, (13, 88, 31, 119), False, X.SLASH),
    'ShieldBrute':     (1, (35, 95, 57, 119), False, X.SLASH),
    'ImpSwarm':        (1, (60, 88, 98, 119), False, X.ORA),
    'LavaGolem':       (1, (96, 87, 131, 119), False, X.ORA),
    'DemonQueen':      (1, (127, 93, 151, 119), False, X.YEL),
}


# ------------------------------------------------------------------ cutting
_sheet_cache = {}


def load_sheet(i):
    if i in _sheet_cache:
        return _sheet_cache[i]
    a = np.array(Image.open(os.path.join(SRC, SHEETS[i])).convert('RGBA'))[::4, ::4].copy()
    bg = np.all(a[:, :, :3] == BG, axis=2)
    a[bg] = 0
    shadow = np.all(a[:, :, :3] == SHADOW, axis=2) & (a[:, :, 3] > 0)
    body = (a[:, :, 3] > 0) & ~shadow
    lab, n = ndimage.label(body, structure=np.ones((3, 3)))
    _sheet_cache[i] = (a, shadow, body, lab, n)
    return _sheet_cache[i]


def cut(name):
    i, (x0, y0, x1, y1), flyer, _ = ROSTER[name]
    a, shadow, body, lab, n = load_sheet(i)
    inside = np.zeros(body.shape, bool); inside[y0:y1, x0:x1] = True
    keep = np.zeros(body.shape, bool)
    for c in np.unique(lab[inside & body]):
        if c == 0: continue
        comp = lab == c
        share = (comp & inside).sum() / comp.sum()
        if share >= 0.5:
            keep |= comp & inside
        elif share > 0:            # an island shared with a neighbour (touching outlines): split it by the nearest box
            ys_, xs_ = np.nonzero(comp & inside)
            mine = (x0 + x1) / 2
            others = [((b[0] + b[2]) / 2, b) for nm, (si, b, _, _) in ROSTER.items() if si == i and nm != name]
            for y, x in zip(ys_, xs_):
                near = [cx_ for cx_, b in others if b[0] <= x < b[2] and b[1] <= y < b[3]]
                if all(abs(x - mine) <= abs(x - cx_) for cx_ in near):
                    keep[y, x] = True
    # ground: the baked shadow under the figure (flyers hover above it), else the lowest body pixel
    sh = shadow & inside
    ys = np.nonzero(sh)[0]
    by, bx = np.nonzero(keep)
    ground = by.max() + 3 if flyer else (int(round(ys.mean())) if len(ys) else by.max())   # flyers hover 3 px up
    cx = (np.percentile(bx, 15) + np.percentile(bx, 85)) / 2
    out = blank()
    dx = int(round(CX - .5 - cx))
    dy = (FEET - 1) - ground
    for y, x in zip(by, bx):
        X_, Y_ = x + dx, y + dy
        if 0 <= X_ < CELL and 0 <= Y_ < CELL:
            out[Y_, X_] = a[y, x]
    return out, flyer


# ------------------------------------------------------------------ repairs: neighbours' leftovers out, hidden parts drawn in
BLACK = (0, 0, 0, 255)
ERASE = {   # 64-cell rects (x0, y0, x1, y1 inclusive) that belong to a neighbour on the sheet
    'Werewolf': [(19, 48, 26, 54)],
    'WolfWarrior': [(33, 46, 34, 52), (44, 48, 47, 52)],
    'Hellhound': [(28, 47, 32, 58), (18, 33, 23, 38), (18, 46, 21, 50)],
    'DemonAxe': [(41, 28, 50, 50)],
    'SkeletonSpear': [(46, 43, 51, 52)],
    'ScytheCultist': [(14, 57, 27, 63)],
}
GREY_ERASE = {'FlameSkull': [(16, 10, 44, 33)]}   # only greys/blacks there (a hound's feet over the flame)


def _colors(f, y0, y1):
    """(main, dark, light) body colours of the figure between rows y0..y1, outline excluded"""
    from collections import Counter
    px = [tuple(int(v) for v in f[y, x]) for y in range(y0, y1) for x in range(CELL) if f[y, x, 3] and f[y, x, :3].sum() > 60]
    if not px: return BLACK, BLACK, BLACK
    c = [k for k, _ in Counter(px).most_common(6)]
    lum = lambda q: q[0] * .3 + q[1] * .59 + q[2] * .11
    main = c[0]
    return main, min(c, key=lum), max(c, key=lum)


def _paint(f, pts, col):
    new = np.zeros(f.shape[:2], bool)
    for x, y in pts:
        if 0 <= x < CELL and 0 <= y < CELL and f[y, x, 3] == 0:
            f[y, x] = col; new[y, x] = True
    return new


def _rect(x0, y0, x1, y1):
    return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]


def _outline_new(f, new):
    o = np.zeros_like(new)
    o[1:] |= new[:-1]; o[:-1] |= new[1:]; o[:, 1:] |= new[:, :-1]; o[:, :-1] |= new[:, 1:]
    o &= f[:, :, 3] == 0
    f[o] = BLACK


def repair(name, f):
    f = f.copy()
    for (x0, y0, x1, y1) in ERASE.get(name, []):
        f[y0:y1 + 1, x0:x1 + 1] = 0
    for (x0, y0, x1, y1) in GREY_ERASE.get(name, []):
        reg = f[y0:y1 + 1, x0:x1 + 1]
        sat = reg[:, :, :3].max(2).astype(int) - reg[:, :, :3].min(2)
        reg[(sat < 45) & (reg[:, :, 3] > 0)] = 0
    # loose specks left by neighbours: islands far from the figure
    m = f[:, :, 3] > 0
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    if n > 1:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        main = lab == (np.argmax(sizes) + 1)
        near = ndimage.binary_dilation(main, iterations=2)
        for k in range(1, n + 1):
            comp = lab == k
            if sizes[k - 1] < 14 and not (comp & near).any():
                f[comp] = 0
    new = np.zeros(f.shape[:2], bool)
    if name == 'WolfWarrior':
        armor, dark, light = _colors(f, 38, 45)
        new |= _paint(f, _rect(26, 46, 32, 47), armor)
        new |= _paint(f, _rect(26, 48, 32, 48), dark)
        new |= _paint(f, _rect(26, 49, 27, 50) + _rect(31, 49, 32, 50), armor)
        new |= _paint(f, [(27, 46), (28, 46)], light)
        new |= _paint(f, _rect(25, 51, 27, 51) + _rect(31, 51, 33, 51), dark)
    elif name == 'Werewolf':
        fur, dark, light = _colors(f, 42, 49)
        new |= _paint(f, _rect(27, 48, 29, 50) + _rect(33, 48, 35, 50), fur)
        new |= _paint(f, _rect(26, 51, 29, 51) + _rect(33, 51, 36, 51), dark)
    elif name == 'Hellhound':
        fur, dark, light = _colors(f, 39, 46)
        new |= _paint(f, _rect(24, 46, 26, 50) + _rect(36, 47, 38, 50), fur)
        new |= _paint(f, _rect(23, 51, 26, 51) + _rect(36, 51, 39, 51), dark)
        new |= _paint(f, [(22, 41), (21, 40), (21, 39), (20, 38), (20, 37), (21, 36)], fur)
    elif name == 'FlameSkull':
        ys, xs = np.nonzero(f[:, :, 3])
        ty = ys.min(); tx = int(round(xs[ys == ty].mean()))
        flame, red, glowc = _colors(f, ty, ty + 7)
        new |= _paint(f, _rect(tx - 1, ty - 1, tx + 1, ty - 1) + _rect(tx - 1, ty - 2, tx, ty - 2), red)
        new |= _paint(f, _rect(tx - 1, ty - 4, tx, ty - 3), flame)
        new |= _paint(f, [(tx, ty - 5), (tx, ty - 6)], glowc)
    if new.any():
        _outline_new(f, new)
    return f


# ------------------------------------------------------------------ animation helpers
def tint(f, col, k):
    o = f.copy(); m = o[:, :, 3] > 0
    o[m, :3] = (o[m, :3] * (1 - k) + np.array(col[:3]) * k).astype(np.uint8)
    return o


def fade(f, k):
    o = f.copy()
    o[:, :, 3] = (o[:, :, 3] * (1 - k)).astype(np.uint8)
    rng = np.random.default_rng(3)
    o[(rng.random(o.shape[:2]) < k) & (o[:, :, 3] > 0)] = 0
    return o


def legs(f, step):
    """walk pose: the lowest 5 rows of the figure slide one pixel apart"""
    b = bbox(f)
    if b is None or step == 0: return f.copy()
    cut_ = b[3] - 5
    o = f.copy(); o[cut_:] = 0
    low = blank(); low[cut_:] = f[cut_:]
    left = low.copy(); left[:, CX:] = 0
    right = low.copy(); right[:, :CX] = 0
    o = over(o, left, -step, 0)
    o = over(o, right, step, 0)
    return o


def body_h(f):
    b = bbox(f); return (b[3] - b[1]) if b else 20


def fx_slash(f, d, big=False, col=X.SLASH, fade_=False):
    h = body_h(f)
    r = (16 if big else 12)
    cy = FEET - h // 2
    if d == 'Right': return X.arc(f, 38, cy, r, r - (5 if big else 4), -75, 75, ry=1.0, fade=fade_)
    if d == 'Down': return X.arc(f, 31.5, FEET - 6, r, r - 4, 15, 165, ry=.55, fade=fade_)
    return X.arc(f, 31.5, FEET - h + 2, r, r - 4, 195, 345, ry=.55, fade=fade_)


def frames_for(base, flyer, col, d):
    """all clips for one facing; base already faces d horizontally"""
    lean_dir = 1 if d == 'Right' else 0
    ly = {'Down': 1, 'Up': -1}.get(d, 0)
    A = {}
    if flyer:
        A['Idle'] = (('Idle', [shift(base, 0, 0), shift(base, 0, -1), shift(base, 0, -2), shift(base, 0, -1)], 6, True))
        A['Walk'] = (('Walk', [shift(base, 0, -k) for k in (0, 1, 2, 1, 0, 1)], 10, True))
    else:
        A['Idle'] = (('Idle', [base, squash(base, 1), squash(base, 1), base], 5, True))
        A['Walk'] = (('Walk', [legs(base, 1), shift(legs(base, 1), 0, -1), base, legs(base, -1), shift(legs(base, -1), 0, -1), base], 10, True))
    lean = lambda f, k: lean_(f, k * (1 if lean_dir else 0), ly * k)
    A['Attack'] = (('Attack', [lean(squash(base, 1), -1), lean(base, -2), fx_slash(lean(base, 3), d, col=col),
                               fx_slash(lean(base, 2), d, col=col, fade_=True), base], 12, False))
    up = shift(stretch(base, 1), 0, -2)
    slam = X.ring(lean(squash(base, 2), 2), 31.5, FEET - 1, 12, X.DUST)
    A['HeavyAttack'] = (('Attack', [squash(base, 2), up, shift(up, 0, -1), fx_slash(slam, d, big=True, col=col),
                                    X.ring(squash(base, 1), 31.5, FEET - 1, 16, X.DUST2), base], 10, False))
    glow1 = X.glow(base, col)
    A['SpecialAttack'] = (('Special', [squash(base, 1), glow1, X.sparkle(glow1, 31 + (8 if d == 'Right' else 0), FEET - body_h(base) // 2, 3, X.WHT, col),
                                       lean(base, 2), base], 10, False))
    A['CastSpell'] = (('Special', [stretch(base, 1), X.glow(stretch(base, 1), col), X.ring(X.glow(base, col), 31.5, FEET - 1, 13, col),
                                   X.ring(base, 31.5, FEET - 1, 17, col), base], 8, False))
    A['Hurt'] = (('Hurt', [tint(base, X.WHT, .8), tint(shift(base, -1 if d == 'Right' else 0, 0), X.RED, .45), base], 12, False))
    fall = [base, tint(base, X.WHT, .7), lean(squash(base, 2), -2), shift(squash(base, 4), 0, 1)]
    fall += [fade(fall[-1], k) for k in (.3, .6, .9)]
    A['Death'] = (('Death', fall, 8, False))
    return A


def lean_(f, dx, dy):
    if dx == 0 and dy == 0: return f.copy()
    o = lean(f, dx) if dx else f.copy()
    if dy:
        b = bbox(o)
        if b is not None:
            top = blank(); split = b[1] + (b[3] - b[1]) // 2
            top[:split] = o[:split]
            o2 = o.copy(); o2[:split] = 0
            o = over(o2, top, 0, dy)
    return o


def dedupe(frames):
    uniq, seq = [], []
    for f in frames:
        for j, u in enumerate(uniq):
            if np.array_equal(f, u): seq.append(j); break
        else:
            seq.append(len(uniq)); uniq.append(f)
    return uniq, seq


def build(name):
    base, flyer = cut(name)
    base = repair(name, base)
    col = ROSTER[name][3]
    root = os.path.join(OUT, name)
    clips = []
    for d in ('Right', 'Left', 'Down', 'Up'):
        b = base if d != 'Left' else flip(base)
        A = frames_for(base, flyer, col, 'Right' if d == 'Right' else d) if d != 'Left' else None
        if d == 'Left':
            A = {k: (cat, [flip(f) for f in fr], fps, loop) for k, (cat, fr, fps, loop) in frames_for(base, flyer, col, 'Right').items()}
        for anim, (cat, fr, fps, loop) in A.items():
            uniq, seq = dedupe(fr)
            rel = f'{cat}/{name}_{anim}_{d}.png'
            save_sheet(uniq, os.path.join(root, rel))
            clips.append(dict(name=anim, dir=d, file=rel, frames=len(uniq), seq=seq, fps=fps, loop=loop, size=[CELL * len(uniq), CELL]))
    with open(os.path.join(root, f'{name}_animations.json'), 'w') as fh:
        json.dump(dict(character=name, cell=CELL, pivot=[0.5, (CELL - FEET) / CELL], ppu=16, clips=clips), fh, indent=1)
    return base


def preview(bases):
    names = list(bases)
    cols = 8; rows = (len(names) + cols - 1) // cols
    sheet = Image.new('RGBA', (64 * cols, 64 * rows), (70, 96, 70, 255))
    for i, n in enumerate(names):
        sheet.alpha_composite(Image.fromarray(bases[n], 'RGBA'), ((i % cols) * 64, (i // cols) * 64))
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(PREVIEW)


if __name__ == '__main__':
    keys = sys.argv[1:] or list(ROSTER)
    bases = {}
    for k in keys:
        bases[k] = build(k)
        print(k)
    preview(bases)
