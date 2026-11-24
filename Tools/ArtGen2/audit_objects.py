"""Audit of every NON-character image (2026-11-21): scenery, props, structures, nature, interiors, tiles, item icons,
interface and effects (everything under Assets/Art except Characters / Animations).

  python Tools/ArtGen2/audit_objects.py         -> Documentation/AUDITORIA_OBJETOS.md data + Documentation/auditoria_objetos.json
  python Tools/ArtGen2/audit_objects.py --fix   also removes stray pixels from props / structures / nature / furniture

Per image:
  meta       no Unity .meta (never imported)
  slicing    a "_WxH" sheet whose size is not a multiple of its cell, or with empty cells in an animation
  empty      nothing drawn
  stray      isolated single pixels (dirt) on props, structures, nature, furniture, catacombs
  alpha      semi-transparent pixels on solid objects (pixel art should be 0/255; glows, fog, water, FX and UI allowed)
  base       objects drawn with their base pivot: transparent rows under the drawing make them float above their
             foot point / sort wrong against the player
  pivot      objects that stand on the ground but import with a centred pivot (folder missing in the importer rules)
  scale      objects far out of proportion with the 16 px grid / the ~20 px tall characters
  unused     images no code, level or tool references (obsolete leftovers)
Plus, across the project:
  refs       image paths written in the builders (WOne / WSheet / One / Sheet / Specs / PROP lines) that do not exist
  collider   box colliders (GameBuilder.World.cs Specs) wider than the drawing they belong to (invisible walls)
"""
import json, os, re, sys
from collections import defaultdict
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ART = os.path.join(ROOT, 'Assets', 'Art')
DOC = os.path.join(ROOT, 'Documentation')
FIX = '--fix' in sys.argv
SOLID = ('/World/Props/', '/World/Structures/', '/World/Nature/', '/World/Interiors/Furniture/', '/World/Catacombs/', '/Props/',
         '/Environments/Vegetation/', '/Environments/Decorations/', '/World/Arena/')
GROUNDED = SOLID
BASE_PIVOT_DIRS = ('/Vegetation/', '/Props/', '/Decorations/', '/World/Nature/', '/World/Structures/', '/World/Interiors/Furniture/', '/External/CuteFantasy/')
SOFT = ('glow', 'light', 'fog', 'shadow', 'water', 'glint', 'rain', 'spore', 'fx_', 'magic', 'aura', 'smoke', 'title', 'map', 'flash', 'ring', 'circle')
FLAT = ('rune', 'crack', 'plate', 'hole', 'grate', 'rubble', 'ledge', 'spike', 'circle', 'carpet', 'rug', 'floor', 'mat')


def cell_of(name):
    m = re.findall(r'_(\d+)x(\d+)', name)
    return (int(m[-1][0]), int(m[-1][1])) if m else None


