"""Visual audit of the merged map (World2.txt): finds what looks unnatural in game.

  python Tools/GameGen/audit_world.py            report only
  python Tools/GameGen/audit_world.py --fix      also removes the offending small things (trees, rocks, bushes, props)

Checks
  overlap    two sprites whose drawn footprints cover the same cells (a tree inside a house, two trees in one spot...)
  on_road    trees, rocks and bushes standing on a road or a bridge
  in_water   any object standing in water, ocean, lava or swamp (except lily pads, reeds, boats, waterfalls)
  on_cliff   anything standing on a cliff / rock wall cell
  blocked    houses, gates, bonfires, chests, signs and entrances with no free walkable cell in front (south)
"""
import os, sys
from collections import Counter

ROOT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FIX = '--fix' in sys.argv
LV = os.path.join(ROOT, 'Assets', 'Game', 'Levels')

# sprite footprint in cells around the foot cell: (left, right, up) - like maps.py, extended
FOOT = {'6': (2, 2, 4), '7': (2, 2, 4), '8': (2, 2, 4), 'J': (2, 2, 6), '9': (1, 1, 6), '0': (1, 1, 5), 'j': (1, 1, 6),
        '#': (0, 1, 2), '@': (0, 1, 1), '$': (1, 1, 2), '5': (5, 5, 7), 'x': (1, 1, 7), 'N': (1, 1, 1), '!': (0, 0, 1),
        'T': (1, 1, 3), 'U': (1, 1, 3), 'A': (1, 1, 3), 'V': (1, 1, 3), 'i': (0, 0, 2), 'I': (0, 0, 2), 'Y': (0, 0, 2),
        't': (0, 0, 1), 'u': (0, 0, 1), 'k': (0, 0, 1), '3': (1, 1, 1), 'R': (0, 1, 0), 'W': (0, 1, 0),
        '1': (1, 1, 2), '2': (1, 1, 2), 'm': (2, 2, 3), '^': (2, 2, 3), '4': (1, 1, 1), 'D': (2, 2, 5), 'E': (1, 1, 2),
        'O': (0, 0, 1), 'F': (1, 1, 1), 'C': (0, 0, 0), 'S': (0, 0, 0), '|': (0, 0, 1), 'H': (0, 0, 0),
        'g': (0, 0, 0), 'G': (0, 0, 0), 'q': (0, 0, 0), 'r': (0, 0, 0), 'Z': (0, 0, 0), 'n': (1, 1, 0), '(': (0, 0, 0), ')': (0, 0, 0),
        '*': (0, 0, 0), '/': (0, 0, 0)}
BIG = set('6789J0j#5xDE$@')            # buildings / landmarks: they win, small things around them go
SMALL = set('TUAVtuikIYgGqrRWZn34N!12m^*()/yzMH')   # graves and flowers too   # removable dressing
SOLID_T = set('wOLs')
CLIFF_T = set('cCk')
WATER_OK = set('le~+')


def load():
    path = os.path.join(LV, 'World2.txt')
    L = open(path, encoding='utf-8').read().splitlines()
    W, H = map(int, [l for l in L if l.startswith('SIZE ')][0].split()[1:3])
    t0, e0, r0 = L.index('TERRAIN'), L.index('ENTITIES'), L.index('REGIONS')
    return path, L, W, H, t0, e0, [list(r) for r in L[t0 + 1:t0 + 1 + H]], [list(r) for r in L[e0 + 1:e0 + 1 + H]]


def main():
    path, L, W, H, t0, e0, T, E = load()
    SW = int([l for l in L if l.startswith('SURFACE ')][0].split()[1]) if any(l.startswith('SURFACE ') for l in L) else W
    issues = Counter()
    remove = set()
    owner = {}
    # biggest first: buildings claim their cells, then everything else
    cells = [(x, y, E[y][x]) for y in range(H) for x in range(SW) if E[y][x] != ' ']
    cells.sort(key=lambda c: 0 if c[2] in BIG else 1)
    town_houses = set((int(l.split()[1]), int(l.split()[2])) for l in L if l.startswith('HOUSE '))
    for (x, y, c) in cells:
        l, r, u = FOOT.get(c, (0, 0, 0))
        cover = [(xx, yy) for yy in range(y - u, y + 1) for xx in range(x - l, x + r + 1)]
        hit = [owner[p] for p in cover if p in owner and owner[p] != (x, y) and E[owner[p][1]][owner[p][0]] in BIG]
        if hit:                                   # trees among trees are fine (depth-sorted); against a building they are not
            issues['overlap'] += 1
            if c in SMALL: remove.add((x, y)); continue
            # two village houses / mills built into each other (hamlets): the later one goes (never a town house with an interior)
            if c in '678J' and (x, y) not in town_houses and any(E[o[1]][o[0]] in '678J' for o in hit):
                remove.add((x, y)); continue
        if c in BIG:
            for p in cover: owner.setdefault(p, (x, y))
        t = T[y][x]
        if c in SMALL and t in '_p=HD': issues['on_road'] += 1; remove.add((x, y))
        if t in SOLID_T and c not in WATER_OK and c != 'X': issues['in_water'] += 1; remove.add((x, y)) if c in SMALL else None
        if t in CLIFF_T and c in SMALL and c not in '12m^3': issues['on_cliff'] += 1; remove.add((x, y))
    moved_chests = []
    # things you must reach need a free cell in front
    for (x, y, c) in cells:
        if c not in '6789FCSE@$J': continue
        front = [(x + dx, y + dy) for dy in (1, 2) for dx in (-1, 0, 1)]
        if not any(0 <= a < W and 0 <= b < H and T[b][a] not in SOLID_T | CLIFF_T and (E[b][a] == ' ' or (a, b) in remove) for (a, b) in front):
            issues['blocked'] += 1
            if c == 'C' and FIX:                  # a chest against a cliff / swamp: move it to the nearest open spot
                def open_(a, b): return 0 <= a < W and 0 <= b < H and T[b][a] not in SOLID_T | CLIFF_T and E[b][a] == ' '
                spot = next(((x + i, y + j) for r in range(1, 8) for j in range(-r, r + 1) for i in range(-r, r + 1)
                             if open_(x + i, y + j) and open_(x + i, y + j + 1) and open_(x + i - 1, y + j) and open_(x + i + 1, y + j)), None)
                if spot: E[y][x] = ' '; E[spot[1]][spot[0]] = 'C'; moved_chests.append(spot)
            for (a, b) in front:
                if 0 <= a < W and 0 <= b < H and E[b][a] in SMALL: remove.add((a, b))
    print('issues:', dict(issues), '· small things to remove:', len(remove))
    if moved_chests: print('chests moved to open ground:', len(moved_chests))
    if FIX and (remove or moved_chests):
        for (x, y) in remove: E[y][x] = ' '
        L[e0 + 1:e0 + 1 + H] = [''.join(r) for r in E]
        open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
        print('fixed: removed', len(remove), 'trees / rocks / bushes / props')


if __name__ == '__main__':
    main()
