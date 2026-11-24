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


if __name__ == '__main__':
    for fn in (title, world_map, underground, classes, directions, enemies):
        fn(); print('ok', fn.__name__)
