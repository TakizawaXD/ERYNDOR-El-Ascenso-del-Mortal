"""Quick schematic of World2.txt (3 px per tile): terrain colours, region borders, POIs, entrances, bonfires, gates.
usage: python preview_world3.py <out.png>"""
import json, os, sys
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LV = os.path.join(ROOT, 'Assets', 'Game', 'Levels')
L = open(os.path.join(LV, 'World2.txt'), encoding='utf-8').read().splitlines()
t0, e0, r0 = L.index('TERRAIN'), L.index('ENTITIES'), L.index('REGIONS')
T = L[t0 + 1:e0]; E = L[e0 + 1:e0 + 1 + len(T)]; R = L[r0 + 1:r0 + 1 + len(T)]
H, W = len(T), len(T[0])
C = {'.': (88, 160, 70), '_': (222, 190, 130), 'f': (40, 100, 50), 'w': (40, 120, 220), 'O': (20, 60, 140), 'c': (110, 90, 70),
     'C': (220, 226, 236), 'k': (60, 50, 60), 'n': (236, 240, 246), 'd': (226, 160, 100), 'a': (80, 72, 90), 'L': (250, 110, 30),
     's': (60, 90, 70), 'v': (100, 60, 110), 'F': (170, 120, 60), 'p': (160, 160, 170), '=': (150, 100, 60), 'H': (150, 100, 60), 'D': (150, 100, 60)}
S = 3
img = Image.new('RGB', (W * S, H * S))
d = ImageDraw.Draw(img)
for y in range(H):
    for x in range(W):
        c = C.get(T[y][x], (255, 0, 255))
        e = E[y][x]
        if e in 'TUtAVuiIkY': c = tuple(max(0, v - 45) for v in c)
        if e in '12m^345': c = (120, 110, 120)
        d.rectangle([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=c)
        if x and R[y][x] != R[y][x - 1] or y and R[y][x] != R[y - 1][x]:
            d.point((x * S, y * S), fill=(0, 0, 0))
mk = {'F': ((255, 140, 0), 3), 'E': ((255, 0, 255), 5), 'P': ((255, 255, 255), 5), 'L': ((255, 0, 0), 4), 'v': ((0, 255, 255), 4),
      'p': ((255, 255, 0), 4), 'D': ((0, 255, 100), 6), 'O': ((200, 255, 255), 3), 'H': ((40, 40, 40), 1), 'X': ((255, 0, 0), 3),
      'C': ((255, 215, 0), 2), '+': ((255, 255, 255), 2)}
for y in range(H):
    for x in range(W):
        e = E[y][x]
        if e in mk:
            col, r = mk[e]; d.ellipse([x * S - r, y * S - r, x * S + r, y * S + r], fill=col, outline=(0, 0, 0))
meta = json.load(open(os.path.join(LV, 'World3.json'), encoding='utf-8'))
for mid, (x0, y0, x1, y1) in meta['towns'].items():
    d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], outline=(255, 255, 255), width=2)
img.save(sys.argv[1]); print(img.size)
