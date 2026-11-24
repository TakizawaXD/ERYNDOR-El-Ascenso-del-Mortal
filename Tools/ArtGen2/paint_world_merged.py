"""Ground of the ONE merged map (2026-11-21): Tools/GameGen/merge_world.py -> World2.txt + Underground.txt.

  python Tools/ArtGen2/paint_world_merged.py            (everything, ~some minutes)
  python Tools/ArtGen2/paint_world_merged.py --tile 2 1  (paint one surface tile only and save a preview: quick look)

* The overworld (towns and Monte Ceniza included, they are part of its terrain now) is painted with the dark painter
  (painter_dark.DarkPainter) in tiles, because at 600x400 cells the painter's full-size noise caches would need many GB.
  TilePainter makes every tile use GLOBAL coordinates (noise, slab rows, cobble cells, dunes, strata), so the tiles meet
  without seams.
* Every cave of the underground is painted with the catacombs painter (catacombs_art.paint) from its raw layout in
  Underground.txt, tinted per cave (frost, blood, orc pits...). The rock between caves is left black.
Output: Assets/Art/World/Ground/ground_<cx>_<cy>.png (512 px chunks; all-black chunks are skipped),
        Assets/Art/World/world_map.png (1 px per cell, the SURFACE only - the map screen and minimap),
        Assets/Art/World/ground_full_preview.png (1/4 scale)
"""
import inspect, math, os, sys, textwrap, time
import numpy as np
import scipy.ndimage as nd
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import painter as PT           # noqa: E402
import painter_dark as PD      # noqa: E402

Image.MAX_IMAGE_PIXELS = None
T = PT.T
ROOT = PT.ROOT
LV = os.path.join(ROOT, 'Assets', 'Game', 'Levels')
OUT = PT.OUT
CHUNK = 512
TILE_W, TILE_H, MARGIN = 120, 100, 8
VOID = (9, 8, 11)
_NORM = {}


# ---------------------------------------------------------------------- global-coordinate painter
REPL = [
    ('np.mgrid[0:self.H, 0:self.W]', 'np.mgrid[self.oy:self.oy + self.H, self.ox:self.ox + self.W]'),
    ('np.mgrid[0:H, 0:W]', 'np.mgrid[self.oy:self.oy + H, self.ox:self.ox + W]'),
    ('np.arange(self.H)', 'np.arange(self.oy, self.oy + self.H)'),
    ('np.arange(self.W)', 'np.arange(self.ox, self.ox + self.W)'),
    ('gy, gx = self.H // S + 2, self.W // S + 2', 'gy, gx = self.FH // S + 2, self.FW // S + 2'),
    ('size=H // h_rng[0] + 8', 'size=self.FH // h_rng[0] + 8'),
]


def _global(cls, name):
    """re-compile a painter method with the coordinate expressions above made global"""
    fn = getattr(cls, name)
    src = textwrap.dedent(inspect.getsource(fn))
    n = 0
    for a, b in REPL:
        if a in src: src = src.replace(a, b); n += 1
    if n == 0: return None
    ns = {}
    exec(compile(src, f'<global {name}>', 'exec'), sys.modules[fn.__module__].__dict__, ns)
    return ns[name]


class TilePainter(PD.DarkPainter):
    def __init__(self, terrain, ox_cells, oy_cells, FW_cells, FH_cells, tid):
        super().__init__(terrain)
        self.ox, self.oy = ox_cells * T, oy_cells * T
        self.FW, self.FH = FW_cells * T, FH_cells * T
        self.tid = tid

    def noise(self, scale, seed):
        key = (scale, seed)
        if key in self._noise: return self._noise[key]
        lo, hi = _norm(scale, seed, self.FH, self.FW)
        r = np.random.default_rng(seed)
        acc = np.zeros((self.H, self.W), np.float32); amp = 1.0; tot = 0
        s = scale
        for _ in range(4):
            gh, gw = int(self.FH / s) + 3, int(self.FW / s) + 3
            g = r.random((gh, gw)).astype(np.float32)
            acc += _window(g, s, self.oy, self.ox, self.H, self.W) * amp
            tot += amp; amp *= 0.5; s = max(2, s / 2)
        n = np.clip((acc / tot - lo) / (hi - lo + 1e-6), 0, 1).astype(np.float32)
        self._noise[key] = n
        return n

    def white(self, seed):
        return np.random.default_rng(seed * 1000003 + self.tid).random((self.H, self.W)).astype(np.float32)

    def field(self, chars, blur=6.0, wob=0.13, wob_scale=24, seed=0):
        tm = np.array([[1.0 if c in chars else 0.0 for c in row] for row in self.ter], np.float32)
        tm = np.pad(tm, 2, mode='edge')
        up = nd.zoom(tm, T, order=1, grid_mode=True, mode='nearest')[2 * T:-2 * T, 2 * T:-2 * T]
        up = nd.gaussian_filter(up, blur)
        up += (self.noise(wob_scale, 900 + seed) - 0.5) * 2 * wob
        return up > 0.5


