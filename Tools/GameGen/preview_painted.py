"""Composites entities over the painted ground for review crops."""
import os, sys
from PIL import Image
import render_world2 as R
import world2 as w
ROOT = R.ROOT
GROUND = Image.open(os.path.join(ROOT, 'Assets', 'Art', 'World', 'ground_full_preview.png')).convert('RGBA')
T = 16


def zone(x0, y0, x1, y1):
    ter, ent = R.parse(os.path.join(ROOT, 'Assets', 'Game', 'Levels', 'World2.txt'))
    img = GROUND.crop((x0 * T, y0 * T, x1 * T, y1 * T)).copy()
    items = [(y, x, ent[y][x]) for y in range(max(0, y0-8), min(len(ent), y1+8)) for x in range(max(0, x0-5), min(len(ent[0]), x1+5)) if ent[y][x] != ' ']
    for y, x, c in sorted(items):
        s = R.sprite(c)
        if s is None: continue
        img.paste(s, ((x-x0)*T + 8 - s.width//2, (y-y0+1)*T - s.height), s)
    return img


if __name__ == '__main__':
    out = sys.argv[1]
    spots = {'pueblo_inicio': (0.52, 0.66), 'lago': (0.50, 0.50), 'ciudadela': (0.68, 0.18), 'picos': (0.30, 0.10),
             'pantano': (0.86, 0.72), 'volcan': (0.91, 0.55), 'bosque_corrupto': (0.11, 0.22), 'desierto_fuerte': (0.90, 0.28)}
    W_ = w.World(); W_.build(); spots_xy = {k: w.U(*v) for k, v in spots.items()}
    spots_xy['puerto'] = (W_.dock_end[0], W_.dock_end[1] - 3)
    for name, (x, y) in spots_xy.items():
        im = zone(x - 16, y - 10, x + 16, y + 10)
        im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(out, name + '.png'))
    full = GROUND.copy()
    full.resize((full.width // 3, full.height // 3), Image.BOX).save(os.path.join(out, 'mundo_suelo.png'))
    print('ok')
