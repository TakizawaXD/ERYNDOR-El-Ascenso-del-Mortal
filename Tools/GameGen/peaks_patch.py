s = open('GameGen/world2.py', encoding='utf8').read()
old = "            if rid == 'e' and t in 'nC':\n                if not S.near(x, y, 2, roads) and not S.crowded(x, y, 2) and r.random() < 0.55:"
new = "            if rid == 'e' and t in 'nC':\n                if not S.near(x, y, 4, roads) and not S.near(x, y + 1, 4, roads) and not S.crowded(x, y, 2) and r.random() < 0.55:"
assert old in s; s = s.replace(old, new)
old = "        S.scatter(full, '1122', 70, 'nC', 3, 5, avoid='_p', region='e')"
new = "        S.scatter(full, '1122', 70, 'nC', 3, 5, avoid='', region='e')\n        self.clear_near_roads('12m^3', 4)"
assert old in s; s = s.replace(old, new)
old = "        wx, wy = U(0.33, 0.13)\n        S.E(wx, wy, '+')\n"
new = ("        # waterfalls only where a river leaves a cliff (river cell with a cliff right above it)\n"
       "        for y in range(1, H):\n"
       "            for x in range(W):\n"
       "                if S.t[y][x] == 'w' and S.t[y - 1][x] in 'cC' and S.t[y][x - 1] == 'w' and S.t[y][x + 1] == 'w' and S.e[y][x] is None:\n"
       "                    if not S.crowded(x, y, 3): S.E(x, y + 1, '+')\n")
assert old in s; s = s.replace(old, new)
fn = '''    def clear_near_roads(self, chars, rad):
        for y in range(H):
            for x in range(W):
                if self.e[y][x] and self.e[y][x] in chars and (self.near(x, y, rad, '_p=HD') or self.near(x, y + 1, rad, '_p=HD')):
                    self.e[y][x] = None

'''
s = s.replace("    def densify(self):", fn + "    def densify(self):", 1)
s = s.replace("        self.densify()\n        S.border()", "        self.densify()\n        self.clear_near_roads('12m^3', 4)\n        S.border()")
open('GameGen/world2.py', 'w', encoding='utf8').write(s)

m = open('ArtGen2/structures.py', encoding='utf8').read()
a = m.index('def mountain('); b = m.index('def mesa(')
m = m[:a] + '''def mountain(seed=1, w=64, h=56, snow=True):
    """main ridge (lit left / shaded right), secondary ridges with creases, jagged snow cap with streaks"""
    c = C(w, h)
    c.ellipse(w / 2, h - 4, w / 2 - 2, 4, SHADOW)
    r = np.random.default_rng(seed)
    apex = w / 2 + r.integers(-w // 10, w // 10 + 1)
    top, bot = 3, h - 4
    ridge = lambda y: apex + 3 * math.sin((y - top) * 0.18 + seed) * (y - top) / (bot - top)
    subs = [(top + (bot - top) * r.uniform(.25, .6), r.choice([-1, 1]) * r.uniform(.5, .9)) for _ in range(4)]
    snowline = top + (bot - top) * 0.45
    for y in range(top, bot):
        p = (y - top) / (bot - top)
        hl, hr = (apex - 1) * p, (w - 1 - apex) * p
        jag = int(round(1.2 * math.sin(y * .8 + seed)))
        for x in range(int(apex - hl) + jag, int(apex + hr) + 1 - jag):
            rx = ridge(y)
            lit = x < rx
            shade = 0.0
            for (sy, slope) in subs:
                if y > sy:
                    sx = rx + slope * (y - sy) * 1.4
                    d = x - sx
                    if 0 <= d < 2: shade -= 1.0          # crease on the far side of a sub-ridge
                    elif -2 < d < 0: shade += 0.6        # lit edge of the sub-ridge
            v = h2(x // 3, y // 3, seed) * 0.4
            sl = snowline + 4 * math.sin(x * .45 + seed) + 3 * h2(x, 0, seed)
            if snow and y < sl:
                base = 2 if lit else 1
                lvl = base + shade + v
                col = 'sn' if lvl > 1.7 else 'sn_md' if lvl > 0.9 else 'sn_dk'
            else:
                base = 2.2 if lit else 0.9
                lvl = base + shade + v - p * 0.6
                col = 'st_hi' if lvl > 2.3 else 'st_lt' if lvl > 1.6 else 'st' if lvl > 0.9 else 'st_md' if lvl > 0.3 else 'st_dk'
                if snow and y < sl + 6 and (x * 3 + y) % 7 == 0 and lit: col = 'sn_md'     # snow streaks in the gullies
            c.px(x, y, col)
        c.px(int(ridge(y)), y, 'sn_dk' if (snow and y < snowline) else 'st_dk') if y > top + 3 else None
    # boulders at the foot
    for k in range(3):
        bx = r.integers(4, w - 6); by = bot - r.integers(0, 3)
        c.ellipse(bx, by, 2.5, 1.6, 'st'); c.px(bx - 1, by - 1, 'st_lt')
    return finish(c, 'st_ol')


''' + m[b:]
open('ArtGen2/structures.py', 'w', encoding='utf8').write(m)
print('ok')
