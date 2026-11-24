"""Open-world map generator: one 200x150 map, 7 regions, roads, bosses, camps, chests.
Writes Assets/Game/Levels/World.txt (+ REGIONS grid) and Assets/Art/Game/world_minimap.png.

Extra entity letters (see levels.py for the rest):
  K orc chieftain (boss)   Q blood mother (boss)   B demon lord (final boss)
  Y shop stall   F campfire = save point   X demonic seal (barrier to the altar)
"""
import math, os, random, sys
from collections import deque
from PIL import Image
from levels import Level, BLOCK_T, BLOCK_E

W, H = 200, 150
REGIONS = {  # id: (name, seed point)
    'a': ('CAMPAMENTO DEL ALBA', (100, 128)),
    'b': ('BOSQUE SUSURRANTE', (38, 112)),
    'c': ('LAGO ESPEJO', (100, 86)),
    'd': ('PANTANO CARMESÍ', (168, 126)),
    'e': ('COLINAS ALTAS', (40, 34)),
    'f': ('RUINAS OLVIDADAS', (164, 72)),
    'g': ('ALTAR DEMONÍACO', (160, 20)),
}
BLOCK_E.update('XY')   # bosses are actors, not obstacles


def noise2(x, y, seed):
    s = 0
    for k, (f, a) in enumerate(((0.045, 1.0), (0.11, 0.5), (0.23, 0.25))):
        ph = seed * 1.7 + k
        s += a * math.sin(x * f + ph) * math.cos(y * f * 1.13 - ph * 0.7)
    return s


