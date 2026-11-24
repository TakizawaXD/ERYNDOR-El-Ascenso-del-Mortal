"""Boss arena set dressing + boss UI (all drawn here, no source art).

  python arena.py   -> Assets/Art/World/Arena/*.png, Assets/Art/UI/Boss/*.png

Themes (index = row/cell order everywhere):  0 violet (El Invocador, Bosque Corrupto)   1 sand (Gorgrak, Arenas Rojas)
                                             2 blood (Madre de Sangre, Pantano)          3 fire (Señor Demonio, Monte Ceniza)
                                             4 ice (Coloso de Escarcha, Picos Nevados)
"""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'Assets', 'Art', 'World', 'Arena')
UI = os.path.join(ROOT, 'Assets', 'Art', 'UI', 'Boss')
PREV = os.path.join(ROOT, 'Documentation', 'CharacterPreviews')


def hx(s, a=255):
    s = s.lstrip('#'); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def R(*c):
    return [hx(x) for x in c]


#            stone ramp (dark->light)                                      flame (core, mid, edge)                    cloth
THEMES = [
    dict(stone=R('#0c0a12', '#16131f', '#221d2e', '#2e2840', '#3e3654', '#544a6c'), flame=R('#ffffff', '#d6a8ff', '#8a3ce0', '#4a1a8a'), cloth=R('#1a0c2c', '#341a56', '#52307e', '#7450a8'), rune='#b070ff'),
    dict(stone=R('#1a120c', '#2c2016', '#40301e', '#5a4428', '#7a5e38', '#9a7a4c'), flame=R('#ffffff', '#ffe08a', '#f09a30', '#a04a10'), cloth=R('#3a0a08', '#62140e', '#8e2416', '#b43a20'), rune='#ffb040'),
    dict(stone=R('#100808', '#1e0e10', '#2e161a', '#402026', '#562c32', '#704048'), flame=R('#ffffff', '#ffb0b0', '#f04050', '#8a1020'), cloth=R('#2a0410', '#4a0a1e', '#701430', '#982444'), rune='#ff4060'),
    dict(stone=R('#0c0808', '#1a1210', '#2a1c18', '#3a2820', '#4e362a', '#664636'), flame=R('#ffffff', '#ffe080', '#ff8020', '#b02010'), cloth=R('#1a0606', '#360c0a', '#5a1410', '#82221a'), rune='#ff7020'),
    dict(stone=R('#0e1420', '#182234', '#24344c', '#344a66', '#4a6684', '#6a88a6'), flame=R('#ffffff', '#c8f4ff', '#60c8f0', '#2a6aa0'), cloth=R('#0c1a34', '#14305a', '#1e4880', '#2e66a8'), rune='#70e0ff'),
]
OUTL = (10, 6, 12, 255)


def shade_mask(im, m, rmp, mid=None, rng=None):
    """cel-shade a bool mask (rim light top-left, shadow bottom-right) into an RGBA array"""
    n = len(rmp)
    mid = n - 3 if mid is None else mid
    sh = lambda a, dx, dy: np.roll(np.roll(a, dy, 0), dx, 1)
    lvl = np.full(m.shape, mid, int)
    lvl[m & ~sh(m, 1, 1)] += 1
    lvl[m & ~sh(m, -1, -1)] -= 2
    lvl[m & ~sh(m, -2, -2)] -= 1
    if rng is not None:
        lvl += (rng.random(m.shape) < 0.08).astype(int) - (rng.random(m.shape) < 0.08).astype(int)
    lvl = np.clip(lvl, 0, n - 1)
    cols = np.array(rmp, np.uint8)
    im[m] = cols[lvl[m]]


def outline(im, col=OUTL):
    a = im[:, :, 3] > 0
    o = np.zeros_like(a)
    o[1:] |= a[:-1]; o[:-1] |= a[1:]; o[:, 1:] |= a[:, :-1]; o[:, :-1] |= a[:, 1:]
    o &= ~a
    im[o] = col