for _cls in (PT.Painter, PD.DarkPainter):
    for _name, _ in inspect.getmembers(_cls, inspect.isfunction):
        if _name in ('noise', 'white', 'field') or _name.startswith('__'): continue
        if _name not in _cls.__dict__: continue
        _f = _global(_cls, _name)
        if _f is not None and _name not in TilePainter.__dict__:
            # DarkPainter overrides win over Painter's: only take Painter's when DarkPainter has none
            if _cls is PT.Painter and _name in PD.DarkPainter.__dict__: continue
            setattr(TilePainter, _name, _f)


def _window(g, s, oy, ox, H, W):
    """pixels [oy, oy+H) x [ox, ox+W) of the bicubic upsampling of grid g by s, pixel p <-> coarse (p + .5) / s - .5
    (PIL's resize uses pixel centres, so a window of the grid lines up exactly with the same window of the whole map)"""
    def span(o, n, size):
        r0 = int(math.floor((o + 0.5) / s - 0.5)) - 4
        r0 -= r0 % 4
        r1 = int(math.ceil((o + n + 0.5) / s)) + 4
        r1 += (-(r1 - r0)) % 4
        return r0, np.arange(r0, r1) % size
    r0, rows = span(oy, H, g.shape[0])
    c0, cols = span(ox, W, g.shape[1])
    sub = np.ascontiguousarray(g[np.ix_(rows, cols)], np.float32)
    size = (int(round(len(cols) * s)), int(round(len(rows) * s)))
    up = np.asarray(Image.fromarray(sub, 'F').resize(size, Image.BICUBIC))
    y0, x0 = int(round(oy - r0 * s)), int(round(ox - c0 * s))
    return up[y0:y0 + H, x0:x0 + W]


def _norm(scale, seed, FH, FW):
    """global min/max of a noise key, sampled every 13 px over the whole map (same for every tile -> no seams)"""
    key = (scale, seed)
    if key in _NORM: return _NORM[key]
    r = np.random.default_rng(seed)
    ys = (np.arange(0, FH, 13) + 0.5)[:, None]
    xs = (np.arange(0, FW, 13) + 0.5)[None, :]
    acc = 0; amp = 1.0; tot = 0; s = scale
    for _ in range(4):
        gh, gw = int(FH / s) + 3, int(FW / s) + 3
        g = r.random((gh, gw)).astype(np.float32)
        cy = np.broadcast_to(ys / s - 0.5, (ys.shape[0], xs.shape[1]))
        cx = np.broadcast_to(xs / s - 0.5, (ys.shape[0], xs.shape[1]))
        acc = acc + nd.map_coordinates(g, [cy, cx], order=3, mode='grid-wrap') * amp
        tot += amp; amp *= 0.5; s = max(2, s / 2)
    v = acc / tot
    _NORM[key] = (float(v.min()), float(v.max()))
    return _NORM[key]


# ---------------------------------------------------------------------- data
def load():
    L = open(os.path.join(LV, 'World2.txt'), encoding='utf-8').read().splitlines()
    W, H = map(int, [l for l in L if l.startswith('SIZE ')][0].split()[1:3])
    SW, SH = map(int, [l for l in L if l.startswith('SURFACE ')][0].split()[1:3])
    t0, e0 = L.index('TERRAIN'), L.index('ENTITIES')
    return W, H, SW, SH, L[t0 + 1:t0 + 1 + H], L[e0 + 1:e0 + 1 + H]


def load_caves():
    L = open(os.path.join(LV, 'Underground.txt'), encoding='utf-8').read().splitlines()
    caves, i = [], 0
    while i < len(L):
        if L[i].startswith('CAVE '):
            p = L[i].split()
            mid, ox, oy, w, h, zone = p[1], int(p[2]), int(p[3]), int(p[4]), int(p[5]), p[6]
            tint = tuple(float(v) for v in p[7:10])
            rows = L[i + 2:i + 2 + h]
            zones = L[i + 3 + h:i + 3 + 2 * h]
            caves.append((mid, ox, oy, w, h, zone, tint, rows, zones))
            i += 3 + 2 * h
        else:
            i += 1
    return caves


def paint_surface_tile(ter, SW, SH, tx, ty, tid):
    x0, y0 = tx * TILE_W, ty * TILE_H
    x1, y1 = min(SW, x0 + TILE_W), min(SH, y0 + TILE_H)
    rows = []
    for y in range(y0 - MARGIN, y1 + MARGIN):
        yy = min(SH - 1, max(0, y))
        r = ter[yy]
        rows.append(''.join(r[min(SW - 1, max(0, x))] for x in range(x0 - MARGIN, x1 + MARGIN)))
    p = TilePainter(rows, x0 - MARGIN, y0 - MARGIN, SW, SH, tid)
    img = p.paint()
    m = MARGIN * T
    return img[m:m + (y1 - y0) * T, m:m + (x1 - x0) * T], (x0, y0)


