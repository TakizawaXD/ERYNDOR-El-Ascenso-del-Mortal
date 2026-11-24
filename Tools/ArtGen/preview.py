"""Composes test scenes from the generated tiles to check seams / coherence."""
import os, sys
import numpy as np
from PIL import Image
from lib import ROOT
from tiles import MASKS, DIRS, canon, T

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '_preview')
os.makedirs(OUT, exist_ok=True)


def load(rel):
    return Image.open(os.path.join(ROOT, rel)).convert('RGBA')


def blob_tile(sheet, m):
    i = MASKS.index(canon(m))
    return sheet.crop(((i % 8) * T, (i // 8) * T, (i % 8) * T + T, (i // 8) * T + T))


def autotile(img, grid, ch, sheet):
    H, W = len(grid), len(grid[0])
    on = lambda x, y: (0 <= y < H and 0 <= x < W and grid[y][x] in ch) or not (0 <= y < H and 0 <= x < W)
    for y in range(H):
        for x in range(W):
            if grid[y][x] not in ch:
                continue
            m = 0
            for b, (dx, dy) in DIRS.items():
                if on(x + dx, y + dy):
                    m |= b
            img.alpha_composite(blob_tile(sheet, m), (x * T, y * T))


MAP_TERRAIN = [
    "..............................",
    "..gggggggggg......gggggggg....",
    ".ggggggggggggg...gggggggggg...",
    ".ggggggggggggggggggggggwwwgg..",
    ".gggggpppppgggggggggggwwwwwg..",
    ".gggggpgggpggggggggggwwwwwwg..",
    ".gggggpgggpppppppggggwwwwwgg..",
    "..ggggpgggggggggpgggggwwwggg..",
    "..gggggggggggggggpgggggggggg..",
    "...ggggggggg.....ggggggggg....",
    "..............................",
]
MAP_OVER = {  # extra layers by char on top of grass
}


def scene_terrain():
    W, H = len(MAP_TERRAIN[0]), len(MAP_TERRAIN)
    img = Image.new('RGBA', (W * T, H * T))
    dirt = load('Environments/Terrain/terrain_dirt_fill_16x16.png')
    for y in range(H):
        for x in range(W):
            v = (x * 7 + y * 3) % 9
            v = 0 if v > 3 else v
            img.alpha_composite(dirt.crop((v * T, 0, v * T + T, T)), (x * T, y * T))
    autotile(img, MAP_TERRAIN, 'gpw', load('Tilesets/Grass/tileset_grass_blob47_16x16.png'))
    autotile(img, MAP_TERRAIN, 'p', load('Tilesets/StonePath/tileset_stonepath_blob47_16x16.png'))
    autotile(img, MAP_TERRAIN, 'w', load('Tilesets/Water/tileset_water_blob47_f0_16x16.png'))
    return img


MAP_CLIFF = [
    "..................",
    "..ccccccc.........",
    "..ccccccccc.......",
    "..cccccccccc..cc..",
    "...ccc.cccccccccc.",
    "...ccc..ccccccccc.",
    "..........cccc....",
    "..................",
    "..................",
]
MAP_TALL = [
    "..................",
    "..................",
    "..................",
    "..................",
    "..................",
    "..................",
    "..tttt............",
    ".tttttt...........",
    "..ttt.............",
]


def scene_cliff():
    W, H = len(MAP_CLIFF[0]), len(MAP_CLIFF)
    img = Image.new('RGBA', (W * T, H * T))
    gf = load('Environments/Terrain/terrain_grass_fill_16x16.png')
    for y in range(H):
        for x in range(W):
            v = (x * 5 + y * 7) % 11
            v = 0 if v > 3 else v
            img.alpha_composite(gf.crop((v * T, 0, v * T + T, T)), (x * T, y * T))
    autotile(img, MAP_TALL, 't', load('Tilesets/TallGrass/tileset_tallgrass_blob47_16x16.png'))
    autotile(img, MAP_CLIFF, 'c', load('Tilesets/Cliff/tileset_cliff_blob47_16x16.png'))
    return img


def big(img, k=3):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


if __name__ == '__main__':
    big(scene_terrain()).save(os.path.join(OUT, 'scene_terrain.png'))
    big(scene_cliff()).save(os.path.join(OUT, 'scene_cliff.png'))
    for rel in ['Tilesets/Grass/tileset_grass_blob47_16x16.png', 'Tilesets/Water/tileset_water_blob47_f0_16x16.png',
                'Tilesets/Cliff/tileset_cliff_blob47_16x16.png']:
        im = load(rel); bg = Image.new('RGBA', im.size, (219, 164, 99, 255)); bg.alpha_composite(im)
        big(bg, 4).save(os.path.join(OUT, os.path.basename(rel)))
    print(OUT)
