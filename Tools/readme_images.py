"""Images for README.md (2026-11-24), made from the game's own data and art so they always match the current build.

  python Tools/readme_images.py   -> Documentation/readme/*.png
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'Documentation', 'readme')
LV = os.path.join(ROOT, 'Assets', 'Game', 'Levels')
CH = os.path.join(ROOT, 'Assets', 'Art', 'Characters')
FONT = 'C:/Windows/Fonts/segoeuib.ttf'
os.makedirs(OUT, exist_ok=True)
Image.MAX_IMAGE_PIXELS = None


def font(sz):
    try: return ImageFont.truetype(FONT, sz)
    except OSError: return ImageFont.load_default()


def label(d, xy, text, sz=18, fill=(255, 240, 200), anchor='mm'):
    f = font(sz)
    x, y = xy
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        d.text((x + dx, y + dy), text, font=f, fill=(10, 8, 16), anchor=anchor)
    d.text((x, y), text, font=f, fill=fill, anchor=anchor)


def world():
    L = open(os.path.join(LV, 'World2.txt'), encoding='utf-8').read().splitlines()
    W, H = map(int, [l for l in L if l.startswith('SIZE ')][0].split()[1:3])
    SW, SH = map(int, [l for l in L if l.startswith('SURFACE ')][0].split()[1:3])
    r0 = L.index('REGIONS')
    R = L[r0 + 1:r0 + 1 + H]
    names = {l[11]: l[13:] for l in L if l.startswith('REGIONNAME ')}
    return W, H, SW, SH, R, names


def title():
    im = Image.open(os.path.join(ROOT, 'Assets', 'Art', 'UI', 'Title', 'eryndor_title.png')).convert('RGB')
    im.crop((260, 40, 1412, 470)).resize((960, 358), Image.LANCZOS).save(os.path.join(OUT, 'banner.png'))


def world_map():
    W, H, SW, SH, R, names = world()
    prev = Image.open(os.path.join(ROOT, 'Assets', 'Art', 'World', 'ground_full_preview.png')).convert('RGB')   # 4 px per cell
    k = prev.width / W
    surf = prev.crop((0, 0, int(SW * k), int(SH * k)))
    scale = 1400 / surf.width
    surf = surf.resize((1400, int(surf.height * scale)), Image.LANCZOS)
    d = ImageDraw.Draw(surf)
    px = surf.width / SW
    # region names at the centre of each surface region
    acc = {}
    for y in range(0, SH, 3):
        for x in range(0, SW, 3):
            c = R[y][x]
            if c in 'abcdefghij' and not (c == 'j' and x < SW * 0.8):      # the Eternal Ruins: their east coast
                s = acc.setdefault(c, [0, 0, 0]); s[0] += x; s[1] += y; s[2] += 1
    for c, (sx, sy, n) in acc.items():
        if n > 50: label(d, (sx / n * px, sy / n * px), names.get(c, c).title(), 20, (240, 230, 255))
    cat = open(os.path.join(LV, 'Maps.txt'), encoding='utf-8').read().splitlines()
    for l in cat:
        p = l.split(' ')
        if p[0] in ('TOWN', 'ZONE'):
            x0, r0, x1, r1 = map(int, p[2:6]); t = ' '.join(p[6:]).split('|')[0].title()
            d.rectangle([x0 * px, r0 * px, x1 * px, r1 * px], outline=(255, 210, 90) if p[0] == 'TOWN' else (255, 90, 60), width=3)
            label(d, ((x0 + x1) / 2 * px, r1 * px + 14), t, 17, (255, 215, 110) if p[0] == 'TOWN' else (255, 130, 100))
    meta = json.load(open(os.path.join(LV, 'World3.json'), encoding='utf-8'))
    for e in meta['entrances']:
        cx, cy = e['x'] * px, e['row'] * px
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(120, 230, 255), outline=(10, 10, 20), width=2)
    surf.save(os.path.join(OUT, 'mapa_mundo.png'))


def underground():
    W, H, SW, SH, R, names = world()
    prev = Image.open(os.path.join(ROOT, 'Assets', 'Art', 'World', 'ground_full_preview.png')).convert('RGB')
    k = prev.width / W
    cat = open(os.path.join(LV, 'Maps.txt'), encoding='utf-8').read().splitlines()
    caves = [l.split(' ') for l in cat if l.startswith('CAVE ')]
    x0 = min(int(c[2]) for c in caves); y1 = max(int(c[5]) for c in caves)
    x1 = max(int(c[4]) for c in caves)
    img = prev.crop((int(x0 * k) - 8, 0, int(x1 * k) + 8, int(y1 * k) + 8))
    scale = 1200 / img.width
    img = img.resize((1200, int(img.height * scale)), Image.LANCZOS)
    ImageEnh = img.point(lambda v: min(255, int(v * 1.6)))       # caves are painted for the dark: lift them for the picture
    d = ImageDraw.Draw(ImageEnh)
    for c in caves:
        cx0, cy0, cx1 = int(c[2]), int(c[3]), int(c[4])
        t = ' '.join(c[7:]).title()
        label(d, (((cx0 + cx1) / 2 - x0) * k * scale + 8 * scale, cy0 * k * scale + 12), t, 16, (255, 225, 150))
    ImageEnh.save(os.path.join(OUT, 'subsuelo.png'))


CLASSES = [('Soldier', 'Caballero'), ('HeroKnight', 'Caballero Real'), ('HeroCrusader', 'Cruzado'), ('HeroAxeKnight', 'G. del Hacha'),
           ('HeroSoldier', 'Mercenario'), ('HeroWizard', 'Mago'), ('HeroSwordswoman', 'Espadachina'), ('HeroPriestess', 'Sacerdotisa'),
           ('HeroRanger', 'Arquera'), ('KnightSamurai', 'Samurái')]


def frame(char, clip, d, i=0):
    m = json.load(open(os.path.join(CH, char, f'{char}_animations.json'), encoding='utf-8'))
    c = next((c for c in m['clips'] if c['name'] == clip and c['dir'] == d), None)
    if c is None: return None
    im = Image.open(os.path.join(CH, char, c['file'])).convert('RGBA')
    cell = m['cell']
    i = min(i, c['frames'] - 1)
    return im.crop((i * cell, 0, (i + 1) * cell, cell))


def classes():
    S = 4
    tile = 64 * S
    out = Image.new('RGB', (tile * 5, (tile + 40) * 2), (24, 20, 36))
    d = ImageDraw.Draw(out)
    for k, (ch, name) in enumerate(CLASSES):
        f = frame(ch, 'Idle', 'Down')
        x, y = (k % 5) * tile, (k // 5) * (tile + 40)
        d.rectangle([x + 6, y + 6, x + tile - 6, y + tile - 6], fill=(42, 62, 58))
        if f: out.paste(f.resize((tile, tile), Image.NEAREST), (x, y + 10), f.resize((tile, tile), Image.NEAREST))
        label(d, (x + tile / 2, y + tile + 18), name, 22)
    out.save(os.path.join(OUT, 'clases.png'))


def directions():
    rows = [('Soldier', ['Walk', 'Attack', 'Block', 'Roll', 'PickUp']), ('Orc', ['Walk', 'Attack', 'HeavyAttack', 'Knockback', 'Dodge'])]
    S = 3; tile = 64 * S
    dirs = ['Down', 'Up', 'Left', 'Right']
    out = Image.new('RGB', (tile * 4 + 160, tile * 10 + 10), (24, 20, 36))
    d = ImageDraw.Draw(out)
    j = 0
    for ch, clips in rows:
        for clip in clips:
            label(d, (80, j * tile + tile / 2), clip, 20, (255, 225, 150))
            for i, dd in enumerate(dirs):
                f = frame(ch, clip, dd, 2)
                if f is None: continue
                g = f.resize((tile, tile), Image.NEAREST)
                out.paste(g, (160 + i * tile, j * tile), g)
            j += 1
    for i, dd in enumerate(['Abajo', 'Arriba', 'Izquierda', 'Derecha']):
        label(d, (160 + i * tile + tile / 2, tile * 10 - 4), dd, 16, (200, 200, 230))
    out.save(os.path.join(OUT, 'direcciones.png'))


def enemies():
    names = ['Orc', 'OrcFrost', 'GoblinAxe', 'Werewolf', 'Minotaur', 'LavaGolem', 'Demon', 'DemonAxe', 'Skeleton', 'Reaper',
             'BloodMonster', 'Tentacle', 'EyeWatcher', 'FireSlug', 'Hellhound', 'OrcCorsair']
    S = 3; tile = 64 * S
    out = Image.new('RGB', (tile * 8, tile * 2), (24, 20, 36))
    for k, n in enumerate(names):
        f = frame(n, 'Idle', 'Down') or frame(n, 'Idle', 'Right')
        if f is None: continue
        g = f.resize((tile, tile), Image.NEAREST)
        out.paste(g, ((k % 8) * tile, (k // 8) * tile), g)
    out.save(os.path.join(OUT, 'enemigos.png'))


# ---------------------------------------------------------------------- data maps (biomes, enemy density, town plans)
BIOME_COL = {'a': (122, 170, 82), 'b': (40, 104, 52), 'c': (214, 196, 128), 'd': (92, 62, 110), 'e': (226, 234, 242),
             'f': (222, 152, 92), 'g': (88, 70, 74), 'h': (138, 78, 176), 'i': (96, 150, 96), 'j': (104, 160, 176)}
SEA = (24, 46, 84)


def grids():
    L = open(os.path.join(LV, 'World2.txt'), encoding='utf-8').read().splitlines()
    W, H = map(int, [l for l in L if l.startswith('SIZE ')][0].split()[1:3])
    SW, SH = map(int, [l for l in L if l.startswith('SURFACE ')][0].split()[1:3])
    t0, e0, r0 = L.index('TERRAIN'), L.index('ENTITIES'), L.index('REGIONS')
    return L, W, H, SW, SH, L[t0 + 1:t0 + 1 + H], L[e0 + 1:e0 + 1 + H], L[r0 + 1:r0 + 1 + H]


def legend(d, x, y, items, sz=17, sw=22):
    for i, (col, text) in enumerate(items):
        yy = y + i * (sw + 8)
        d.rectangle([x, yy, x + sw, yy + sw], fill=col, outline=(10, 8, 16), width=2)
        d.text((x + sw + 10, yy + sw / 2), text, font=font(sz), fill=(235, 230, 245), anchor='lm')


def biome_map():
    L, W, H, SW, SH, T, E, R = grids()
    names = {l[11]: l[13:] for l in L if l.startswith('REGIONNAME ')}
    k = 2
    img = Image.new('RGB', (SW * k + 380, SH * k), (16, 14, 24))
    px = img.load()
    for y in range(SH):
        for x in range(SW):
            c = SEA if T[y][x] == 'O' else BIOME_COL.get(R[y][x], (60, 60, 60))
            if T[y][x] in 'wL=H' and T[y][x] != 'O': c = (52, 110, 190) if T[y][x] != 'L' else (240, 110, 30)
            if T[y][x] in '_p': c = tuple(min(255, int(v * 0.72 + 60)) for v in c)
            for dy in range(k):
                for dx in range(k): px[x * k + dx, y * k + dy] = c
    d = ImageDraw.Draw(img)
    items = [(BIOME_COL[c], names.get(c, c).title()) for c in 'abcdefghij']
    items += [(SEA, 'Mar'), ((52, 110, 190), 'Ríos y lagos'), ((240, 110, 30), 'Lava')]
    d.text((SW * k + 24, 24), 'Biomas de Eryndor', font=font(22), fill=(255, 225, 150))
    legend(d, SW * k + 24, 64, items)
    img.save(os.path.join(OUT, 'mapa_biomas.png'))


def enemy_density():
    import scipy.ndimage as nd
    L, W, H, SW, SH, T, E, R = grids()
    dens = np.zeros((SH, SW), np.float32)
    for l in L:
        if l.startswith('ENEMY '):
            q = l.split(' '); x, y = int(q[2]), int(q[3])
            if x < SW: dens[y, x] += 1
    dens = nd.gaussian_filter(dens, 6)
    dens /= dens.max()
    base = np.zeros((SH, SW, 3), np.float32)
    for y in range(SH):
        for x in range(SW):
            base[y, x] = SEA if T[y][x] == 'O' else (70, 70, 78)
    hot = np.array((228, 64, 52), np.float32)
    a = np.clip(dens * 1.4, 0, 1)[:, :, None]
    land = np.array([[T[y][x] != 'O' for x in range(SW)] for y in range(SH)])[:, :, None]
    out = base * (1 - a * land) + (hot * a + base * 0.15 * a) * land
    img = Image.fromarray(out.clip(0, 255).astype(np.uint8)).resize((SW * 2, SH * 2), Image.NEAREST)
    canvas = Image.new('RGB', (SW * 2 + 330, SH * 2), (16, 14, 24)); canvas.paste(img, (0, 0))
    d = ImageDraw.Draw(canvas)
    cat = open(os.path.join(LV, 'Maps.txt'), encoding='utf-8').read().splitlines()
    for l in cat:
        q = l.split(' ')
        if q[0] == 'TOWN':
            x0, r0, x1, r1 = map(int, q[2:6])
            d.rectangle([x0 * 2, r0 * 2, x1 * 2, r1 * 2], outline=(255, 215, 110), width=3)
    d.text((SW * 2 + 24, 24), 'Densidad de enemigos', font=font(22), fill=(255, 225, 150))
    steps = [(70, 70, 78), (150, 68, 64), (200, 66, 56), (228, 64, 52)]
    legend(d, SW * 2 + 24, 64, [(steps[0], 'Sin enemigos'), (steps[1], 'Baja'), (steps[2], 'Media'), (steps[3], 'Alta'),
                                ((255, 215, 110), 'Ciudad (zona segura)')])
    canvas.save(os.path.join(OUT, 'mapa_enemigos.png'))


HOUSE_NAMES = {'casa': 'Casa', 'cabana': 'Cabaña', 'posada': 'Posada', 'herreria': 'Herrería', 'capilla': 'Capilla',
               'biblioteca': 'Biblioteca', 'cuartel': 'Cuartel'}
TER = {'.': (98, 150, 70), 'f': (58, 110, 56), '_': (200, 176, 128), 'p': (150, 148, 140), 'w': (60, 120, 200), 'O': (34, 70, 140),
       '=': (130, 90, 50), 'H': (130, 90, 50), 'D': (130, 90, 50), 'c': (110, 104, 92), 'k': (60, 52, 56), 'a': (90, 80, 84),
       'F': (170, 126, 64), 's': (60, 90, 70), 'L': (240, 110, 30), 'd': (220, 170, 110), 'n': (230, 236, 244), 'C': (200, 210, 225), 'v': (110, 70, 140)}


def town_plans():
    L, W, H, SW, SH, T, E, R = grids()
    houses = {(int(l.split()[1]), int(l.split()[2])): l.split()[3] for l in L if l.startswith('HOUSE ')}
    cat = open(os.path.join(LV, 'Maps.txt'), encoding='utf-8').read().splitlines()
    k = 9
    for l in cat:
        q = l.split(' ')
        if q[0] not in ('TOWN', 'ZONE'): continue
        mid = q[1]; x0, r0, x1, r1 = map(int, q[2:6]); title = ' '.join(q[6:]).split('|')[0].title()
        w, h = x1 - x0 + 1, r1 - r0 + 1
        img = Image.new('RGB', (w * k, h * k + 50), (16, 14, 24))
        d = ImageDraw.Draw(img)
        for y in range(h):
            for x in range(w):
                d.rectangle([x * k, y * k + 50, x * k + k - 1, y * k + 50 + k - 1], fill=TER.get(T[r0 + y][x0 + x], (80, 80, 80)))
        labels = []
        for y in range(h):
            for x in range(w):
                c = E[r0 + y][x0 + x]
                cx, cy = x * k + k / 2, y * k + 50 + k / 2
                if c in 'TUtAVuiIY':
                    d.ellipse([cx - k * .55, cy - k * .55, cx + k * .55, cy + k * .55], fill=(30, 74, 38))
                elif c in '#90':
                    d.rectangle([x * k, y * k + 50, x * k + k, y * k + 50 + k], fill=(70, 66, 72))
                elif c in '678J':
                    d.rectangle([cx - 2.2 * k, cy - 3.2 * k, cx + 2.2 * k, cy + k * .5], fill=(168, 70, 58) if c != 'J' else (150, 120, 80), outline=(20, 14, 16), width=2)
                    hn = houses.get((x0 + x, r0 + y))
                    if hn: labels.append((cx, cy - 1.4 * k, HOUSE_NAMES.get(hn, hn.title())))
                    elif c == 'J': labels.append((cx, cy - 1.4 * k, 'Molino'))
                elif c == 'F':
                    d.ellipse([cx - k * .8, cy - k * .8, cx + k * .8, cy + k * .8], fill=(255, 150, 40), outline=(20, 14, 16))
                elif c == '$':
                    d.rectangle([cx - k, cy - k * .7, cx + k, cy + k * .7], fill=(240, 200, 70), outline=(20, 14, 16))
                elif c == '@':
                    d.ellipse([cx - k * .6, cy - k * .6, cx + k * .6, cy + k * .6], fill=(120, 170, 230), outline=(20, 14, 16))
                elif c == 'C':
                    d.rectangle([cx - k * .45, cy - k * .35, cx + k * .45, cy + k * .35], fill=(200, 150, 60), outline=(20, 14, 16))
        for (cx, cy, t) in labels: label(d, (cx, cy), t, 15)
        d.text((12, 25), title, font=font(24), fill=(255, 225, 150), anchor='lm')
        img.save(os.path.join(OUT, f'plano_{mid}.png'))


if __name__ == '__main__':
    for fn in (title, world_map, underground, classes, directions, enemies, biome_map, enemy_density, town_plans):
        fn(); print('ok', fn.__name__)
