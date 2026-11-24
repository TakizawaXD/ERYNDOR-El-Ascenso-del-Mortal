"""Paints the ground of every separate map (towns, Monte Ceniza) listed in Assets/Game/Levels/Maps.txt.

Uses the same painter as the overworld (painter_dark.DarkPainter when present, else painter.Painter) so the towns
match the world's look. It only imports the painters, never changes them.
Output per map: Assets/Art/World/Maps/<MapId>/ground_<cx>_<cy>.png (512 px chunks) + map.png (1 px per tile, for the
map screen and the minimap); Tools/ArtGen2/previews/<MapId>.png shows the whole map with the entities marked.
usage: python Tools/ArtGen2/paint_maps.py [MapId ...]
"""
import os, sys, time
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import painter as PT                     # noqa: E402
try:
    import painter_dark as PD            # noqa: E402
    PainterClass, world_map = PD.DarkPainter, PD.world_map
except Exception as ex:                  # the dark painter is being edited elsewhere: fall back to the original look
    print('painter_dark unavailable (%s), using painter.Painter' % ex)
    PD = None
    PainterClass = PT.Painter

    def world_map(img, ent_rows, out):
        h, w = len(ent_rows), len(ent_rows[0])
        small = np.array(Image.fromarray(img).resize((w, h), Image.BOX)).astype(np.float32)
        small = (small * 1.25 + 8).clip(0, 255)
        for y, row in enumerate(ent_rows):
            for x, c in enumerate(row):
                if c in 'TUtAVuiIkY': small[y, x] *= 0.55
                elif c in '#9x0': small[y, x] = (158, 40, 53)
        Image.fromarray(small.astype(np.uint8)).save(out)

ROOT = PT.ROOT
LV = os.path.join(ROOT, 'Assets', 'Game', 'Levels')
MAPS = os.path.join(ROOT, 'Assets', 'Art', 'World', 'Maps')


def town_map(img, ents, out):
    """like the world map, plus houses and big buildings drawn as roofs so the town plan reads at a glance"""
    world_map(img, ents, out)
    im = np.array(Image.open(out).convert('RGB')).astype(np.int32)
    roof = {'6': (176, 66, 58), '7': (70, 98, 160), '8': (186, 150, 82), 'J': (200, 190, 160), 'j': (230, 230, 220),
            '5': (120, 40, 30), '$': (230, 190, 70), 'F': (255, 160, 60), '@': (120, 160, 200)}
    for y, row in enumerate(ents):
        for x, c in enumerate(row):
            if c in '678':
                im[max(0, y - 3):y + 1, max(0, x - 2):x + 3] = roof[c]
            elif c in roof:
                im[y, x] = roof[c]
    Image.fromarray(im.clip(0, 255).astype(np.uint8)).save(out)


def paint(mid):
    t = time.time()
    path = os.path.join(LV, mid + '.txt')
    lines = open(path, encoding='utf-8').read().splitlines()
    ter = PT.parse(path)
    e0 = lines.index('ENTITIES')
    ents = lines[e0 + 1:e0 + 1 + len(ter)]
    out = os.path.join(MAPS, mid)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.startswith('ground_') and f.endswith('.png'): os.remove(os.path.join(out, f))
    p = PainterClass(ter, seed=3)
    img = p.paint()
    n = 0
    for cy in range(0, p.H, PT.CHUNK):
        for cx in range(0, p.W, PT.CHUNK):
            Image.fromarray(img[cy:cy + PT.CHUNK, cx:cx + PT.CHUNK]).save(os.path.join(out, f'ground_{cx // PT.CHUNK}_{cy // PT.CHUNK}.png'))
            n += 1
    town_map(img, ents, os.path.join(out, 'map.png'))
    prev = img.copy()
    for y, row in enumerate(ents):
        for x, c in enumerate(row):
            if c != ' ':
                prev[y * 16 + 6:y * 16 + 10, x * 16 + 6:x * 16 + 10] = (255, 40, 200) if c in '678J9#j5' else (255, 255, 255)
    pv = os.path.join(ROOT, 'Tools', 'ArtGen2', 'previews')
    os.makedirs(pv, exist_ok=True)
    Image.fromarray(prev).resize((p.W // 2, p.H // 2), Image.NEAREST).save(os.path.join(pv, mid + '.png'))
    print(mid, 'chunks', n, 'size', img.shape, 'secs', round(time.time() - t, 1))


if __name__ == '__main__':
    cat = open(os.path.join(LV, 'Maps.txt'), encoding='utf-8').read().splitlines()
    ids = [l.split()[1] for l in cat if l.startswith('MAP ') and l.split()[2] != 'world']
    for mid in (sys.argv[1:] or ids):
        paint(mid)
