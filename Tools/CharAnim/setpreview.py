"""python setpreview.py out.png Kind [clip ...]  -> contact sheet (rows = clip x direction) of a weapon set, x4, for review/docs"""
import sys
import numpy as np
from PIL import Image, ImageDraw
import weaponsets as WS


def sheet(data, clips, dirs=('Right', 'Down', 'Up', 'Left'), k=4, crop=(4, 10, 60, 64)):
    x0, y0, x1, y1 = crop
    rows = [(c, d) for c in clips for d in dirs if (c, d) in data]
    ncol = max(len(data[r][0]) for r in rows)
    cw, ch = (x1 - x0) * k, (y1 - y0) * k
    im = Image.new('RGBA', (110 + ncol * (cw + 2), len(rows) * (ch + 2)), (52, 64, 56, 255))
    dr = ImageDraw.Draw(im)
    for r, key in enumerate(rows):
        frames, fps, loop, ev = data[key]
        evs = {e['frame']: e['arg'] for e in ev}
        dr.text((4, r * (ch + 2) + 4), f'{key[0]}\n{key[1]}', fill=(255, 255, 255, 255))
        for i, f in enumerate(frames):
            cell = Image.fromarray(f[y0:y1, x0:x1], 'RGBA').resize((cw, ch), Image.NEAREST)
            bg = Image.new('RGBA', (cw, ch), (96, 120, 96, 255) if i % 2 == 0 else (90, 112, 90, 255))
            bg.alpha_composite(cell)
            im.paste(bg, (110 + i * (cw + 2), r * (ch + 2)))
            if i in evs:
                dr.text((112 + i * (cw + 2), r * (ch + 2) + 2), evs[i], fill=(255, 240, 120, 255))
    return im


if __name__ == '__main__':
    out, kind = sys.argv[1], sys.argv[2]
    clips = sys.argv[3:]
    R = WS.Renderer('Soldier')
    if kind in WS.KINDS:
        data = WS.render_set(R, WS.KINDS[kind], clips or None)
    else:
        data = WS.render_bow(R, WS.BOWS[kind])
    clips = clips or sorted({c for c, _ in data})
    sheet(data, clips).save(out)
    print(out)
