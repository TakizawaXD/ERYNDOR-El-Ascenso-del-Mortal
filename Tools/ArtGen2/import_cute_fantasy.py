"""Imports the user's 'Cute Fantasy (Free)' pack pieces into Assets/Art/External/CuteFantasy (cut into named sheets).

  python import_cute_fantasy.py [pack dir]   (default: the user's desktop copy)

Licence of the free pack (read_me.txt): non-commercial projects only, may be modified, may NOT be redistributed.
The original files are only read, never changed.
"""
import os, shutil, sys
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else r'C:/Users/andre/OneDrive/Desktop/Cute_Fantasy_Free'
DST = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Art', 'External', 'CuteFantasy'))
os.makedirs(DST, exist_ok=True)


def load(rel): return Image.open(os.path.join(SRC, rel)).convert('RGBA')


def cells(sheet, coords, cw=16, ch=16):
    out = Image.new('RGBA', (cw * len(coords), ch), (0, 0, 0, 0))
    for i, (c, r) in enumerate(coords):
        out.alpha_composite(sheet.crop((c * 16, r * 16, c * 16 + cw, r * 16 + ch)), (i * cw, 0))
    return out


def save(im, name): im.save(os.path.join(DST, name)); print(name, im.size)


# animals: 2x2 cells of 32 px (row 0 idle, row 1 walk), facing left
for a in ('Chicken', 'Cow', 'Pig', 'Sheep'):
    save(load(f'Animals/{a}/{a}.png'), f'animal_{a.lower()}_32x32.png')

deco = load('Outdoor decoration/Outdoor_Decor_Free.png')
save(cells(deco, [(3, 1), (4, 1), (3, 2), (4, 2), (5, 1), (6, 1), (5, 2), (6, 2)]), 'cf_crops_16x16.png')      # carrot x4, wheat x4
save(cells(deco, [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 8), (1, 8), (0, 9), (1, 9), (0, 10), (1, 10),
                  (0, 11), (1, 11), (2, 7), (1, 2), (2, 2)]), 'cf_flora_16x16.png')                              # grass, flowers, mushroom, rocks
save(cells(deco, [(3, 0), (4, 0), (5, 0), (6, 0)]), 'cf_signs_16x16.png')
save(deco.crop((64, 64, 80, 112)), 'cf_lamp.png')
save(deco.crop((0, 112, 32, 128)), 'cf_log.png')
save(deco.crop((0, 32, 16, 48)), 'cf_stump.png')
save(load('Outdoor decoration/Oak_Tree.png'), 'cf_oak_tree.png')
save(load('Outdoor decoration/Oak_Tree_Small.png'), 'cf_oak_small_32x48.png')
save(load('Outdoor decoration/Fences.png'), 'cf_fences_16x16.png')
save(load('Outdoor decoration/House_1_Wood_Base_Blue.png'), 'cf_house_blue.png')
save(load('Outdoor decoration/Chest.png'), 'cf_chest.png')
save(load('Tiles/FarmLand_Tile.png'), 'cf_farmland_16x16.png')
shutil.copy(os.path.join(SRC, 'read_me.txt'), os.path.join(DST, 'LICENSE_CuteFantasy_Free.txt'))

# terrain tiles for the town maps (own folder: centred pivots for the Tilemap)
TILES = os.path.join(os.path.dirname(DST), 'CuteFantasyTiles')
os.makedirs(TILES, exist_ok=True)
for src, name in (('Path_Tile', 'cf_path_16x16'), ('Water_Tile', 'cf_water_16x16'), ('Cliff_Tile', 'cf_cliff_16x16'),
                  ('Beach_Tile', 'cf_beach_16x16'), ('Grass_Middle', 'cf_grass'), ('Path_Middle', 'cf_path_mid'), ('Water_Middle', 'cf_water_mid')):
    im = load(f'Tiles/{src}.png'); im.save(os.path.join(TILES, name + '.png')); print(name, im.size)
