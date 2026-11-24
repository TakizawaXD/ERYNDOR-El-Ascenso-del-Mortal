s = open('painter.py', encoding='utf8').read()
rep = [
 ("        self.put(g & (big > 0.62) & (small > 0.42), mid if mid != light else light)\n        self.put(g & (big < 0.33) & (small > 0.5), dark)",
  "        self.put(g & (big > 0.74) & (small > 0.55), mid if mid != light else light)\n        self.put(g & (big < 0.2) & (small > 0.55), dark)"),
 ("        self.put(mask & (n1 > 0.6) & (n2 > 0.45), alt)\n        self.put(mask & (n1 < 0.3) & (n2 > 0.55), alt2)",
  "        self.put(mask & (n1 > 0.72) & (n2 > 0.5), alt)\n        self.put(mask & (n1 < 0.22) & (n2 > 0.55), alt2)"),
 ("        n = self.noise(18, 50)\n        cracks = np.abs(n - 0.5) < 0.012", "        n = self.noise(40, 50)\n        cracks = np.abs(n - 0.5) < 0.006"),
 ("    def water(self, mask, deep_d=12, seed=70):", "    def water(self, mask, deep_d=30, seed=70):"),
]
for a, b in rep:
    assert a in s, a[:60]
    s = s.replace(a, b)
BR = '''    def bridges(self):
        """bridges and docks painted as single continuous decks (rails on the outer edges only)"""
        h, w = self.h, self.w
        seen = set()
        for y in range(h):
            for x in range(w):
                c = self.ter[y][x]
                if c not in '=HD' or (x, y) in seen: continue
                comp = []; st = [(x, y)]; seen.add((x, y))
                while st:
                    a, b = st.pop(); comp.append((a, b))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = (a + dx, b + dy)
                        if 0 <= n[0] < w and 0 <= n[1] < h and n not in seen and self.ter[n[1]][n[0]] == c:
                            seen.add(n); st.append(n)
                xs = [p[0] for p in comp]; ys = [p[1] for p in comp]
                X0, X1, Y0, Y1 = min(xs) * T, (max(xs) + 1) * T, min(ys) * T, (max(ys) + 1) * T
                horiz = c == '=' or (c == 'D' and (X1 - X0) >= (Y1 - Y0))
                img = self.img
                if horiz:
                    y0, y1 = Y0 + 3, Y1 - 3
                    for xx in range(X0, X1):
                        k = (xx - X0) % 5
                        img[y0:y1, xx] = col('w_lt' if k == 0 else 'w' if k < 3 else 'w_mid' if k == 3 else 'w_dk')
                    img[y0:y0 + 2, X0:X1] = col('w_dk'); img[y0, X0:X1] = col('w_lt')
                    img[y1 - 2:y1, X0:X1] = col('w_dk'); img[y1 - 1, X0:X1] = col('w_ol')
                    img[y1:y1 + 2, X0:X1] = (img[y1:y1 + 2, X0:X1].astype(np.int16) * 0.7).astype(np.uint8)
                    for px in list(range(X0, X1 - 3, 24)) + [X1 - 4]:
                        img[y0 - 2:y0 + 3, px:px + 4] = col('w'); img[y0 - 2, px:px + 4] = col('s')
                        img[y1 - 3:y1 + 1, px:px + 4] = col('w_dk')
                else:
                    x0, x1 = X0 + 3, X1 - 3
                    for yy in range(Y0, Y1):
                        k = (yy - Y0) % 5
                        img[yy, x0:x1] = col('w_lt' if k == 0 else 'w' if k < 3 else 'w_mid' if k == 3 else 'w_dk')
                    img[Y0:Y1, x0:x0 + 2] = col('w_dk'); img[Y0:Y1, x0] = col('w_ol')
                    img[Y0:Y1, x1 - 2:x1] = col('w_dk'); img[Y0:Y1, x1 - 1] = col('w_ol')
                    img[Y0:Y1, x1:x1 + 2] = (img[Y0:Y1, x1:x1 + 2].astype(np.int16) * 0.7).astype(np.uint8)
                    for py in list(range(Y0, Y1 - 3, 24)) + [Y1 - 4]:
                        img[py:py + 4, x0 - 2:x0 + 2] = col('w'); img[py, x0 - 2:x0 + 2] = col('s')
                        img[py:py + 4, x1 - 2:x1 + 2] = col('w'); img[py, x1 - 2:x1 + 2] = col('s')

    # ------------------------------------------------------------ compose
'''
s = s.replace("    # ------------------------------------------------------------ compose\n", BR, 1)
s = s.replace("        self.cliff(F('k', 5, 0.08, 16, 15), top='ash', face=('st_md', 'st_dk', 'st', 'ash_bk'))\n        return self.img",
              "        self.cliff(F('k', 5, 0.08, 16, 15), top='ash', face=('st_md', 'st_dk', 'st', 'ash_bk'))\n        self.bridges()\n        return self.img")
open('painter.py', 'w', encoding='utf8').write(s)
print('patched')
