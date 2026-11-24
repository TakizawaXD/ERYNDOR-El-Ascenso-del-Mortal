"""ERYNDOR — redesigned overworld (2026-11-21): 360x240 tiles, the regions of the Eryndor lore.

Builds on world2.py (same terrain/entity letters, same helpers, same output file World2.txt so every tool and the
Unity builder keep working) and adds:
  * a continent shaped by noise, with bays, islands, beaches and sea cliffs
  * regions grown from seeds (organic borders), each with its own terrain and dressing
  * mountain ridges with passes, rivers from the glaciers to the sea, lakes, a waterfall terrace, lava rivers
  * towns (footprints for City_Valle / City_Ciudadela / City_Puerto), Aurelith's temples, cemeteries, ruins, shrines,
    the Great Tree of Eldoria, Valgrimm's frozen castle, the Forbidden Tower, the orc fortress, the volcano + seal
  * one entrance per boss dungeon (E), bonfires (F) at crossroads, entrances and dangerous places
  * locked passes (L) with regional keys (p), lever shortcuts (v), hidden glades with treasure
New ENTITY letters (handled by GameBuilder.Eryndor.cs):
  E dungeon entrance   H gravestone   O shrine statue   D great tree   L locked gate   p ancient key   v lever gate
Writes Assets/Game/Levels/World2.txt (world) + World3.json (towns, entrances, gates, keys, POIs) for maps.py.
usage: python Tools/GameGen/world3.py <project root>
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
import world2 as W2

W, H = 720, 480                       # 2026-11-21: one single map - towns, volcano and underground all live in it
AF = (W * H) / (360 * 240)            # area factor: the old densities were tuned for 360x240
LF = W / 360                          # length factor
SURF = lambda n: int(round(n * AF))
LEVELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Assets', 'Game', 'Levels')


def map_size(mid, default):
    """(w, h) of a town / zone map file, so its footprint in the world is exactly its size (merge_world.py stamps it)"""
    try:
        for l in open(os.path.join(LEVELS_DIR, mid + '.txt'), encoding='utf-8'):
            if l.startswith('SIZE '): return tuple(map(int, l.split()[1:3]))
    except OSError:
        pass
    return default
W2.W, W2.H = W, H                     # the shared helpers read the module size
noise = W2.noise
REGIONS = {
    'a': 'VALLES DE VALTHERION', 'b': 'BOSQUE ETERNO DE ELDORIA', 'c': 'AURELITH, LA CIUDAD SAGRADA',
    'd': 'NOXHEIM, TIERRAS DE SOMBRAS', 'e': 'TIERRAS HELADAS DE VALGRIMM', 'f': 'DESIERTO DE LOS ANTIGUOS',
    'g': 'DRAKMOR, TIERRAS DE FUEGO', 'h': 'LA TORRE PROHIBIDA', 'i': 'REINO DE VALTHERION', 'j': 'RUINAS ETERNAS',
}
W2.REGIONS = REGIONS
W2.BLOCK_E |= set('EHODLv')


def U(fx, fy): return int(fx * W), int(fy * H)


# region seeds (fractions of the map) - like the Eryndor map: frozen north, forbidden tower NE, capital W,
# eternal forest in the middle, volcanic Drakmor E, desert SE, sacred Aurelith S, shadow lands SW, ruins on the E coast
SEEDS = [('e', .28, .10), ('e', .46, .09), ('e', .14, .12), ('h', .80, .12), ('h', .66, .10),
         ('i', .14, .34), ('a', .26, .54), ('a', .32, .38), ('b', .48, .34), ('b', .54, .50), ('b', .42, .46),
         ('c', .50, .80), ('c', .40, .70), ('d', .14, .74), ('d', .22, .88), ('f', .74, .74), ('f', .84, .62),
         ('g', .78, .38), ('g', .68, .28), ('j', .93, .52), ('j', .93, .80)]


class World3(W2.World):
    def __init__(self):
        super().__init__()
        self.meta = {'towns': {}, 'entrances': [], 'gates': [], 'keys': [], 'levers': [], 'pois': [], 'seal': None}

    # ------------------------------------------------------------------ helpers
    def poi(self, kind, name, x, y):
        self.meta['pois'].append({'kind': kind, 'name': name, 'x': x, 'row': y})

    def clear_area(self, x0, y0, x1, y1, ter=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if self.inb(x, y):
                    self.e[y][x] = None
                    if ter and self.t[y][x] not in 'O': self.t[y][x] = ter

    def road(self, pts, width=2, mat='_', wig=1.5, seed=0):
        S = self
        def put(x, y, d):
            if not S.inb(x, y): return
            t = S.t[y][x]
            if t == 'w': S.t[y][x] = '=' if abs(d[0]) >= abs(d[1]) else 'H'
            elif t in 'sL': S.t[y][x] = mat
            elif t in 'O=HDp': return
            elif t in 'cCk': S.t[y][x] = mat                  # roads cut passes through ridges
            else: S.t[y][x] = mat
            if S.e[y][x] in W2.BLOCK_E: S.e[y][x] = None
        S.line(pts, width, put, wig, seed)

    def ridge(self, pts, width, mat, seed, gaps=()):
        """impassable mountain ridge (cliff terrain) with passes left open at the given points"""
        S = self
        def put(x, y, d):
            if not S.inb(x, y) or S.t[y][x] in 'Ow': return
            if any(abs(x - gx) <= 2 and abs(y - gy) <= 2 for gx, gy in gaps): return
            S.t[y][x] = mat
        S.line(pts, width, put, 2.5, seed)

    def river(self, pts, width, seed, mat='w'):
        S = self
        def put(x, y, d):
            if S.inb(x, y) and S.t[y][x] not in 'O': S.t[y][x] = mat
        S.line(pts, width, put, 2.8, seed)

    def ring_of(self, cx, cy, rad, chars, n, seed, allow='._fnvda'):
        r = random.Random(seed)
        for k in range(n):
            a = r.random() * math.tau; d = rad * (0.4 + 0.6 * r.random())
            x, y = int(cx + math.cos(a) * d), int(cy + math.sin(a) * d * 0.7)
            if self.free(x, y, allow): self.E(x, y, r.choice(chars))

    # ------------------------------------------------------------------ build
    def build(self):
        S = self
        # ---- continent
        for y in range(H):
            for x in range(W):
                fx, fy = x / W, y / H
                n = noise(x, y, 3) * 0.10 + noise(x * 2.3, y * 2.3, 9) * 0.04
                d = ((fx - 0.5) / 0.47) ** 4 + ((fy - 0.5) / 0.455) ** 4
                bay = ((fx - 0.06) / 0.10) ** 2 + ((fy - 0.60) / 0.07) ** 2 < 1 + n * 3       # western bay
                bay |= ((fx - 0.60) / 0.07) ** 2 + ((fy - 0.99) / 0.08) ** 2 < 1 + n * 3       # southern cove
                bay |= ((fx - 0.99) / 0.05) ** 2 + ((fy - 0.36) / 0.10) ** 2 < 1 + n * 3       # eastern gulf
                if d > 1 + n * 3 or bay:
                    S.t[y][x] = 'O'; S.r[y][x] = 'j'
        isl = [(.05, .16, 6, 4), (.08, .94, 7, 4), (.95, .90, 6, 4), (.97, .12, 5, 4), (.30, .97, 5, 3)]
        for k, (fx, fy, rx, ry) in enumerate(isl):
            S.blob(*U(fx, fy), rx, ry, lambda x, y: S.T(x, y, '.'), 0.25, 80 + k)
        # ---- regions (nearest seed, warped by noise)
        for y in range(H):
            for x in range(W):
                if S.t[y][x] == 'O': continue
                fx, fy = x / W + noise(x, y, 21) * 0.035, y / H + noise(x, y, 22) * 0.035
                best = min(SEEDS, key=lambda s: (fx - s[1]) ** 2 + (fy - s[2]) ** 2)
                S.r[y][x] = best[0]
        # ---- biome ground
        for y in range(H):
            for x in range(W):
                if S.t[y][x] == 'O': continue
                rid = S.r[y][x]; nz = noise(x, y, 11); nz2 = noise(x * 1.7, y * 1.7, 12)
                S.t[y][x] = {
                    'e': 'n' if nz > -0.45 else '.',
                    'h': 'v' if nz > -0.3 else 'f',
                    'i': '.' if nz < 0.5 else 'f',
                    'a': 'f' if nz > 0.42 else '.',
                    'b': 'f' if nz > -0.35 else '.',
                    'c': '.' if nz < 0.45 else 'f',
                    'd': 'f' if nz > -0.1 else ('v' if nz2 > 0.2 else '.'),
                    'f': 'd',
                    'g': 'a',
                    'j': '.' if nz < 0.2 else '_',
                }[rid]
        # beaches, sea cliffs on the west (Valtherion) and south-west (Noxheim)
        for y in range(H):
            for x in range(W):
                if S.t[y][x] != 'O' and S.near(x, y, 2, 'O'):
                    S.t[y][x] = 'c' if (S.r[y][x] in 'id' and not S.near(x, y, 1, 'O') and noise(x, y, 31) > -0.2) else '_'
        # ---- mountains: the Valgrimm wall (north), the Drakmor ridge (east), the Aurelith terraces (south)
        S.ridge([U(.05, .20), U(.20, .22), U(.34, .21), U(.50, .18), U(.60, .16)], 3, 'C', 41, gaps=[U(.30, .21), U(.50, .18)])
        S.ridge([U(.62, .20), U(.64, .34), U(.62, .48), U(.66, .58)], 3, 'k', 42, gaps=[U(.63, .27), U(.62, .45)])
        S.ridge([U(.30, .64), U(.40, .62), U(.52, .66), U(.62, .70)], 2, 'c', 43, gaps=[U(.45, .63), U(.56, .67)])
        for k in range(SURF(14)):                                  # snowy plateaus and crags in Valgrimm
            x, y = S.rng.randint(int(W * .06), int(W * .56)), S.rng.randint(4, int(H * .17))
            S.blob(x, y, S.rng.uniform(3, 7), S.rng.uniform(2, 3.5), lambda x, y: S.T(x, y, 'C') if S.t[y][x] in 'n.' else None, 0.2, 100 + k)
        for k in range(SURF(10)):                                  # basalt crags in Drakmor
            x, y = S.rng.randint(int(W * .66), int(W * .88)), S.rng.randint(int(H * .24), int(H * .50))
            S.blob(x, y, S.rng.uniform(2, 5), S.rng.uniform(1.5, 3), lambda x, y: S.T(x, y, 'k') if S.t[y][x] == 'a' else None, 0.2, 120 + k)
        # ---- water: glacier river -> Eldoria lake -> Aurelith falls -> southern sea; western river; eastern river
        S.river([U(.30, .06), U(.31, .15), U(.36, .26), U(.44, .34), U(.48, .40)], 3, 51)
        lx, ly = U(.50, .42)
        S.blob(lx, ly, 20 * LF, 11 * LF, lambda x, y: S.T(x, y, 'w'), 0.18, 52)                 # Lago de Eldoria
        S.blob(lx + 3, ly - 1, 6, 4, lambda x, y: S.T(x, y, '.'), 0.1, 53)              # island shrine
        S.river([U(.52, .47), U(.50, .56), U(.46, .62), U(.45, .70), U(.47, .80), U(.49, .97)], 3, 54)
        S.river([U(.28, .30), U(.20, .40), U(.12, .46), U(.04, .50)], 2, 55)
        S.river([U(.56, .38), U(.60, .44), U(.70, .52), U(.86, .50), U(.96, .48)], 2, 56)
        fl = U(.46, .25)
        S.blob(fl[0], fl[1], 7 * LF, 4 * LF, lambda x, y: S.T(x, y, 'w'), 0.15, 57)               # frozen lake (Valgrimm)
        for k in range(SURF(8)):
            x, y = S.rng.randint(int(W * .38), int(W * .62)), S.rng.randint(int(H * .26), int(H * .56))
            if S.r[y][x] == 'b': S.blob(x, y, S.rng.uniform(2, 4), S.rng.uniform(1.5, 3), lambda x, y: S.T(x, y, 'w') if S.t[y][x] in '.f' else None, 0.3, 140 + k)
        ox_, oy_ = U(.80, .74)
        S.blob(ox_, oy_, 4 * LF, 3 * LF, lambda x, y: S.T(x, y, 'w'), 0.2, 58)                   # desert oasis
        for k in range(SURF(30)):                                  # Noxheim marshes
            x, y = S.rng.randint(int(W * .05), int(W * .30)), S.rng.randint(int(H * .66), int(H * .93))
            if S.r[y][x] == 'd' and S.t[y][x] != 'O':
                S.blob(x, y, S.rng.uniform(2, 5), S.rng.uniform(1.5, 3), lambda x, y: S.T(x, y, 's') if S.t[y][x] in '.fv' else None, 0.3, 160 + k)
        vx, vy = U(.80, .27)                                       # Drakmor: the Monte Ceniza map is stamped around here
        zw, zh = map_size('Zone_MonteCeniza', (80, 72))
        zx0, zy0 = vx - zw // 2, vy - zh // 2
        S.meta['zone'] = {'map': 'Zone_MonteCeniza', 'rect': [zx0, zy0, zx0 + zw - 1, zy0 + zh - 1]}
        S.river([(zx0 + zw - 5, zy0 + zh), U(.88, .42), U(.90, .48)], 2, 59, 'L')
        for k in range(SURF(7)):
            cx, cy = vx + S.rng.randint(-zw, zw), zy0 + zh + S.rng.randint(2, 30)
            if S.inb(cx, cy) and abs(cx - vx) > 6:
                S.blob(cx, cy, S.rng.uniform(1.5, 3.5), S.rng.uniform(1.2, 2.5), lambda x, y: S.T(x, y, 'L') if S.t[y][x] == 'a' else None, 0.3, 170 + k)
        # waterfall terrace where the great river drops into Aurelith (a cliff band across it)
        wy = U(0, .66)[1]
        for y in range(wy, wy + 2):
            for x in range(U(.30, 0)[0], U(.62, 0)[0]):
                if S.t[y][x] == 'w': S.t[y][x] = 'c'
        # farmland around the villages
        for (fx, fy, w_, h_) in [(.22, .50, 9, 5), (.30, .58, 7, 4), (.20, .30, 8, 5), (.36, .44, 6, 4), (.44, .74, 7, 4)]:
            x0, y0 = U(fx, fy)
            for y in range(y0, y0 + h_):
                for x in range(x0, x0 + w_):
                    if S.inb(x, y) and S.t[y][x] in '.f': S.t[y][x] = 'F'

        # ---------------------------------------------------------- towns (footprints cut out into their own maps)
        def town(mid, fx, fy, w, h, build):
            # the footprint is the town map's own size: merge_world.py stamps the whole town map in here
            w, h = map_size(mid, (w + 1, h + 1)); w -= 1; h -= 1
            cx, cy = U(fx, fy); x0, y0 = cx - w // 2, cy - h // 2
            S.clear_area(x0, y0, x0 + w, y0 + h, '.')
            build(x0, y0, w, h)
            S.meta['towns'][mid] = [x0, y0, x0 + w, y0 + h]
            return cx, cy
        def valle(x0, y0, w, h):
            for (dx, dy, c) in [(6, 5, '6'), (13, 4, '7'), (24, 6, '8'), (31, 4, '6'), (8, 14, '8'), (27, 15, '7'), (18, 17, 'J')]:
                S.E(x0 + dx, y0 + dy, c)
            for x in range(x0, x0 + w + 1): S.T(x, y0 + h // 2, '_')                    # main street across
            for y in range(y0, y0 + h + 1): S.T(x0 + w // 2, y, '_')
        def ciudadela(x0, y0, w, h):
            for y in range(y0, y0 + h + 1):
                for x in range(x0, x0 + w + 1): S.T(x, y, 'p') if (x - x0 + y - y0) % 7 == 0 else None
            for x in range(x0, x0 + w + 1, 2):
                for y in (y0, y0 + h):
                    if abs(x - (x0 + w // 2)) > 2: S.E(x, y, '#')
            for y in range(y0, y0 + h + 1, 2):
                if abs(y - (y0 + h // 2)) > 1: S.E(x0, y, '#'); S.E(x0 + w, y, '#')
            for (dx, dy) in [(0, 0), (w, 0), (0, h), (w, h), (w // 2 - 5, h // 2 - 3), (w // 2 + 5, h // 2 - 3), (w // 2, h // 2 - 5)]:
                S.E(x0 + dx, y0 + dy, '9')
            for x in range(x0, x0 + w + 1): S.T(x, y0 + h // 2, 'p')
            for y in range(y0, y0 + h + 1): S.T(x0 + w // 2, y, 'p')
        def puerto(x0, y0, w, h):
            for (dx, dy, c) in [(3, 2, '6'), (9, 1, '7'), (14, 3, '8')]: S.E(x0 + dx, y0 + dy, c)
            for x in range(x0, x0 + w + 1): S.T(x, y0 + h // 2, '_')
        vcx, vcy = town('City_Valle', .26, .50, 38, 22, valle)
        ccx, ccy = town('City_Ciudadela', .15, .32, 30, 18, ciudadela)
        # the port faces south (its map ends in the sea): it sits on the southern coast, its harbour over the ocean
        pw, ph = map_size('City_Puerto', (74, 54))
        pcol = int(W * .70)
        coast = next((y for y in range(H - 1, 0, -1) if S.t[y][pcol] != 'O'), H - 20)
        py0 = min(coast - (ph - 20), H - ph - 2)
        pcx, pcy = town('City_Puerto', pcol / W, (py0 + ph // 2) / H, pw - 1, ph - 1, puerto)
        bx, by = pcx + pw // 2 + 4, pcy + ph // 2 - 16
        S.meta['dock'] = [bx, by]

        # ---------------------------------------------------------- roads (sand; cobble in Valtherion)
        R = S.road
        R([(vcx, vcy), U(.22, .42), (ccx, ccy + 9)], 3, 'p', 1.0, 1)                         # village -> capital (royal road)
        R([(vcx + 19, vcy), U(.36, .48), U(.44, .50), U(.52, .55), U(.58, .60)], 2, '_', 1.5, 2)  # -> Eldoria south
        R([U(.36, .48), U(.40, .38), U(.46, .30), U(.50, .19), U(.48, .10)], 2, '_', 1.5, 3)     # -> Valgrimm pass
        R([U(.30, .21), U(.26, .14), U(.18, .08)], 2, '_', 1.5, 4)                                # western pass -> frozen castle
        R([(ccx + 15, ccy), U(.24, .30), U(.30, .21)], 2, 'p', 1.0, 5)                           # capital -> north pass
        R([(vcx, vcy + 11), U(.24, .66), U(.18, .76), U(.14, .84)], 2, '_', 1.5, 6)             # -> Noxheim
        R([U(.24, .66), U(.34, .70), U(.45, .63), U(.48, .74), U(.50, .82)], 2, '_', 1.5, 7)    # -> Aurelith
        R([U(.58, .60), U(.62, .45), U(.63, .27), U(.70, .22), U(.78, .16)], 2, '_', 1.5, 8)    # -> Forbidden Tower
        R([U(.62, .45), U(.70, .44), U(.74, .46)], 2, '_', 1.0, 9)                               # -> Drakmor (seal road)
        R([U(.58, .60), U(.66, .66), U(.74, .70), U(.82, .66), (pcx - 10, pcy)], 2, '_', 1.5, 10)  # -> desert -> port
        R([U(.50, .82), U(.62, .80), U(.74, .80)], 2, '_', 1.5, 11)                              # Aurelith -> desert
        R([(pcx, pcy - 5), U(.90, .54), U(.88, .46)], 2, '_', 1.5, 12)                          # port -> eastern ruins
        # bridge to the lake island
        S.straighten_bridges(); S.drop_stray_bridges(); S.bridge_pads()

        # ---------------------------------------------------------- landmarks & points of interest
        P = lambda fx, fy: U(fx, fy)
        # start: by the village east gate
        S.E(vcx, vcy, 'P')                 # reachability seed only: the village map stamped here brings its own start
        S.E(vcx + 42, vcy + 4, 'S', 'VALLES DE VALTHERION. LA ALDEA DEL VALLE ESTÁ AL OESTE; EL BOSQUE ETERNO DE ELDORIA, AL ESTE. LAS HOGUERAS GUARDAN TU PROGRESO.')
        # Great Tree of Eldoria + forest shrines
        gx, gy = P(.54, .30)
        S.clear_area(gx - 4, gy - 3, gx + 4, gy + 3, '.')
        S.E(gx, gy, 'D'); S.poi('tree', 'GRAN ÁRBOL DE ELDORIA', gx, gy)
        S.E(gx + 3, gy + 2, 'S', 'EL GRAN ÁRBOL DE ELDORIA. DICEN QUE SUS RAÍCES TOCAN LAS CRIPTAS DE TODO EL REINO.')
        for (fx, fy) in [(.44, .40), (.58, .52)]:
            x, y = P(fx, fy); p_ = S.place(x, y, 'O', '.f')
            if p_: S.poi('shrine', 'SANTUARIO DE ELDORIA', *p_)
        x, y = lx + 3, ly - 1; S.E(x, y, 'O'); S.poi('shrine', 'SANTUARIO DEL LAGO', x, y)
        # Aurelith: the sacred city of temples (open ruins in the world)
        ax_, ay_ = P(.50, .80)
        S.clear_area(ax_ - 10, ay_ - 6, ax_ + 10, ay_ + 6, '.')
        for y in range(ay_ - 6, ay_ + 7):
            for x in range(ax_ - 10, ax_ + 11):
                if abs(x - ax_) <= 1 or abs(y - ay_) <= 1 or (abs(x - ax_) <= 5 and abs(y - ay_) <= 3): S.T(x, y, 'p')
        for (dx, dy, c) in [(-8, -5, '9'), (8, -5, '9'), (-8, 5, '0'), (8, 5, '0'), (-4, -2, '!'), (4, -2, '!'), (-4, 2, '!'), (4, 2, '!'), (0, -5, 'O')]:
            S.E(ax_ + dx, ay_ + dy, c)
        S.poi('city', 'AURELITH, LA CIUDAD SAGRADA', ax_, ay_)
        S.E(ax_ + 2, ay_ + 7, 'S', 'AURELITH. LOS PRIMORDIALES LEVANTARON ESTOS TEMPLOS ANTES DE QUE EXISTIERA EL REINO.')
        # Valgrimm frozen castle
        fx_, fy_ = P(.16, .07)
        S.clear_area(fx_ - 8, fy_ - 3, fx_ + 8, fy_ + 5, 'n')
        for x in range(fx_ - 8, fx_ + 9, 2): S.E(x, fy_ - 3, '#')
        for (dx, dy) in [(-8, -3), (8, -3), (-3, -1), (3, -1)]: S.E(fx_ + dx, fy_ + dy, '9')
        S.poi('ruin', 'CASTILLO HELADO DE VALGRIMM', fx_, fy_)
        # Forbidden Tower
        tx_, ty_ = P(.82, .10)
        S.clear_area(tx_ - 4, ty_ - 2, tx_ + 4, ty_ + 4, 'v')
        S.E(tx_, ty_, 'x'); S.E(tx_ - 3, ty_ + 2, 'N'); S.E(tx_ + 3, ty_ + 2, 'N')
        S.poi('tower', 'LA TORRE PROHIBIDA', tx_, ty_)
        # Eternal Ruins (east coast)
        for k, (fx, fy) in enumerate([(.90, .44), (.94, .58), (.91, .72)]):
            x, y = P(fx, fy)
            S.ring_of(x, y, 5, 'N!', 7, 300 + k, '._d')
            S.poi('ruin', 'RUINAS ETERNAS', x, y)
        # desert: arch ruins and the old kings' obelisks
        for k, (fx, fy) in enumerate([(.72, .66), (.86, .78)]):
            x, y = P(fx, fy); S.ring_of(x, y, 4, 'N!4', 6, 320 + k, 'd'); S.poi('ruin', 'RUINAS DE LOS ANTIGUOS', x, y)
        # lighthouse by the port
        dbx, dby = S.meta['dock']
        p_ = S.place(dbx, dby + 6, 'j', '_.')
        if p_: S.poi('tower', 'FARO DE LAS RUINAS', *p_)

        # ---- cemeteries (Valtherion royal cemetery, Noxheim graveyards)
        def cemetery(cx, cy, w, h, seed, name):
            S.clear_area(cx - w, cy - h, cx + w, cy + h, '.' if S.r[cy][cx] != 'd' else 'f')
            r = random.Random(seed)
            for y in range(cy - h + 1, cy + h, 2):
                for x in range(cx - w + 1, cx + w, 2):
                    if r.random() < 0.7: S.E(x, y, 'H')
            for x in range(cx - w, cx + w + 1): S.E(x, cy - h, '/')
            for k in range(3): S.E(cx - w - 1 + k * (w + 1), cy + h + 1, 'k')
            S.poi('cemetery', name, cx, cy)
        cemetery(*P(.36, .56), 5, 3, 401, 'CEMENTERIO REAL DE VALTHERION')
        cemetery(*P(.12, .80), 5, 3, 402, 'CEMENTERIO DE LOS CONDENADOS')
        cemetery(*P(.24, .92), 4, 2, 403, 'TUMBAS SIN NOMBRE')

        # ---------------------------------------------------------- dungeon entrances (one per boss) + their bonfires
        def entrance(mid, kind, name, fx, fy, boss, deco, seed):
            x, y = P(fx, fy)
            S.clear_area(x - 3, y - 3, x + 3, y + 4)
            for yy in range(y, y + 4): S.T(x, yy, '_'); S.T(x + 1, yy, '_')
            S.E(x, y, 'E')
            S.meta['entrances'].append({'map': mid, 'kind': kind, 'name': name, 'x': x, 'row': y, 'boss': boss})
            S.poi('dungeon', name, x, y)
            S.ring_of(x, y + 1, 5, deco, 8, seed)
            f = S.place(x + 4, y + 4, 'F', '._fndva_', 4)                           # a bonfire right before the descent
            # a path from the entrance to the nearest road
            return x, y
        entrance('Dungeon_ReySepultado', 'crypt', 'CATACUMBAS DEL REY OLVIDADO', .36, .52, 'boss_R', 'HHk', 501)
        entrance('Dungeon_Invocador', 'crypt', 'CATACUMBA DE LOS CONDENADOS', .12, .76, 'boss_I', 'HHVk', 502)
        entrance('Dungeon_Sangre', 'tower', 'TORRE CARMESÍ', .26, .82, 'boss_Q', 'kVq', 503)
        entrance('Dungeon_Orco', 'cave', 'FOSOS DE GUERRA ORCOS', .82, .70, 'boss_K', '(4)', 504)
        entrance('Dungeon_Escarcha', 'cave', 'CRIPTA DE ESCARCHA', .38, .08, 'boss_F', 'IW', 505)
        # orc fortress walls around the war pits
        ox, oy = P(.82, .70)
        for x in range(ox - 7, ox + 8, 2):
            S.E(x, oy - 6, '#')
            if abs(x - ox) > 2: S.E(x, oy + 7, '#')
        for y in range(oy - 6, oy + 8, 2): S.E(ox - 7, y, '#'); S.E(ox + 7, y, '#')
        S.E(ox - 7, oy - 6, '0'); S.E(ox + 7, oy - 6, '0')
        # crimson tower over the blood dungeon
        sx, sy = P(.26, .82); S.E(sx, sy - 3, 'x')
        # volcano + the seal of Monte Ceniza: the zone map is stamped in its footprint (cliffs all round), its only way in is
        # the south gate, right behind the seal
        zx0, zy0, zx1, zy1 = S.meta['zone']['rect']
        S.clear_area(zx0 - 1, zy0 - 1, zx1 + 1, zy1 + 1, 'a')
        for y in range(zy0, zy1 + 1):
            for x in range(zx0, zx1 + 1): S.r[y][x] = 'g'
        sealx, sealy = vx - 1, zy1 + 2
        for y in range(zy1 + 1, zy1 + 8):
            for x in range(vx - 3, vx + 2):
                S.T(x, y, 'a'); S.e[y][x] = None
        S.road([U(.74, .46), (vx - 1, zy1 + 7)], 2, '_', 1.0, 13)
        for (dx, dy) in [(0, 0), (0, 1), (1, 0), (1, 1)]: S.E(sealx + dx, sealy + dy, 'X')
        S.E(sealx - 3, sealy + 3, 'S', 'EL SELLO DE DRAKMOR. CAERÁ CUANDO EL JEFE ORCO Y LA MADRE DE SANGRE HAYAN SIDO DERROTADOS EN SUS MAZMORRAS.')
        S.meta['seal'] = {'x': sealx, 'row': sealy, 'volcano': [vx, vy]}
        S.poi('dungeon', 'MONTE CENIZA (SANTUARIO DE DRAKMOR)', vx, zy1 - 4)

        # ---------------------------------------------------------- locked passes, keys, lever shortcuts, secret glades
        def enclose(pred, key, name, mat='k'):
            """wall a whole area with cliffs; the road that entered it becomes the one locked gateway"""
            inside = {(x, y) for y in range(H) for x in range(W) if S.t[y][x] != 'O' and pred(x, y)}
            border = [(x, y) for (x, y) in inside
                      if any((x + dx, y + dy) not in inside and S.inb(x + dx, y + dy) and S.t[y + dy][x + dx] != 'O'
                             for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
            roads = [(x, y) for (x, y) in border if S.t[y][x] in '_p=H']
            gate = None
            if roads:
                # the crossing closest to the area's centre of mass along the main road
                mx = sum(x for x, _ in inside) / len(inside); my = sum(y for _, y in inside) / len(inside)
                gate = min(roads, key=lambda c: (c[0] - mx) ** 2 + (c[1] - my) ** 2)
            for (x, y) in border:
                if gate and (x, y) == gate: continue
                S.t[y][x] = mat
                if S.e[y][x] is not None and S.e[y][x] not in 'EF': S.e[y][x] = None
            if gate:
                gx_, gy_ = gate
                S.t[gy_][gx_] = '_'
                S.E(gx_, gy_, 'L'); S.meta['gates'].append({'x': gx_, 'row': gy_, 'key': key, 'name': name})
            return gate
        # the Forbidden Tower lands and the northern Eternal Ruins are closed behind locked gates
        enclose(lambda x, y: S.r[y][x] == 'h', 'key_torre', 'PORTÓN DE LA TORRE PROHIBIDA')
        enclose(lambda x, y: S.r[y][x] == 'j' and y < H * 0.60 and x > W * 0.84, 'key_ruinas', 'PUERTA DE LAS RUINAS ETERNAS', 'c')
        def key(fx, fy, kid, name, region_hint):
            x, y = P(fx, fy); p_ = S.place(x, y, 'p', '._fndv', 5)
            if p_: S.meta['keys'].append({'x': p_[0], 'row': p_[1], 'key': kid, 'name': name})
        # secret glades (closed by forest, a narrow gap) - each with a key or a treasure
        def glade(fx, fy, seed, content):
            x, y = P(fx, fy)
            S.blob(x, y, 7, 5, lambda xx, yy: S.E(xx, yy, random.Random(xx * 7 + yy).choice('TTUVk')) if S.free(xx, yy, '.fvndn') else None, 0.1, seed)
            S.clear_area(x - 3, y - 2, x + 3, y + 2, '.')
            S.clear_area(x + 3, y, x + 8, y)                                               # the narrow way in
            S.E(x, y, content); S.poi('secret', 'CLARO OCULTO', x, y)
            return x, y
        kx, ky = glade(.08, .70, 701, 'C')                                                # Noxheim: the Onyx key
        S.meta['keys'].append({'x': kx, 'row': ky, 'key': 'key_torre', 'name': 'LLAVE DE ÓNICE', 'chest': True})
        kx, ky = glade(.58, .88, 702, 'C')                                                # Aurelith: the Lighthouse key
        S.meta['keys'].append({'x': kx, 'row': ky, 'key': 'key_ruinas', 'name': 'LLAVE DEL FARO', 'chest': True})
        glade(.40, .14, 703, 'C'); glade(.70, .58, 704, 'C')                              # treasure only
        # lever shortcuts: a cliff gap closed by an iron gate that opens from one side
        def lever(fx, fy, lid, name):
            x, y = P(fx, fy)
            for yy in range(y - 3, y + 4):
                for xx in range(x - 1, x + 2):
                    if S.inb(xx, yy) and S.t[yy][xx] not in 'O': S.t[yy][xx] = 'c'
            S.T(x, y, '.'); S.T(x, y - 1, '.'); S.T(x, y + 1, '.')
            S.E(x, y, 'v'); S.meta['levers'].append({'x': x, 'row': y, 'id': lid, 'name': name})
        lever(.30, .62, 'lever_aurelith', 'ATAJO DE LOS VALLES A AURELITH')
        lever(.66, .64, 'lever_desierto', 'ATAJO DE ELDORIA AL DESIERTO')

        # ---------------------------------------------------------- hamlets, mills, watchtowers, roadside shrines
        def hamlet(fx, fy, seed, name):
            x, y = P(fx, fy)
            r = random.Random(seed)
            S.clear_area(x - 6, y - 4, x + 6, y + 4)
            for (dx, dy) in [(-4, -2), (3, -3), (-1, 2), (5, 2)][: 2 + r.randint(0, 2)]:
                S.E(x + dx, y + dy, r.choice('678'))
            S.place(x, y, '@', '._f', 2)
            if r.random() < 0.6: S.place(x + 7, y - 3, 'J', '._fF', 3)
            for k in range(4): S.place(x - 6 + k * 4, y + 5, r.choice('(/)*'), '._f', 1)
            S.poi('village', name, x, y)
        for k, (fx, fy, name) in enumerate([(.10, .50, 'ALDEA DE LOS PASTORES'), (.32, .30, 'MOLINOS DEL NORTE'),
                                            (.20, .60, 'GRANJAS DEL SUR'), (.92, .64, 'PESCADORES DE LAS RUINAS'),
                                            (.38, .78, 'ERMITA DE AURELITH'), (.60, .76, 'CARAVASAR DEL DESIERTO'),
                                            (.56, .22, 'REFUGIO DE LOS CAZADORES'), (.08, .30, 'FARO OCCIDENTAL')]):
            hamlet(fx, fy, 600 + k, name)
        for k, (fx, fy) in enumerate([(.30, .44), (.18, .54), (.42, .58), (.60, .56), (.70, .62), (.24, .24), (.56, .70), (.86, .60)]):
            x, y = P(fx, fy); p_ = S.place(x, y, '0' if k % 2 == 0 else 'O', '._fdn', 4)
            if p_ and k % 2: S.poi('shrine', 'SANTUARIO DEL CAMINO', *p_)
        # ---------------------------------------------------------- bonfires: crossroads, safe spots, dangerous places
        for f in [(.22, .42), (.36, .48), (.40, .38), (.46, .30), (.30, .21), (.20, .10), (.48, .12), (.52, .55), (.58, .60),
                  (.62, .45), (.70, .22), (.80, .14), (.74, .44), (.66, .66), (.78, .78), (.88, .58), (.46, .70), (.50, .74),
                  (.24, .66), (.16, .86), (.12, .60), (.10, .40), (.92, .76)]:
            x, y = P(*f)
            for k in range(12):
                xx, yy = x + k % 4 - 1, y + k // 4
                if S.free(xx, yy, '._fndav') and not S.near(xx, yy, 1, 'wOsL') and not S.near(xx, yy, 2, 'kc'):
                    S.E(xx, yy, 'F'); break
        # waterfalls under the Aurelith terrace and wherever a river leaves a cliff
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if S.t[y][x] == 'w' and S.t[y - 1][x] in 'cC' and S.t[y][x - 1] == 'w' and S.t[y][x + 1] == 'w' and S.e[y][x] is None:
                    if not S.crowded(x, y, 3): S.E(x, y + 1, '+')

        # ---------------------------------------------------------- treasure & enemies (strategic: around ruins and paths)
        full = (2, 2, W - 3, H - 3)
        for rid, n in [('b', 9), ('e', 7), ('h', 6), ('f', 7), ('d', 7), ('c', 5), ('a', 6), ('j', 5), ('g', 5), ('i', 3)]:
            S.scatter(full, 'C', SURF(n), '._fndav', 5, 100 + ord(rid), region=rid)
            S.scatter(full, 'h', SURF(max(1, n // 2)), '._fndav', 4, 200 + ord(rid), region=rid)
            S.scatter(full, 'a', SURF(max(1, n // 2)), '._fndav', 4, 300 + ord(rid), region=rid)
        for rid, chars, n in [('b', 'oooob', 60), ('e', 'oood', 40), ('h', 'ddddb', 44), ('f', 'oooo', 48), ('d', 'bbbbo', 50),
                              ('c', 'bbo', 22), ('a', 'ob', 22), ('j', 'ob', 24), ('g', 'dd', 30)]:
            S.scatter(full, chars, SURF(n), '._fndav', 3, 400 + ord(rid), avoid='p=HD', region=rid)
        # safe zones: towns, Aurelith, bonfires, the start
        safe = [(vcx, vcy, 46), (ccx, ccy, 50), (pcx, pcy, 44), (ax_, ay_, 14)]
        for y in range(H):
            for x in range(W):
                if S.e[y][x] == 'F': safe.append((x, y, 5))
        for (zx, zy, rad) in safe:
            for y in range(zy - rad, zy + rad):
                for x in range(zx - rad, zx + rad):
                    if S.inb(x, y) and S.e[y][x] in ('o', 'b', 'd'): S.e[y][x] = None

        # ---------------------------------------------------------- decoration by biome (densities scaled to the bigger map)
        S.scatter(full, 'TTUUtiggyyzZn', SURF(1700), '.f', 2, 1, region='b')
        S.scatter(full, 'TUtggGyyzA', SURF(520), '.f', 2, 2, region='a')
        S.scatter(full, 'TAUtgG', SURF(160), '.f', 2, 2, region='i')
        S.scatter(full, 'TtGgyyze', SURF(300), '.f', 2, 3, region='c')
        S.scatter(full, 'iiIIWr', SURF(380), 'n.', 2, 4, region='e')
        S.scatter(full, '1122', SURF(150), 'nC', 3, 5, avoid='', region='e')
        S.scatter(full, 'VVuuqMk', SURF(520), 'vf.', 2, 6, region='h')
        S.scatter(full, '44Rrk', SURF(230), 'd', 3, 7, region='f')
        S.scatter(full, '3Rrk', SURF(120), 'a', 3, 8, region='g')
        S.scatter(full, 'kkMMegZnVu', SURF(560), 'f.v', 2, 9, region='d')
        S.scatter(full, 'YYgyzNr', SURF(160), '_.', 3, 10, region='j')
        S.scatter(full, 'Y', SURF(120), '_', 4, 12, avoid='p=HD')
        for y in range(H):
            for x in range(W):
                if S.e[y][x] == 'Y' and not S.near(x, y, 4, 'O') and not S.near(x, y, 2, 'w'): S.e[y][x] = None
        S.scatter(full, '3', SURF(90), 'c', 3, 13, avoid='_p')
        S.scatter(full, '1', SURF(60), 'C', 4, 14, avoid='_p')
        S.scatter(full, ';', SURF(260), 'F', 1, 15, avoid='')
        S.scatter(full, 'le', SURF(260), 'w', 2, 16, avoid='')
        for y in range(H):
            for x in range(W):
                if S.e[y][x] == 'e' and not S.near(x, y, 1, '.f_'): S.e[y][x] = 'l'
        self.clear_near_roads('12m^3', 4)
        self.densify()
        self.clear_near_roads('12m^3', 4)
        # keep every special place reachable: nothing tall on the tiles around entrances, gates, levers, keys, bonfires
        for y in range(H):
            for x in range(W):
                if S.e[y][x] in ('E', 'L', 'v', 'p', 'F', 'O', 'D'):
                    for yy in range(y - 1, y + 3):
                        for xx in range(x - 2, x + 3):
                            if S.inb(xx, yy) and (xx, yy) != (x, y) and S.e[yy][xx] in W2.BLOCK_E and S.e[yy][xx] not in 'EHLvFODp#9x0':
                                S.e[yy][xx] = None
        S.border()
        # the meta: world gate positions
        S.meta['size'] = [W, H]

    # ------------------------------------------------------------------ validation (locked gates count as open once
    # their key is reachable; the volcano seal counts as open)
    def walkable(self, x, y, seal_open):
        e = self.e[y][x]
        if e in ('L', 'v'): return seal_open
        if e in ('E', 'p', 'H'): return e != 'E'
        return super().walkable(x, y, seal_open)

    def dump3(self, root):
        lv = os.path.join(root, 'Assets', 'Game', 'Levels')
        self.dump(os.path.join(lv, 'World2.txt'))
        with open(os.path.join(lv, 'World3.json'), 'w', encoding='utf-8') as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    w = World3(); w.build()
    pruned = w.prune()
    bad, rc, ro, behind = w.validate()
    w.dump3(root)
    cnt = {}
    for row in w.e:
        for c in row:
            if c: cnt[c] = cnt.get(c, 0) + 1
    land = sum(1 for r in w.t for t in r if t != 'O')
    print(f'{W}x{H}  land {land}  pruned {pruned}  reach {rc}  open {ro}  behind locks {len(behind)}')
    print({k: cnt[k] for k in 'PobdFCSEHODLvpX$hJ69#x+' if k in cnt})
    print('towns', w.meta['towns'], 'entrances', [(e['map'], e['x'], e['row']) for e in w.meta['entrances']])
