"""Review sheets + animated GIF previews.
python preview.py <outdir> <Char> [category-filter...]"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from engine import OUT, CELL

CROP = (6, 14, 58, 62)


def load(char):
    man = json.load(open(os.path.join(OUT, char, f'{char}_animations.json')))
    for c in man['clips']:
        im = np.array(Image.open(os.path.join(OUT, char, c['file'])).convert('RGBA'))
        c['img'] = [im[:, i * CELL:(i + 1) * CELL] for i in range(c['frames'])]
    return man


def sheet(clips, k=3, bg=(150, 160, 150, 255)):
    cw, ch = (CROP[2] - CROP[0]) * k, (CROP[3] - CROP[1]) * k
    n = max(len(c['seq']) for c in clips)
    im = Image.new('RGBA', (140 + cw * n, ch * len(clips)), bg)
    d = ImageDraw.Draw(im)
    for r, c in enumerate(clips):
        d.text((4, r * ch + 4), f"{c['name']}\n{c['dir']}\n{c['frames']}f {c['fps']}fps", fill=(0, 0, 0, 255))
        for i, fi in enumerate(c['seq']):
            t = Image.fromarray(c['img'][fi]).crop(CROP).resize((cw, ch), Image.NEAREST)
            im.alpha_composite(t, (140 + i * cw, r * ch))
            d.line([(140 + i * cw, r * ch), (140 + i * cw, r * ch + ch)], fill=(120, 130, 120, 255))
            d.line([(140 + i * cw, r * ch + (52 - CROP[1]) * k), (140 + i * cw + cw, r * ch + (52 - CROP[1]) * k)], fill=(110, 120, 110, 255))
    return im


def gif(clips, path, k=4, cols=4, bg=(120, 170, 90)):
    """all clips play side by side, each at its own fps, on a grass-coloured background"""
    cw, ch = (CROP[2] - CROP[0]) * k, (CROP[3] - CROP[1]) * k
    rows = (len(clips) + cols - 1) // cols
    dt = 20  # ms
    total = 2400
    frames = []
    for t in range(0, total, dt * 4):
        im = Image.new('RGBA', (cw * cols, ch * rows + 0), bg + (255,))
        d = ImageDraw.Draw(im)
        for i, c in enumerate(clips):
            n = len(c['seq'])
            idx = int(t / 1000 * c['fps'])
            idx = idx % n if c['loop'] else min(idx % (n + 6), n - 1)
            f = Image.fromarray(c['img'][c['seq'][idx]]).crop(CROP).resize((cw, ch), Image.NEAREST)
            x, y = (i % cols) * cw, (i // cols) * ch
            im.alpha_composite(f, (x, y))
            d.text((x + 3, y + 2), f"{c['name']} {c['dir']}", fill=(0, 0, 0, 255))
        frames.append(im.convert('P', palette=Image.ADAPTIVE))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=dt * 4, loop=0, disposal=2)


if __name__ == '__main__':
    out, char = sys.argv[1], sys.argv[2]
    filt = sys.argv[3:]
    man = load(char)
    clips = [c for c in man['clips'] if not filt or any(f.lower() in c['name'].lower() for f in filt)]
    order = {'Down': 0, 'Up': 1, 'Left': 2, 'Right': 3}
    clips.sort(key=lambda c: (c['name'], order[c['dir']]))
    tag = '_'.join(filt) or 'all'
    sheet(clips).save(os.path.join(out, f'rev_{char}_{tag}.png'))
    print(len(clips))