def _tile_job(a):
    return paint_surface_tile(*a)


def main():
    t = time.time()
    W, H, SW, SH, ter, ent = load()
    only = None
    if len(sys.argv) > 3 and sys.argv[1] == '--tile': only = (int(sys.argv[2]), int(sys.argv[3]))
    full = np.zeros((H * T, W * T, 3), np.uint8); full[:] = VOID
    caves_only = '--caves-only' in sys.argv            # keep the painted surface (its chunks), repaint the underground only
    if caves_only:
        for f in os.listdir(OUT):
            if not (f.startswith('ground_') and f.endswith('.png')): continue
            cx, cy = map(int, f[7:-4].split('_'))
            if cx * CHUNK >= SW * T: continue
            im = np.asarray(Image.open(os.path.join(OUT, f)).convert('RGB'))
            full[cy * CHUNK:cy * CHUNK + im.shape[0], cx * CHUNK:cx * CHUNK + im.shape[1]] = im
        only = (-1, -1)
    nty, ntx = math.ceil(SH / TILE_H), math.ceil(SW / TILE_W)
    jobs = [(tx, ty) for ty in range(nty) for tx in range(ntx) if not only or (tx, ty) == only]
    workers = int(os.environ.get('PAINT_WORKERS', '3'))
    args = [(ter, SW, SH, tx, ty, ty * 97 + tx) for (tx, ty) in jobs]
    if workers > 1 and len(args) > 1:
        import multiprocessing as mp
        with mp.Pool(workers) as pool:
            for img, (x0, y0) in pool.imap_unordered(_tile_job, args):
                full[y0 * T:y0 * T + img.shape[0], x0 * T:x0 * T + img.shape[1]] = img[:, :, :3]
                print(f'  surface tile at {x0},{y0} done ({round(time.time() - t)} s)', flush=True)
    else:
        for a in args:
            img, (x0, y0) = _tile_job(a)
            full[y0 * T:y0 * T + img.shape[0], x0 * T:x0 * T + img.shape[1]] = img[:, :, :3]
            print(f'  surface tile at {x0},{y0} done ({round(time.time() - t)} s)', flush=True)
    if only and only != (-1, -1):
        x0, y0 = only[0] * TILE_W * T, only[1] * TILE_H * T
        out = os.path.join(ROOT, 'Tools', 'ArtGen2', 'previews', f'merged_tile_{only[0]}_{only[1]}.png')
        Image.fromarray(full[y0:y0 + TILE_H * T, x0:x0 + TILE_W * T]).save(out); print('preview', out); return
    # ---- the underground
    import catacombs_art as CA
    for (mid, ox, oy, w, h, zone, tint, rows, zones) in load_caves():
        Tm = [list(r) for r in rows]
        Rg = zones if zone == '-' else [zone * w for _ in range(h)]
        img, _ = CA.paint(w, h, Tm, Rg)
        rgb = img[:, :, :3].astype(np.float32) * np.array(tint, np.float32)
        solid = np.array([[c == '#' for c in r] for r in rows])
        solid_px = np.repeat(np.repeat(solid, T, 0), T, 1)
        rgb[solid_px & (img[:, :, :3].sum(axis=2) < 6)] = VOID
        full[oy * T:(oy + h) * T, ox * T:(ox + w) * T] = rgb.clip(0, 255).astype(np.uint8)
        print('  cave', mid, w, 'x', h)
    # ---- chunks
    os.makedirs(OUT, exist_ok=True)
    keep = set()
    for cy in range(0, H * T, CHUNK):
        for cx in range(0, W * T, CHUNK):
            part = full[cy:cy + CHUNK, cx:cx + CHUNK]
            if (part == np.array(VOID, np.uint8)).all(): continue
            name = f'ground_{cx // CHUNK}_{cy // CHUNK}.png'
            Image.fromarray(part).save(os.path.join(OUT, name)); keep.add(name)
    for f in os.listdir(OUT):                               # chunks of the old, smaller map that no longer exist
        base = f[:-5] if f.endswith('.meta') else f
        if base.startswith('ground_') and base.endswith('.png') and base not in keep: os.remove(os.path.join(OUT, f))
    surf = full[:SH * T, :SW * T]
    PD.world_map(surf, [r[:SW] for r in ent[:SH]], os.path.join(OUT, '..', 'world_map.png'))
    Image.fromarray(full).resize((W * T // 4, H * T // 4), Image.BOX).save(os.path.join(OUT, '..', 'ground_full_preview.png'))
    print('chunks', len(keep), 'size', full.shape, 'secs', round(time.time() - t, 1))


if __name__ == '__main__':
    main()
