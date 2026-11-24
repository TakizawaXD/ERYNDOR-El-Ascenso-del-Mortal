"""Renders a level .txt with the real tiles/sprites (design preview, mirrors the Unity builder's rules)."""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ArtGen'))
from tiles import MASKS, DIRS, canon   # noqa: E402

ART = os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Art')
T = 16


def load(rel):
    return Image.open(os.path.join(ART, rel)).convert('RGBA')


def cell(sheet, i, w=16, h=16):
    cols = sheet.width // w
    return sheet.crop(((i % cols) * w, (i // cols) * h, (i % cols) * w + w, (i // cols) * h + h))


def parse(path):
    lines = open(path, encoding='utf-8').read().splitlines()
    t0 = lines.index('TERRAIN'); e0 = lines.index('ENTITIES')
    end = lines.index('REGIONS') if 'REGIONS' in lines else len(lines)
    return lines[t0 + 1:e0], lines[e0 + 1:end]


WOODS = Image.open(os.path.join(os.path.dirname(__file__), '..', '..', 'pixel_16_woods v2 free', 'free_pixel_16_woods.png')).convert('RGBA')
W = {'T': WOODS.crop((275, 10, 334, 80)), 't': WOODS.crop((275, 92, 303, 128)), 'i': WOODS.crop((308, 97, 333, 128)),
     'r': WOODS.crop((224, 36, 240, 48)), 'g': WOODS.crop((225, 52, 239, 64)), 'M': WOODS.crop((228, 70, 238, 79)),
     'Z': WOODS.crop((231, 80, 250, 96))}


def sprite_for(c):
    if c in W: return W[c]
    m = {
        'D': ('Environments/Vegetation/veg_tree_dead_32x40.png', 0, 32, 40), 'b': ('Environments/Vegetation/veg_bush_large_32x24.png', 0, 32, 24),
        'x': ('Props/props_static_16x16.png', 1, 16, 16), 'k': ('Props/props_static_16x16.png', 0, 16, 16), 'u': ('Props/props_static_16x16.png', 2, 16, 16),
        'S': ('Props/props_static_16x16.png', 4, 16, 16), 'G': ('Props/props_static_16x16.png', 6, 16, 16),
        'C': ('Props/prop_chest_open_anim_16x16.png', 0, 16, 16), 'L': ('Props/prop_torch_anim_16x32.png', 1, 16, 32),
        'F': ('Props/prop_campfire_anim_16x16.png', 1, 16, 16), 'l': ('Props/prop_lantern_post_16x32.png', 0, 16, 32),
        'R': ('Environments/Decorations/deco_ruin_wall_32x32.png', 0, 32, 32), 'I': ('Environments/Decorations/deco_ruin_pillar_16x32.png', 0, 16, 32),
        'O': ('Environments/Decorations/deco_demon_obelisk_anim_16x32.png', 2, 16, 32), 'f': ('Environments/Decorations/deco_fence_16x16.png', 1, 16, 16),
        'y': ('Environments/Vegetation/veg_flowers_16x16.png', 1, 16, 16), 'v': ('Environments/Vegetation/veg_tallgrass_sway_anim_16x16.png', 0, 16, 16),
        'n': ('Environments/Vegetation/veg_log_fallen_32x16.png', 0, 32, 16),
        'h': ('UI/Icons/ui_icons_items_16x16.png', 5, 16, 16), 'a': ('UI/Icons/ui_icons_items_16x16.png', 3, 16, 16), '$': ('UI/Icons/ui_icons_items_16x16.png', 7, 16, 16),
        'E': ('UI/ui_prompts_16x16.png', 2, 16, 16), 'X': ('Effects/fx_demon_summon_circle_anim_32x32.png', 0, 32, 32),
        'Y': ('Props/props_static_16x16.png', 4, 16, 16),
    }
    if c in m:
        rel, i, w, h = m[c]; return cell(load(rel), i, w, h)
    chars = {'P': ('Soldier', 'Idle/Soldier_Idle_Down.png'), 'o': ('Orc', 'Idle/Orc_Idle_Down.png'), 'd': ('Demon', 'Idle/Demon_Idle_Down.png'),
             'm': ('BloodMonster', 'Idle/BloodMonster_Idle_Down.png'), 'B': ('Demon', 'Idle/Demon_Idle_Down.png'),
             'K': ('Orc', 'Idle/Orc_Idle_Down.png'), 'Q': ('BloodMonster', 'Idle/BloodMonster_Idle_Down.png')}
    if c in chars:
        ch, rel = chars[c]
        im = cell(load(f'Characters/{ch}/{rel}'), 0, 64, 64).crop((0, 0, 64, 52))
        if c in 'BKQ': im = im.resize((128, 104), Image.NEAREST)
        return im
    return None


def autotile(img, grid, pred, sheet, H, Wd):
    for y in range(H):
        for x in range(Wd):
            if not pred(x, y): continue
            m = 0
            for b, (dx, dy) in DIRS.items():
                nx, ny = x + dx, y + dy
                if not (0 <= nx < Wd and 0 <= ny < H) or pred(nx, ny): m |= b
            i = MASKS.index(canon(m))
            img.alpha_composite(cell(sheet, i), (x * T, y * T))


def render(path):
    ter, ent = parse(path)
    H, Wd = len(ter), len(ter[0])
    img = Image.new('RGBA', (Wd * T, H * T))
    dirt = load('Environments/Terrain/terrain_dirt_fill_16x16.png')
    for y in range(H):
        for x in range(Wd):
            v = (x * 7 + y * 3) % 9
            img.alpha_composite(cell(dirt, v if v < 4 else 0), (x * T, y * T))
    tt = lambda x, y: ter[y][x]
    autotile(img, ter, lambda x, y: tt(x, y) in '."pwc=H', load('Tilesets/Grass/tileset_grass_blob47_16x16.png'), H, Wd)
    autotile(img, ter, lambda x, y: tt(x, y) == '"', load('Tilesets/TallGrass/tileset_tallgrass_blob47_16x16.png'), H, Wd)
    autotile(img, ter, lambda x, y: tt(x, y) == 'p', load('Tilesets/StonePath/tileset_stonepath_blob47_16x16.png'), H, Wd)
    autotile(img, ter, lambda x, y: tt(x, y) in 'w=H', load('Tilesets/Water/tileset_water_blob47_f0_16x16.png'), H, Wd)
    autotile(img, ter, lambda x, y: tt(x, y) == 'c', load('Tilesets/Cliff/tileset_cliff_blob47_16x16.png'), H, Wd)
    br = load('Environments/Decorations/deco_bridge_16x16.png')
    for y in range(H):
        for x in range(Wd):
            if ter[y][x] == '=':
                k = 0 if ter[y][x - 1] != '=' else 2 if ter[y][x + 1] != '=' else 1
                img.alpha_composite(cell(br, k), (x * T, y * T))
    # entities sorted by y (feet at the bottom of their cell)
    items = [(y, x, ent[y][x]) for y in range(H) for x in range(Wd) if ent[y][x] not in ' ."pwc=H']
    for y, x, c in sorted(items):
        s = sprite_for(c)
        if s is None: continue
        img.alpha_composite(s, (x * T + 8 - s.width // 2, (y + 1) * T - s.height))
    return img


if __name__ == '__main__':
    out = sys.argv[1]
    for name in sys.argv[2:]:
        im = render(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Game', 'Levels', name + '.txt'))
        im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(out, name + '.png'))
        print(name, im.size)
