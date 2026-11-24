"""Menu / title background (320x180) composed only from project tiles + original woods sprites."""
import os
from PIL import Image
from lib import ROOT, save
from preview import autotile, load, T

WOODS = os.path.join(ROOT, '..', '..', 'pixel_16_woods v2 free', 'free_pixel_16_woods.png')
w = Image.open(WOODS).convert('RGBA')
BIG_TREE = w.crop((275, 10, 334, 80)); SMALL_TREE = w.crop((275, 92, 303, 128)); PINE = w.crop((308, 97, 333, 128))
ROCK = w.crop((224, 36, 240, 48)); BUSH = w.crop((225, 52, 239, 64)); MUSH = w.crop((228, 70, 238, 79))
STUMP = w.crop((231, 80, 250, 96)); LILY = w.crop((240, 132, 256, 144)); REED = w.crop((226, 132, 239, 144))

MAP_CLIFF = [
    "cccccccccccccccccccc",
    "cccccccccccccccccccc",
    "ccccccccc..ccccccccc",
    "cccc.............ccc",
    "....................",
    "....................",
    "....................",
    "....................",
    "....................",
    "....................",
    "....................",
    "....................",
]
MAP_WATER = [
    "....................",
    "....................",
    "....................",
    "....................",
    "..........www.......",
    ".........wwwww......",
    "........wwwwwww.....",
    "........wwwwww......",
    ".........wwww.......",
    "....................",
    "....................",
    "....................",
]
MAP_PATH = [
    "....................",
    "....................",
    "....................",
    "....................",
    "....................",
    "....................",
    "....................",
    "....pp..............",
    "....pppp............",
    ".....pppppp.........",
    "........ppp.........",
    "........ppp.........",
]


def compose():
    W, H = 20, 12
    img = Image.new('RGBA', (W * T, H * T))
    gf = load('Environments/Terrain/terrain_grass_fill_16x16.png')
    for y in range(H):
        for x in range(W):
            v = (x * 5 + y * 7) % 11
            v = 0 if v > 3 else v
            img.alpha_composite(gf.crop((v * T, 0, v * T + T, T)), (x * T, y * T))
    autotile(img, MAP_PATH, 'p', load('Tilesets/StonePath/tileset_stonepath_blob47_16x16.png'))
    autotile(img, MAP_WATER, 'w', load('Tilesets/Water/tileset_water_blob47_f0_16x16.png'))
    autotile(img, MAP_CLIFF, 'c', load('Tilesets/Cliff/tileset_cliff_blob47_16x16.png'))
    # waterfall from the cliff gap into the pond
    body = load('Environments/Water/water_waterfall_body_anim_32x16.png').crop((0, 0, 32, 16))
    top = load('Environments/Water/water_waterfall_top_anim_32x16.png').crop((0, 0, 32, 16))
    foam = load('Environments/Water/water_waterfall_foam_anim_48x16.png').crop((0, 0, 48, 16))
    img.alpha_composite(top, (144, 24)); img.alpha_composite(body, (144, 40)); img.alpha_composite(body, (144, 56))
    img.alpha_composite(foam, (136, 64))

    def put(spr, x, y):  # x,y = bottom-centre
        img.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height)))

    deco = lambda rel, i=0, cw=16, ch=16: load(rel).crop((i * cw, 0, i * cw + cw, ch))
    put(PINE, 20, 52); put(PINE, 296, 50); put(SMALL_TREE, 270, 56)
    put(BIG_TREE, 28, 140); put(BIG_TREE, 300, 150); put(SMALL_TREE, 236, 176)
    put(deco('Environments/Vegetation/veg_tree_dead_32x40.png', 0, 32, 40), 62, 104)
    put(deco('Environments/Decorations/deco_ruin_wall_32x32.png', 0, 32, 32), 100, 96)
    put(deco('Environments/Decorations/deco_ruin_pillar_16x32.png', 0, 16, 32), 72, 120)
    put(deco('Environments/Decorations/deco_demon_obelisk_anim_16x32.png', 2, 16, 32), 112, 124)
    put(deco('Props/prop_campfire_anim_16x16.png', 1), 264, 168)
    put(deco('Props/props_static_16x16.png', 4), 200, 176)  # sign
    put(deco('Props/props_static_16x16.png', 0), 232, 132)  # barrel
    put(deco('Props/props_static_16x16.png', 1), 244, 134)  # crate
    put(deco('Props/prop_chest_open_anim_16x16.png', 0), 262, 112)
    put(deco('Props/prop_torch_anim_16x32.png', 1, 16, 32), 216, 168)
    put(deco('Environments/Vegetation/veg_bush_large_32x24.png', 0, 32, 24), 120, 178)
    put(deco('Environments/Vegetation/veg_bushes_small_16x16.png', 0), 84, 160)
    put(deco('Environments/Vegetation/veg_log_fallen_32x16.png', 0, 32, 16), 270, 92)
    put(deco('Environments/Vegetation/veg_flowers_16x16.png', 1), 48, 170)
    put(deco('Environments/Vegetation/veg_flowers_16x16.png', 0), 176, 172)
    put(deco('Environments/Vegetation/veg_tallgrass_sway_anim_16x16.png', 0), 222, 92)
    put(deco('Environments/Vegetation/veg_tallgrass_sway_anim_16x16.png', 8), 116, 80)
    put(ROCK, 196, 104); put(MUSH, 44, 120); put(STUMP, 248, 76); put(BUSH, 92, 70)
    put(LILY, 150, 112); put(REED, 186, 116)
    for x, y in [(60, 84), (300, 110), (230, 62)]:
        put(deco('Environments/Ambient/amb_firefly_anim_8x8.png', 2, 8, 8), x, y)
    return img.crop((0, 0, 320, 180))


if __name__ == '__main__':
    im = compose()
    p = save(im, 'Environments/Backgrounds/bg_menu_forest_320x180.png')
    im.resize((960, 540), Image.NEAREST).save(os.path.join(os.environ.get('PREV', '.'), 'bg_prev.png'))
    print(p)