class World(Level):
    def __init__(self):
        super().__init__(W, H)
        self.region = [[None] * W for _ in range(H)]
        self.rng = random.Random(2026)

    # ------------------------------------------------------------ regions
    def assign_regions(self):
        seeds = {k: v[1] for k, v in REGIONS.items()}
        for y in range(H):
            for x in range(W):
                jx = x + noise2(x, y, 1) * 9
                jy = y + noise2(x, y, 2) * 9
                best = min(seeds, key=lambda k: (jx - seeds[k][0]) ** 2 + ((jy - seeds[k][1]) * 1.15) ** 2)
                self.region[y][x] = best

    def cells(self, rid):
        return [(x, y) for y in range(1, H - 1) for x in range(1, W - 1) if self.region[y][x] == rid]

    def in_region(self, x, y, rid):
        return 0 <= x < W and 0 <= y < H and self.region[y][x] == rid

    # ------------------------------------------------------------ roads
    def road(self, pts, width=2):
        """stone road; crossing water becomes a wooden bridge"""
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(abs(x1 - x0), abs(y1 - y0))
            horizontal = abs(x1 - x0) >= abs(y1 - y0)
            for i in range(n + 1):
                x = round(x0 + (x1 - x0) * i / max(n, 1)); y = round(y0 + (y1 - y0) * i / max(n, 1))
                for dx in range(width):
                    for dy in range(width):
                        X, Y = x + dx, y + dy
                        if not (1 <= X < W - 1 and 1 <= Y < H - 1):
                            continue
                        t = self.t[Y][X]
                        if t in 'w=H':
                            self.t[Y][X] = '=' if horizontal else 'H'
                        elif t == 'c':
                            self.t[Y][X] = 'p'      # roads cut passes through cliffs
                        else:
                            self.t[Y][X] = 'p'
                        if self.e[Y][X] in BLOCK_E:
                            self.e[Y][X] = None

    def clear(self, x0, y0, x1, y1, ground='.'):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 1 <= x < W - 1 and 1 <= y < H - 1:
                    if self.t[y][x] in 'wc"': self.t[y][x] = ground
                    self.e[y][x] = None

    def scatter_region(self, rid, chars, n, seed, spacing=2, allow='."', avoid_road=True):
        r = random.Random(seed)
        cells = self.cells(rid)
        placed = 0
        for _ in range(n * 30):
            if placed >= n or not cells:
                break
            x, y = r.choice(cells)
            if not self.free(x, y, allow):
                continue
            if any(self.e[yy][xx] for yy in range(max(0, y - spacing), min(H, y + spacing + 1))
                   for xx in range(max(0, x - spacing), min(W, x + spacing + 1))):
                continue
            if avoid_road and any(self.t[yy][xx] in 'p=H' for yy in range(max(0, y - 1), min(H, y + 2)) for xx in range(max(0, x - 1), min(W, x + 2))):
                continue
            self.E(x, y, r.choice(chars))
            placed += 1
        return placed

    # ------------------------------------------------------------ build
    def build(self):
        r = self.rng
        self.assign_regions()
        # base ground per region
        for y in range(H):
            for x in range(W):
                rid = self.region[y][x]
                n = noise2(x, y, 7)
                if rid in 'dg':
                    self.t[y][x] = ' ' if n > -0.35 else '.'
                elif rid == 'f':
                    self.t[y][x] = ' ' if n > 0.25 else '.'
                else:
                    self.t[y][x] = '.' if n > -0.75 else ' '
                if rid in 'be' and noise2(x, y, 9) > 0.55:
                    self.t[y][x] = '"'
                if rid == 'c' and noise2(x, y, 11) > 0.8:
                    self.t[y][x] = '"'
        self.border()
        for x in range(W):
            self.T(x, 1, 'c')
        # Lago Espejo: great lake with two islands
        self.ellipse(98, 80, 22, 13, 'w', 0.12, 3)
        self.ellipse(92, 78, 5, 3, '.', 0.2, 4); self.ellipse(110, 84, 4, 2.5, '.', 0.2, 5)
        self.ellipse(70, 92, 6, 4, 'w', 0.2, 6)
        # swamp ponds
        for i in range(14):
            cx, cy = r.randint(140, 192), r.randint(108, 144)
            if self.region[cy][cx] == 'd':
                self.ellipse(cx, cy, r.uniform(2, 4.5), r.uniform(1.5, 3), 'w', 0.25, i + 20)
        # highlands plateaus
        for i in range(10):
            cx, cy = r.randint(6, 76), r.randint(5, 56)
            if self.region[cy][cx] == 'e':
                self.ellipse(cx, cy, r.uniform(4, 9), r.uniform(2.5, 5), 'c', 0.2, i + 40)
        # altar: ring of cliffs around the sanctum, stone arena inside
        self.ellipse(160, 20, 30, 16, 'c', 0.08, 60)
        self.ellipse(160, 21, 25, 12, ' ', 0.06, 61)
        self.rect(146, 12, 174, 28, 'p')
        # ruins: stone plazas
        for (cx, cy) in [(158, 62), (176, 80), (150, 88), (182, 52)]:
            self.rect(cx - 4, cy - 3, cx + 4, cy + 3, 'p')
        # rivers feeding the lake
        for (x0, y0, x1, y1) in [(98, 66, 92, 40), (120, 82, 140, 88)]:
            n = max(abs(x1 - x0), abs(y1 - y0))
            for i in range(n + 1):
                x = round(x0 + (x1 - x0) * i / n + math.sin(i * 0.3) * 2); y = round(y0 + (y1 - y0) * i / n)
                for dx in range(3):
                    self.T(x + dx, y, 'w')
        # camp clearing
        self.clear(88, 120, 112, 138)
        self.rect(94, 126, 106, 132, 'p')

        # roads (camp hub -> every region)
        hub = (99, 128)
        self.road([hub, (99, 112), (99, 100), (99, 70), (99, 52), (130, 44), (160, 38), (160, 30)])   # north across the lake to the altar gate
        self.road([hub, (80, 128), (60, 118), (38, 112)])          # forest
        self.road([(60, 118), (52, 90), (44, 62), (40, 40)])        # forest -> highlands
        self.road([hub, (122, 128), (146, 124), (168, 126)])        # swamp
        self.road([(99, 70), (130, 66), (158, 62), (176, 80)])       # lake -> ruins
        self.road([(158, 62), (150, 88), (146, 124)])                # ruins -> swamp
        self.road([(40, 40), (70, 30), (99, 52)])                    # highlands -> north road

        # ---------------------------------------------- landmarks & bosses
        # camp
        self.E(99, 131, 'P')
        self.E(102, 129, 'F')                        # save point
        self.E(95, 127, 'Y')                          # shop stall
        self.E(97, 125, 'S', 'CAMPAMENTO DEL ALBA. DOS GUARDIANES PROTEGEN EL ALTAR DEMONÍACO DEL NORESTE: EL JEFE ORCO (OESTE) Y LA MADRE DE SANGRE (SURESTE). DERRÓTALOS Y EL SELLO CAERÁ.')
        self.E(104, 125, 'S', 'HOGUERAS: PULSA E PARA DESCANSAR, CURARTE Y GUARDAR LA PARTIDA. M ABRE EL MAPA, TAB EL DIARIO DE MISIONES.')
        for (x, y) in [(90, 122), (110, 122), (90, 136), (110, 136)]:
            self.E(x, y, 'l')
        for (x, y, c) in [(93, 130, 'x'), (93, 131, 'k'), (106, 131, 'x'), (107, 131, 'u'), (106, 127, 'k')]:
            self.E(x, y, c)
        for x in range(89, 112, 2):
            if self.t[138][x] in '.': self.E(x, 138, 'f')
        # orc war camp (forest) + chieftain
        self.clear(24, 92, 42, 104)
        for (x, y) in [(26, 94), (40, 94), (26, 103), (40, 103)]:
            self.E(x, y, 'L')
        for (x, y, c) in [(28, 96, 'x'), (29, 96, 'k'), (38, 101, 'x'), (37, 101, 'x'), (30, 102, 'k')]:
            self.E(x, y, c)
        self.E(33, 98, 'K')
        self.E(33, 95, 'F')
        self.E(35, 105, 'C')
        self.road([(38, 112), (33, 104)])
        # blood mother's nest (swamp)
        self.clear(178, 132, 192, 142, ' ')
        self.E(185, 137, 'Q')
        for (x, y) in [(180, 134), (190, 134), (180, 141), (190, 141)]:
            self.E(x, y, 'O')
        self.road([(168, 126), (178, 132), (181, 134)])
        # altar: seal across the road gate + demon lord
        for x in range(160, 162):
            self.e[33][x] = None
            self.E(x, 33, 'X')
        self.E(160, 18, 'B')
        for (x, y) in [(148, 13), (172, 13), (148, 27), (172, 27)]:
            self.E(x, y, 'L')
        for (x, y) in [(152, 16), (168, 16), (152, 25), (168, 25)]:
            self.E(x, y, 'O')
        self.E(159, 36, 'S', 'EL SELLO DEMONÍACO. SOLO CAERÁ CUANDO EL JEFE ORCO Y LA MADRE DE SANGRE HAYAN SIDO DERROTADOS.')
        # campfires (save points) per region
        for (x, y) in [(52, 90), (44, 60), (40, 42), (130, 66), (158, 58), (146, 120), (150, 40), (99, 98)]:
            if self.t[y][x] in 'w=Hc': continue
            self.E(x + 3, y, 'F') if self.free(x + 3, y, '. "') else None
        self.E(162, 37, 'F')

        # ---------------------------------------------- treasure
        for rid, n in [('b', 5), ('c', 3), ('d', 4), ('e', 5), ('f', 5), ('g', 2)]:
            self.scatter_region(rid, 'C', n, 100 + ord(rid), spacing=3, allow='. "')
        for rid, n in [('b', 3), ('c', 2), ('d', 3), ('e', 3), ('f', 3)]:
            self.scatter_region(rid, 'h', n, 200 + ord(rid), spacing=3, allow='. "')
            self.scatter_region(rid, 'a', n, 300 + ord(rid), spacing=3, allow='. "')

        # ---------------------------------------------- enemies by region
        for rid, chars, n in [('b', 'oooooom', 34), ('e', 'oooodd', 22), ('c', 'mmmmo', 16), ('d', 'mmmmmo', 26),
                              ('f', 'ddddmmo', 26), ('g', 'dddd', 8), ('a', 'o', 2)]:
            self.scatter_region(rid, chars, n, 400 + ord(rid), spacing=3, allow='. "', avoid_road=False)
        # ---------------------------------------------- nature & ruins dressing
        self.scatter_region('b', 'TTTttiigbZ', 260, 1, spacing=2)
        self.scatter_region('b', 'yvMn', 120, 2, spacing=1)
        self.scatter_region('e', 'iiitTr', 120, 3, spacing=2)
        self.scatter_region('e', 'yvr', 60, 4, spacing=1)
        self.scatter_region('a', 'TTttgyyvZbn', 150, 5, spacing=2)
        self.scatter_region('c', 'TTttgyyvrMb', 220, 6, spacing=2)
        self.scatter_region('d', 'DDDMMZgn', 150, 7, spacing=2, allow='. "')
        self.scatter_region('f', 'RRIIGGDr', 110, 8, spacing=2, allow='. "')
        self.scatter_region('f', 'O', 6, 9, spacing=6, allow='. "')
        self.scatter_region('g', 'DGr', 30, 10, spacing=2, allow='. "')
        self.scatter_top('iiTt', 60, 11, spacing=2)

        # keep the camp itself safe
        for y in range(118, 140):
            for x in range(86, 114):
                if self.e[y][x] in ('o', 'm', 'd'): self.e[y][x] = None

    # ---------------------------------------------- validation
    def check_world(self):
        problems, reach = self.check()
        # the altar beyond the seal is unreachable on purpose: re-check with the seal open
        seal = [(x, y) for y in range(H) for x in range(W) if self.e[y][x] == 'X']
        for (x, y) in seal: self.e[y][x] = None
        problems2, reach2 = self.check()
        for (x, y) in seal: self.e[y][x] = 'X'
        behind_seal = [p for p in problems if p not in problems2]
        return problems2, reach, reach2, len(behind_seal)

    def prune_unreachable(self):
        problems, _ = self.check_open()
        for (c, x, y) in problems:
            self.e[y][x] = None
        return len(problems)

    def check_open(self):
        seal = [(x, y) for y in range(H) for x in range(W) if self.e[y][x] == 'X']
        for (x, y) in seal: self.e[y][x] = None
        res = self.check()
        for (x, y) in seal: self.e[y][x] = 'X'
        return res

    def dump_world(self, path):
        self.dump(path, 'MUNDO', '')
        with open(path, 'a', encoding='utf-8') as f:
            f.write('REGIONS\n' + '\n'.join(''.join(r) for r in self.region) + '\n')
            for k, (name, _) in REGIONS.items():
                f.write(f'REGIONNAME {k} {name}\n')

    def minimap(self, path):
        col = {' ': (186, 133, 79), '.': (89, 193, 53), '"': (20, 160, 46), 'p': (139, 147, 175), 'w': (36, 159, 222),
               '=': (140, 80, 54), 'H': (140, 80, 54), 'c': (113, 65, 59)}
        im = Image.new('RGBA', (W, H))
        for y in range(H):
            for x in range(W):
                c = col.get(self.t[y][x], (89, 193, 53))
                e = self.e[y][x]
                if e and e in "TtiD": c = (26, 122, 62) if e != "D" else (90, 78, 68)
                if e and e in "RIGO": c = (90, 87, 85)
                im.putpixel((x, H - 1 - y if False else y), c + (255,))
        im.save(path)


if __name__ == '__main__':
    root = sys.argv[1]
    w = World()
    w.build()
    removed = w.prune_unreachable()
    problems, reach, reach_open, sealed = w.check_world()
    w.dump_world(os.path.join(root, 'Assets', 'Game', 'Levels', 'World.txt'))
    w.minimap(os.path.join(root, 'Assets', 'Art', 'Game', 'world_minimap.png'))
    ents = {}
    for row in w.e:
        for c in row:
            if c: ents[c] = ents.get(c, 0) + 1
    print('pruned', removed, 'problems', problems, 'reach', reach, 'reach_with_seal_open', reach_open, 'behind_seal', sealed)
    print({k: ents[k] for k in sorted(ents) if k in 'PomdKQBCFSYXha'})