class _Filled:
    """ImageDraw wrapper: shapes drawn without a colour are filled (newer Pillow draws nothing for polygon() without fill)"""
    def __init__(self, d): self.d = d
    def __getattr__(self, k):
        f = getattr(self.d, k)
        if k in ('polygon', 'ellipse', 'rectangle', 'pieslice', 'chord', 'rounded_rectangle'):
            return lambda *a, **kw: f(*a, **({'fill': 255} if 'fill' not in kw and 'outline' not in kw else {}), **kw)
        return f


def mask(w, h, fn):
    m = Image.new('L', (w, h), 0); fn(_Filled(ImageDraw.Draw(m))); return np.array(m) > 0


def save(a, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(a, 'RGBA').save(path)


# ------------------------------------------------------------------ floor: 320x192 ellipse of cracked flagstones (20x12 tiles)
def floor(t, seed):
    W, H = 320, 192
    rng = np.random.default_rng(seed)
    st = THEMES[t]['stone']
    a = np.zeros((H, W, 4), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    nx, ny = (xx - W / 2 + .5) / (W / 2 - 2), (yy - H / 2 + .5) / (H / 2 - 2)
    r = np.sqrt(nx ** 2 + ny ** 2)
    edge = 1 + (rng.random((H, W)) - .5) * 0.06
    disc = r < 0.97 * edge
    # flagstones: concentric rings split into blocks
    ring = (r * 8).astype(int)
    ang = (np.degrees(np.arctan2(ny, nx)) + 360) % 360
    block = (ang / (360 / (6 + ring * 5))).astype(int)
    cell = ring * 100 + block
    ids = np.unique(cell[disc])
    tone = {c: int(rng.integers(1, 4)) for c in ids}
    lvl = np.zeros((H, W), int)
    for c in ids:
        lvl[(cell == c) & disc] = tone[c]
    # grout lines
    grout = disc & ((np.roll(cell, 1, 1) != cell) | (np.roll(cell, 1, 0) != cell))
    lvl[grout] = 0
    # rim highlight on the top-left edge of each stone
    hl = disc & ~grout & (np.roll(grout, 1, 0) | np.roll(grout, 1, 1))
    lvl[hl] = np.minimum(lvl[hl] + 1, 5)
    # cracks
    for _ in range(30):
        x, y = rng.integers(20, W - 20), rng.integers(12, H - 12)
        for _ in range(int(rng.integers(6, 16))):
            if disc[y, x]: lvl[y, x] = 0
            x += int(rng.integers(-1, 2)); y += int(rng.integers(-1, 2)) if rng.random() < .5 else 0
            x, y = np.clip(x, 0, W - 1), np.clip(y, 0, H - 1)
    # darker toward the rim (vignette)
    lvl = lvl - (r > 0.8).astype(int)
    lvl = np.clip(lvl, 0, 5)
    cols = np.array(st, np.uint8)
    a[disc] = cols[lvl[disc]]
    # broken rim stones
    rim = disc & (r > 0.9)
    a[rim & (rng.random((H, W)) < 0.25)] = 0
    outline(a)
    return a


# ------------------------------------------------------------------ rune circle (white, tinted + additive in Unity)
def runes(W=128, H=64):
    a = np.zeros((H, W, 4), np.uint8)
    im = Image.fromarray(a, 'RGBA'); d = ImageDraw.Draw(im)
    cx, cy = W / 2 - .5, H / 2 - .5
    def el(rx, ry, w=1):
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(255, 255, 255, 255), width=w)
    el(61, 30, 2); el(54, 26); el(36, 17); el(20, 9)
    # star of two triangles
    pts = lambda k: [(cx + math.cos(math.radians(k + i * 120)) * 52, cy + math.sin(math.radians(k + i * 120)) * 25) for i in range(3)]
    d.polygon(pts(-90), outline=(255, 255, 255, 220)); d.polygon(pts(90), outline=(255, 255, 255, 220))
    # glyphs in the outer band
    rng = random.Random(4)
    for i in range(24):
        a0 = math.radians(i * 15 + 7)
        x, y = cx + math.cos(a0) * 57.5, cy + math.sin(a0) * 28
        g = rng.randint(0, 3)
        if g == 0: d.line([(x - 1, y - 1), (x + 1, y + 1)], fill=(255, 255, 255, 230))
        elif g == 1: d.line([(x, y - 1), (x, y + 1)], fill=(255, 255, 255, 230)); d.point((x + 1, y), fill=(255, 255, 255, 230))
        elif g == 2: d.rectangle([x - 1, y - 1, x, y], outline=(255, 255, 255, 230))
        else: d.point([(x - 1, y), (x + 1, y), (x, y - 1)], fill=(255, 255, 255, 230))
    return np.array(im)


# ------------------------------------------------------------------ brazier (stone stand) + flames
def brazier(t):
    W, H = 18, 22
    a = np.zeros((H, W, 4), np.uint8)
    st = THEMES[t]['stone']
    rng = np.random.default_rng(t)
    shade_mask(a, mask(W, H, lambda d: d.polygon([(2, 4), (15, 4), (13, 9), (4, 9)])), st, rng=rng)            # bowl
    shade_mask(a, mask(W, H, lambda d: d.rectangle([7, 9, 10, 18])), st)                                       # stem
    shade_mask(a, mask(W, H, lambda d: d.polygon([(4, 18), (13, 18), (15, 21), (2, 21)])), st)                # foot
    a[4, 3:15] = THEMES[t]['flame'][3]                                                                          # embers in the bowl
    outline(a)
    return a


def flames(t, n=4):
    W, H = 16, 16
    fl = THEMES[t]['flame']
    out = []
    for f in range(n):
        rng = np.random.default_rng(f * 11 + t)
        a = np.zeros((H, W, 4), np.uint8)
        for x in range(3, 13):
            h = int(6 + 6 * math.exp(-((x - 7.5) / 3.2) ** 2) + rng.integers(-2, 3))
            for y in range(h):
                k = y / max(1, h)
                c = fl[3] if k < .25 else fl[2] if k < .6 else fl[1] if k < .85 else fl[0]
                if abs(x - 7.5) > 3.5 and k > .6: c = fl[2]
                a[H - 1 - y, x] = c
        # loose sparks
        for _ in range(2):
            x, y = int(rng.integers(4, 12)), int(rng.integers(0, 4))
            a[y, x] = fl[1]
        out.append(a)
    return out


def pillar(t, broken=False):
    W, H = 20, 56
    st = THEMES[t]['stone']
    rng = np.random.default_rng(t + 9)
    a = np.zeros((H, W, 4), np.uint8)
    top = 16 if broken else 2
    shade_mask(a, mask(W, H, lambda d: d.rectangle([1, H - 7, 18, H - 1])), st, mid=4)
    shade_mask(a, mask(W, H, lambda d: d.rectangle([4, top + 5, 15, H - 7])), st, mid=4, rng=rng)
    if broken:
        m = mask(W, H, lambda d: d.polygon([(4, top + 5), (8, top), (11, top + 4), (15, top + 1), (15, top + 6), (4, top + 6)]))
        shade_mask(a, m, st, mid=4)
    else:
        shade_mask(a, mask(W, H, lambda d: d.rectangle([2, top, 17, top + 5])), st, mid=5)
    for x in (7, 11):                                                   # fluting
        a[top + 7:H - 8, x] = st[2]
    for y in range(top + 8, H - 8, 9):                                  # cracks / joints
        a[y, 4:16] = st[2]
    outline(a)
    return a


def banner(t):
    W, H = 14, 30
    cl = THEMES[t]['cloth']; rune = hx(THEMES[t]['rune'])
    a = np.zeros((H, W, 4), np.uint8)
    a[0:2, 0:14] = (60, 50, 40, 255); a[0, 0:14] = (110, 96, 80, 255)
    m = mask(W, H, lambda d: d.polygon([(1, 2), (12, 2), (12, 26), (9, 23), (6.5, 28), (4, 23), (1, 26)]))
    shade_mask(a, m, cl, mid=2)
    # emblem: diamond with an eye
    for y in range(8, 17):
        w = 4 - abs(y - 12)
        a[y, 6 - w:7 + w + 1] = rune if abs(y - 12) == 4 - (4 - abs(y - 12)) and False else a[y, 6 - w:7 + w + 1]
        if w >= 0:
            a[y, 6 - w] = rune; a[y, 7 + w] = rune
    a[12, 6:8] = (255, 255, 255, 255)
    outline(a)
    return a


def chain():
    W, H = 6, 40
    a = np.zeros((H, W, 4), np.uint8)
    for y in range(0, H, 4):
        a[y:y + 3, 1] = (90, 90, 106, 255); a[y:y + 3, 4] = (60, 60, 72, 255)
        a[y, 2:4] = (150, 150, 168, 255); a[y + 2, 2:4] = (60, 60, 72, 255)
        a[y + 3, 2:4] = (110, 110, 126, 255)
    return a


def light_column():
    W, H = 16, 80
    a = np.zeros((H, W, 4), np.uint8)
    for y in range(H):
        for x in range(W):
            k = 1 - abs(x - 7.5) / 8
            v = k ** 1.6 * (0.35 + 0.65 * (y / H) ** 0.7)
            a[y, x] = (255, 255, 255, int(255 * min(1, v)))
    return a


def fog():
    W, H = 96, 40
    rng = np.random.default_rng(5)
    a = np.zeros((H, W, 4), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    v = np.zeros((H, W))
    for _ in range(7):
        cx, cy = rng.uniform(20, W - 20), rng.uniform(12, H - 12)
        rx, ry = rng.uniform(14, 26), rng.uniform(7, 12)
        v += np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
    v = np.clip(v, 0, 1)
    a[..., :3] = 255
    a[..., 3] = (np.round(v * 4) / 4 * 150).astype(np.uint8)          # banded alpha keeps it pixel-art
    return a


def ring_sprite(W=288, H=288, w=2):
    """shockwave ring drawn at its largest size (18 units) so it is never scaled up into chunky pixels"""
    a = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(a)
    d.ellipse([1, 1, W - 2, H - 2], outline=(255, 255, 255, 255), width=w)
    d.ellipse([5, 5, W - 6, H - 6], outline=(255, 255, 255, 90), width=1)
    return np.array(a)


def seal_rune():
    """one floating glyph of the rune wall (white, tinted + additive in Unity)"""
    a = np.zeros((14, 8, 4), np.uint8)
    w, f = (255, 255, 255, 255), (255, 255, 255, 120)
    for y in range(1, 13): a[y, 3] = w
    for (x, y) in ((1, 3), (2, 2), (5, 5), (4, 4), (1, 8), (2, 9), (5, 10), (4, 11), (6, 6)):
        a[y, x] = w
    for y in range(0, 14): a[y, 2 if y % 2 else 4] = np.maximum(a[y, 2 if y % 2 else 4], f)
    return a


def telegraph():
    W = H = 32
    a = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(a)
    d.ellipse([1, 1, W - 2, H - 2], fill=(255, 255, 255, 60), outline=(255, 255, 255, 255), width=2)
    d.ellipse([10, 10, W - 11, H - 11], outline=(255, 255, 255, 160), width=1)
    return np.array(a)


def debris(t):
    """8 small ground bits per theme: rubble, skulls, bones, theme extras"""
    st = THEMES[t]['stone']; fl = THEMES[t]['flame']
    bone = R('#3e3224', '#7a6648', '#b8a27a', '#e6d8b4')
    cells = []
    for k in range(8):
        a = np.zeros((16, 16, 4), np.uint8)
        rng = np.random.default_rng(t * 31 + k)
        if k < 3:      # rubble
            for _ in range(3):
                x, y, r = rng.integers(3, 12), rng.integers(8, 13), rng.integers(2, 4)
                shade_mask(a, mask(16, 16, lambda d: d.ellipse([x - r, y - r + 1, x + r, y + r - 1])), st)
        elif k == 3:   # skull
            shade_mask(a, mask(16, 16, lambda d: d.ellipse([4, 5, 11, 11])), bone, mid=2)
            shade_mask(a, mask(16, 16, lambda d: d.rectangle([5, 10, 10, 12])), bone, mid=2)
            a[8, 6] = a[8, 9] = (16, 8, 8, 255); a[11, 7] = (40, 30, 20, 255)
        elif k == 4:   # bones
            for (x0, y0, x1, y1) in ((3, 12, 12, 9), (4, 8, 11, 13)):
                shade_mask(a, mask(16, 16, lambda d: d.line([(x0, y0), (x1, y1)], fill=255, width=2)), bone, mid=2)
        elif k == 5:   # candles / embers in theme colour
            for x in (4, 8, 11):
                a[9:13, x] = st[4]; a[8, x] = fl[1]; a[7, x] = fl[0]
        elif k == 6:   # crystal / shard in theme colour
            shade_mask(a, mask(16, 16, lambda d: d.polygon([(6, 13), (8, 3), (10, 13)])), [fl[3], fl[2], fl[1], fl[0]], mid=1)
            shade_mask(a, mask(16, 16, lambda d: d.polygon([(9, 13), (12, 7), (13, 13)])), [fl[3], fl[2], fl[1], fl[0]], mid=1)
        else:          # cracked slab
            shade_mask(a, mask(16, 16, lambda d: d.polygon([(2, 10), (13, 9), (14, 13), (3, 14)])), st)
            a[11, 5:10] = st[0]
        outline(a)
        cells.append(a)
    return cells


def sheet(cells, cols=None):
    cols = cols or len(cells)
    h, w = cells[0].shape[:2]
    rows = (len(cells) + cols - 1) // cols
    s = np.zeros((h * rows, w * cols, 4), np.uint8)
    for i, c in enumerate(cells):
        r, k = divmod(i, cols)
        s[r * h:(r + 1) * h, k * w:(k + 1) * w] = c
    return s


# ------------------------------------------------------------------ boss UI
def ui():
    gold = R('#3a2a1a', '#7a5a2e', '#c09a50', '#f4dc94', '#fff6d0')
    vio = hx('#b070ff')
    # end cap: ornate diamond with a gem (14x18)
    cap = np.zeros((18, 14, 4), np.uint8)
    shade_mask(cap, mask(14, 18, lambda d: d.polygon([(7, 0), (13, 9), (7, 17), (1, 9)])), gold, mid=2)
    gem = mask(14, 18, lambda d: d.polygon([(7, 5), (10, 9), (7, 12), (4, 9)]))
    cap[gem] = (120, 40, 200, 255); cap[7:9, 6:8] = (230, 200, 255, 255)
    outline(cap)
    # track: dark inner channel with a gold rim (9-slice, border 3) 16x10
    tr = np.zeros((10, 16, 4), np.uint8)
    tr[:, :] = (10, 6, 16, 235)
    tr[0, :] = gold[2]; tr[9, :] = gold[1]; tr[1, :] = gold[3]; tr[8, :] = gold[0]
    tr[:, 0] = gold[1]; tr[:, 15] = gold[1]
    # crest above the name (spiked arc) 48x10
    cr = np.zeros((10, 48, 4), np.uint8)
    shade_mask(cr, mask(48, 10, lambda d: [d.polygon([(0, 9), (24, 4), (48, 9), (24, 7)]), d.polygon([(21, 6), (24, 0), (27, 6)]),
                                            d.polygon([(12, 7), (14, 3), (16, 6)]), d.polygon([(32, 6), (34, 3), (36, 7)])]), gold, mid=2)
    outline(cr)
    # fill: vertical gradient white (tinted in Unity) 4x6
    fill = np.zeros((6, 4, 4), np.uint8)
    for y, v in enumerate((255, 235, 210, 190, 160, 130)):
        fill[y, :] = (v, v, v, 255)
    # objective panel 9-slice (border 4) 16x16 + icon 9x9
    pan = np.zeros((16, 16, 4), np.uint8)
    pan[:, :] = (12, 8, 20, 200)
    pan[0, 1:15] = (80, 60, 110, 255); pan[15, 1:15] = (40, 30, 60, 255); pan[1:15, 0] = (70, 52, 100, 255); pan[1:15, 15] = (40, 30, 60, 255)
    icon = np.zeros((9, 9, 4), np.uint8)
    m = mask(9, 9, lambda d: d.polygon([(4, 0), (8, 4), (4, 8), (0, 4)]))
    icon[m] = vio; icon[3:6, 3:6] = (240, 220, 255, 255); outline(icon)
    save(cap, os.path.join(UI, 'ui_boss_cap.png'))
    save(tr, os.path.join(UI, 'ui_boss_track_9s3.png'))
    save(cr, os.path.join(UI, 'ui_boss_crest.png'))
    save(fill, os.path.join(UI, 'ui_boss_fill.png'))
    save(pan, os.path.join(UI, 'ui_objective_9s4.png'))
    save(icon, os.path.join(UI, 'ui_objective_icon.png'))


def main():
    for t in range(5):
        save(floor(t, 11 + t), os.path.join(OUT, f'arena_floor_{t}.png'))
    save(runes(), os.path.join(OUT, 'arena_runes.png'))
    save(sheet([brazier(t) for t in range(5)]), os.path.join(OUT, 'arena_braziers_18x22.png'))
    save(sheet([f for t in range(5) for f in flames(t)], 4), os.path.join(OUT, 'arena_flames_16x16.png'))
    save(sheet([pillar(t) for t in range(5)] + [pillar(t, True) for t in range(5)], 5), os.path.join(OUT, 'arena_pillars_20x56.png'))
    save(sheet([banner(t) for t in range(5)]), os.path.join(OUT, 'arena_banners_14x30.png'))
    save(chain(), os.path.join(OUT, 'arena_chain.png'))
    save(light_column(), os.path.join(OUT, 'arena_lightcolumn.png'))
    save(fog(), os.path.join(OUT, 'arena_fog.png'))
    save(ring_sprite(), os.path.join(OUT, 'arena_wave.png'))
    save(telegraph(), os.path.join(OUT, 'arena_telegraph.png'))
    save(seal_rune(), os.path.join(OUT, 'arena_sealrune.png'))
    save(sheet([c for t in range(5) for c in debris(t)], 8), os.path.join(OUT, 'arena_debris_16x16.png'))
    ui()
    # preview: each theme's floor with props
    pv = Image.new('RGBA', (320 * 5, 230), (20, 16, 24, 255))
    br = Image.open(os.path.join(OUT, 'arena_braziers_18x22.png')); fl = Image.open(os.path.join(OUT, 'arena_flames_16x16.png'))
    pl = Image.open(os.path.join(OUT, 'arena_pillars_20x56.png')); bn = Image.open(os.path.join(OUT, 'arena_banners_14x30.png'))
    rn = Image.open(os.path.join(OUT, 'arena_runes.png'))
    for t in range(5):
        x0 = t * 320
        pv.alpha_composite(Image.open(os.path.join(OUT, f'arena_floor_{t}.png')), (x0, 30))
        tint = Image.new('RGBA', rn.size, hx(THEMES[t]['rune'])); tint.putalpha(rn.split()[3])
        pv.alpha_composite(tint, (x0 + 96, 94))
        for px in (10, 290):
            pv.alpha_composite(pl.crop((t * 20, 0, t * 20 + 20, 56)), (x0 + px, 10))
            pv.alpha_composite(br.crop((t * 18, 0, t * 18 + 18, 22)), (x0 + px + 30, 100))
            pv.alpha_composite(fl.crop((0, t * 16, 16, t * 16 + 16)), (x0 + px + 31, 88))
        pv.alpha_composite(bn.crop((t * 14, 0, t * 14 + 14, 30)), (x0 + 90, 4))
    pv.resize((pv.width * 2, pv.height * 2), Image.NEAREST).save(os.path.join(PREV, 'arenas.png'))


if __name__ == '__main__':
    main()
