"""Renders World2.txt with the new art kit (Assets/Art/World) - design preview of what Unity will build."""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ArtGen'))
from tiles import MASKS, DIRS, canon   # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
WA = os.path.join(ROOT, 'Assets', 'Art', 'World')
CH = os.path.join(ROOT, 'Assets', 'Art', 'Characters')
T = 16
_cache = {}


def L(rel, base=WA):
    k = (base, rel)
    if k not in _cache: _cache[k] = Image.open(os.path.join(base, rel)).convert('RGBA')
    return _cache[k]


def cell(s, i, w=16, h=16):
    cols = s.width // w
    return s.crop(((i % cols) * w, (i // cols) * h, (i % cols) * w + w, (i // cols) * h + h))


def parse(path):
    lines = open(path, encoding='utf-8').read().splitlines()
    t0, e0, r0 = lines.index('TERRAIN'), lines.index('ENTITIES'), lines.index('REGIONS')
    return lines[t0 + 1:e0], lines[e0 + 1:r0]


LAYERS = [   # (predicate chars, tileset, has centre variants)
    ('.fwcCFsvn=HD' , 'Tilesets/world_grass_blob_16x16.png', True),
    ('f', 'Tilesets/world_forestfloor_blob_16x16.png', False),
    ('v', 'Tilesets/world_corrupt_blob_16x16.png', False),
    ('nC', 'Tilesets/world_snow_blob_16x16.png', False),
    ('d', 'Tilesets/world_desert_blob_16x16.png', False),
    ('aLk', 'Tilesets/world_ash_blob_16x16.png', False),
    ('F', 'Tilesets/world_farm_blob_16x16.png', False),
    ('p', 'Tilesets/world_cobble_blob_16x16.png', False),
    ('w=H', 'Tilesets/world_water_blob_f0_16x16.png', False),
    ('s', 'Tilesets/world_swamp_blob_f0_16x16.png', False),
    ('L', 'Tilesets/world_lava_blob_f0_16x16.png', False),
    ('OD', 'Tilesets/world_ocean_blob_f0_16x16.png', False),
    ('c', 'Tilesets/world_cliff_blob_16x16.png', False),
    ('C', 'Tilesets/world_snowcliff_blob_16x16.png', False),
    ('k', 'Tilesets/world_ashcliff_blob_16x16.png', False),
]

SPR = {  # entity -> (file, frame index or None, cell w, cell h)
    'T': ('Nature/tree_oak.png',), 'U': ('Nature/tree_oak_b.png',), 't': ('Nature/tree_oak_small.png',), 'A': ('Nature/tree_autumn.png',),
    'V': ('Nature/tree_corrupt.png',), 'u': ('Nature/tree_corrupt_small.png',), 'i': ('Nature/tree_pine.png',), 'I': ('Nature/tree_pine_snow.png',),
    'k': ('Nature/tree_dead.png',), 'Y': ('Nature/tree_palm.png',),
    'g': ('Nature/bushes_26x22.png', 0, 26, 22), 'G': ('Nature/bushes_26x22.png', 1, 26, 22), 'q': ('Nature/bushes_26x22.png', 2, 26, 22),
    'y': ('Nature/plants_16x16.png', 0, 16, 16), 'z': ('Nature/plants_16x16.png', 1, 16, 16), 'M': ('Nature/plants_16x16.png', 3, 16, 16),
    'e': ('Nature/cattails.png',), 'l': ('Nature/lilypads_16x16.png', 0, 16, 16), 'Z': ('Nature/stump.png',), 'n': ('Nature/log.png',),
    'r': ('Nature/rock_small.png',), 'R': ('Nature/rock_big.png',), 'W': ('Nature/rock_snow.png',),
    '1': ('Structures/mountain_snow_a.png',), '2': ('Structures/mountain_snow_b.png',), '3': ('Structures/mountain_rock.png',),
    '4': ('Structures/mesa.png',), '5': ('Structures/volcano_big_anim_160x128.png', 0, 160, 128),
    'm': ('Structures/mountain_big_a.png',), '^': ('Structures/mountain_big_b.png',),
    '6': ('Structures/house_red.png',), '7': ('Structures/house_blue.png',), '8': ('Structures/house_thatch.png',),
    '9': ('Structures/castle_tower.png',), '#': ('Structures/castle_wall.png',), '0': ('Structures/watchtower.png',),
    'J': ('Structures/windmill_anim_76x108.png', 0, 76, 108), 'j': ('Structures/lighthouse.png',), 'x': ('Structures/dark_tower_anim_44x120.png', 0, 44, 120),
    'N': ('Structures/ruin_wall.png',), '!': ('Structures/ruin_pillar.png',), '~': ('Structures/boat.png',),
    '+': ('Structures/waterfall_anim_32x32.png', 0, 32, 32),
    '(': ('Props/props_16x16.png', 0, 16, 16), ')': ('Props/props_16x16.png', 1, 16, 16), 'S': ('Props/props_16x16.png', 2, 16, 16),
    '*': ('Props/props_16x16.png', 3, 16, 16), ';': ('Props/props_16x16.png', 4, 16, 16), 'C': ('Props/chest_anim_16x16.png', 0, 16, 16),
    '|': ('Props/torch_anim_16x34.png', 1, 16, 34), 'F': ('Props/campfire_anim_20x20.png', 1, 20, 20), '@': ('Props/well.png',),
    '$': ('Props/market_stall.png',), '/': ('Nature/fence_16x16.png', 1, 16, 16),
}
ACTORS = {'P': 'Soldier', 'o': 'Orc', 'b': 'BloodMonster', 'd': 'Demon', 'K': 'Orc', 'Q': 'BloodMonster', 'B': 'Demon'}


def sprite(c):
    if c in SPR:
        spec = SPR[c]
        s = L(spec[0])
        return s if len(spec) == 1 else cell(s, spec[1], spec[2], spec[3])
    if c in ACTORS:
        a = ACTORS[c]
        im = cell(L(f'{a}/Idle/{a}_Idle_Down.png', CH), 0, 64, 64).crop((0, 0, 64, 52))
        return im.resize((128, 104), Image.NEAREST) if c in 'KQB' else im
    if c == 'X':
        return cell(L('Effects/fx_demon_summon_circle_anim_32x32.png', os.path.join(ROOT, 'Assets', 'Art')), 0, 32, 32)
    if c in 'ha':
        return cell(L('UI/Icons/ui_icons_items_16x16.png', os.path.join(ROOT, 'Assets', 'Art')), 5 if c == 'h' else 3)
    return None


def render(path, region=None):
    ter, ent = parse(path)
    H, W = len(ter), len(ter[0])
    x0, y0, x1, y1 = region or (0, 0, W, H)
    img = Image.new('RGBA', ((x1 - x0) * T, (y1 - y0) * T))
    sand = L('Tilesets/world_sand_fill_16x16.png')
    for y in range(y0, y1):
        for x in range(x0, x1):
            v = (x * 7 + y * 13) % 11
            img.alpha_composite(cell(sand, v if v < 4 else 0), ((x - x0) * T, (y - y0) * T))
    for chars, rel, variants in LAYERS:
        sh = L(rel)
        pred = lambda x, y: ter[y][x] in chars
        for y in range(y0, y1):
            for x in range(x0, x1):
                if not pred(x, y): continue
                m = 0
                for b, (dx, dy) in DIRS.items():
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < W and 0 <= ny < H) or pred(nx, ny): m |= b
                i = MASKS.index(canon(m))
                if i == 46 and variants:
                    i = [46, 47, 46, 48, 46, 49, 50, 51, 46][(x * 7 + y * 13) % 9]
                img.alpha_composite(cell(sh, i), ((x - x0) * T, (y - y0) * T))
    br, dk = L('Structures/bridge_16x16.png'), L('Structures/dock_16x16.png')
    for y in range(y0, y1):
        for x in range(x0, x1):
            t = ter[y][x]
            if t == '=':
                k = 0 if ter[y][x - 1] != '=' else 2 if ter[y][x + 1] != '=' else 1
                img.alpha_composite(cell(br, k), ((x - x0) * T, (y - y0) * T))
            elif t == 'H':
                k = 3 if ter[y - 1][x] != 'H' else 5 if ter[y + 1][x] != 'H' else 4
                img.alpha_composite(cell(br, k), ((x - x0) * T, (y - y0) * T))
            elif t == 'D':
                k = 0 if ter[y][x - 1] != 'D' else 2 if ter[y][x + 1] != 'D' else 1
                img.alpha_composite(cell(dk, k), ((x - x0) * T, (y - y0) * T))
    items = [(y, x, ent[y][x]) for y in range(max(0, y0 - 6), min(H, y1 + 6)) for x in range(max(0, x0 - 4), min(W, x1 + 4)) if ent[y][x] != ' ']
    for y, x, c in sorted(items):
        s = sprite(c)
        if s is None: continue
        img.paste(s, ((x - x0) * T + 8 - s.width // 2, (y - y0 + 1) * T - s.height), s)
    return img


if __name__ == '__main__':
    out = sys.argv[1]
    path = os.path.join(ROOT, 'Assets', 'Game', 'Levels', 'World2.txt')
    im = render(path)
    im.save(os.path.join(out, 'world2_full.png'))
    im.resize((im.width // 4, im.height // 4), Image.BOX).save(os.path.join(out, 'world2_small.png'))
    print(im.size)