def stray(a):
    on = a > 0
    p = np.pad(on, 1)
    nb = sum(p[1 + dy:1 + dy + on.shape[0], 1 + dx:1 + dx + on.shape[1]] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
    return on & (nb == 0)


def referenced_names():
    """every image file name mentioned by code, levels or tools (cheap text search)"""
    text = []
    for base in ('Assets/Game/Editor', 'Assets/Game/Scripts', 'Assets/Editor', 'Tools'):
        for dp, _, fs in os.walk(os.path.join(ROOT, base)):
            for f in fs:
                if f.endswith(('.cs', '.py')): text.append(open(os.path.join(dp, f), encoding='utf-8', errors='ignore').read())
    for f in ('World2.txt', 'Interiors.txt', 'Maps.txt'):
        p = os.path.join(ROOT, 'Assets', 'Game', 'Levels', f)
        if os.path.exists(p): text.append(open(p, encoding='utf-8', errors='ignore').read())
    return '\n'.join(text)


def main():
    refs_text = referenced_names()
    rows, issues = [], defaultdict(list)
    for dp, _, fs in os.walk(ART):
        rel_dir = dp.replace('\\', '/')
        if '/Characters' in rel_dir or '/Animations' in rel_dir: continue
        for f in fs:
            if not f.endswith('.png'): continue
            p = os.path.join(dp, f); rel = p.replace('\\', '/').split('/Assets/')[-1]
            o = {'file': rel, 'issues': []}
            name = f[:-4]
            if not os.path.exists(p + '.meta'): o['issues'].append('meta')
            im = np.asarray(Image.open(p).convert('RGBA'))
            a = im[:, :, 3]
            h, w = a.shape
            if not a.any(): o['issues'].append('empty')
            c = cell_of(name)
            if c:
                cw, ch = c
                if w % cw or h % ch: o['issues'].append(f'slicing: {w}x{h} no es múltiplo de {cw}x{ch}')
                elif '_anim' in name:
                    empties = [i for i in range((w // cw) * (h // ch)) if not a[(i // (w // cw)) * ch:(i // (w // cw) + 1) * ch, (i % (w // cw)) * cw:(i % (w // cw) + 1) * cw].any()]
                    n_cells = (w // cw) * (h // ch)
                    # an empty last cell of a one-shot effect (it fades out) or the pause frames of a twinkle are by design
                    real = [i for i in empties if not ((name.startswith(('fx_', 'water_glint')) and (i == n_cells - 1 or 'glint' in name)))]
                    if real: o['issues'].append(f'slicing: celdas vacías {real[:6]}')
            solid = any(s in '/' + rel for s in SOLID) and not any(k in name for k in SOFT)
            ground = '/World/Ground/' in rel or '/Maps/' in rel
            if solid and a.any() and not name.startswith(('arena_telegraph', 'arena_wave', 'arena_chain', 'arena_flames', 'fire_anim')):
                st = stray(a)
                if st.sum():
                    o['issues'].append(f'stray: {int(st.sum())} px sueltos')
                    if FIX:
                        g = im.copy(); g[st] = 0; Image.fromarray(g).save(p); o['fixed'] = int(st.sum())
                semi = (a > 0) & (a < 200)
                rows_all = np.nonzero(a.any(axis=1))[0]
                lum = im[:, :, :3].astype(int).sum(axis=2)
                yy = np.arange(h)[:, None].repeat(w, 1)
                shadow = semi & (lum < 150) & (yy >= rows_all.min() + 0.6 * (rows_all.max() - rows_all.min()))   # drawn ground shadow
                faint = (semi & ~shadow).sum()
                if faint > max(8, 0.02 * (a > 0).sum()) and not name.startswith(('candle', 'torch', 'fire', 'brazier', 'bonfire', 'campfire')):
                    o['issues'].append(f'alpha: {int(faint)} px semitransparentes')
                if not c and not any(k in name for k in FLAT):
                    rows_ = np.nonzero(a.any(axis=1))[0]
                    pad = h - 1 - rows_.max()
                    if pad > 2: o['issues'].append(f'base: {pad} filas vacías bajo el dibujo (flota sobre su punto de apoyo)')
                    if not any(d in '/' + rel for d in BASE_PIVOT_DIRS) and not ('/World/Catacombs/' in rel) and not ('/Arena/' in rel and name.startswith(('arena_chain', 'arena_telegraph', 'arena_wave'))):
                        o['issues'].append('pivot: objeto de suelo importado con el pivote en el centro')
                    hgt = rows_.max() - rows_.min() + 1
                    if hgt > 160 or (hgt < 6 and w > 6): o['issues'].append(f'scale: {hgt} px de alto')
            dynamic = ('fx_', 'animal_', 'room_', 'arena_floor_', '_blob')       # names the builders put together in code
            if not ground and not any(k in name for k in dynamic) and name not in refs_text and not any(k in refs_text for k in (re.sub(r'_anim.*|_\d+x\d+.*|_9s\d+', '', name),)):
                o['issues'].append('unused')
            for k in o['issues']: issues[k.split(':')[0]].append(rel)
            rows.append(o)
    # ---- references written in the builders that do not exist
    missing = []
    editor = ''.join(open(os.path.join(dp, f), encoding='utf-8').read() for dp, _, fs in os.walk(os.path.join(ROOT, 'Assets', 'Game', 'Editor')) for f in fs if f.endswith('.cs'))
    consts = {'WA': 'Assets/Art/World/', 'PROPS2': 'Props/', 'CF': 'Assets/Art/External/CuteFantasy/', 'CFT': 'Assets/Art/External/CuteFantasyTiles/'}
    for m in re.finditer(r'W(?:One|Sheet)\("([^"]+\.png)"\)', editor):
        if not os.path.exists(os.path.join(ART, 'World', m.group(1))): missing.append('Art/World/' + m.group(1))
    for m in re.finditer(r'new Spec\("([^"]+\.png)"', editor):
        if not os.path.exists(os.path.join(ART, 'World', m.group(1))): missing.append('Art/World/' + m.group(1))
    for m in re.finditer(r'(?<![A-Za-z])(?:One|Sheet)\("(Assets/[^"]+\.png)"\)', editor):
        if not os.path.exists(os.path.join(ROOT, m.group(1))): missing.append(m.group(1))
    lv = open(os.path.join(ROOT, 'Assets', 'Game', 'Levels', 'World2.txt'), encoding='utf-8').read()
    for spr in sorted(set(re.findall(r'^PROP (\S+) ', lv, re.M))):
        if not os.path.exists(os.path.join(ART, 'World', 'Catacombs', spr + '.png')): missing.append(f'Art/World/Catacombs/{spr}.png (PROP)')
    # ---- colliders wider than their drawing (Specs in GameBuilder.World.cs)
    wide = []
    for m in re.finditer(r"\{ '(.)', new Spec\(\"([^\"]+)\",\s*([\d.]+)f", editor):
        ch_, file_, colw = m.group(1), m.group(2), float(m.group(3))
        pth = os.path.join(ART, 'World', file_)
        if not os.path.exists(pth): continue
        im = np.asarray(Image.open(pth).convert('RGBA'))
        c = cell_of(os.path.basename(file_)[:-4])
        cw = c[0] if c else im.shape[1]
        a = im[:, :cw, 3]
        cols = np.nonzero(a.any(axis=0))[0]
        drawn = (cols.max() - cols.min() + 1) / 16 if len(cols) else 0
        if colw > drawn + 0.15: wide.append(f"'{ch_}' {file_}: colisión {colw} > dibujo {drawn:.2f} unidades")
    res = {'images': rows, 'missing_refs': sorted(set(missing)), 'wide_colliders': wide, 'totals': {k: len(v) for k, v in issues.items()}}
    os.makedirs(DOC, exist_ok=True)
    json.dump(res, open(os.path.join(DOC, 'auditoria_objetos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('images', len(rows), '· issues', res['totals'], '· missing refs', len(res['missing_refs']), '· wide colliders', len(wide),
          '· fixed px', sum(o.get('fixed', 0) for o in rows))
    return res


if __name__ == '__main__':
    main()
