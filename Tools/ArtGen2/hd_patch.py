s = open('nature_hd.py', encoding='utf8').read()
a = s.index('def trunk_hd('); b = s.index('def oak_hd(')
s = s[:a] + '''def trunk_hd(c, cx, top, bot, w, cols=('w_lt', 'w', 'w_dk', 'w_ol'), canopy_shadow=4):
    """slightly tapered trunk, bark fissures, three spreading roots per side"""
    lt, md, dk, ol = cols
    t = C(c.w, c.h)
    for y in range(top, bot + 1):
        p = (y - top) / max(1, bot - top)
        half = w / 2 * (0.85 + 0.25 * p)
        x0, x1 = int(round(cx - half)), int(round(cx + half - 1))
        for x in range(x0, x1 + 1):
            rel = (x - x0) / max(1, x1 - x0)
            colr = lt if rel < .25 else md if rel < .65 else dk
            if (x * 7 + (y // 3)) % 5 == 0 and 0.15 < rel < 0.85: colr = dk
            if y < top + canopy_shadow: colr = dk if rel > .3 else md
            t.px(x, y, colr)
    # roots: diagonal prongs fanning out along the ground
    for side in (-1, 1):
        for k, (ln, drop) in enumerate(((6, 4), (4, 2), (3, 1))):
            x = cx + side * (w // 2 - 1 - k)
            y = bot - drop
            for i in range(ln):
                xx = x + side * i; yy = y + (i * drop) // ln
                t.px(xx, yy, md if i < ln - 1 else dk); t.px(xx, yy + 1, dk)
    t.outline(ol)
    c.paste(t, 0, 0)


''' + s[b:]
s = s.replace("    trunk_hd(c, w // 2, h - 34, h - 4, 10)\n    crown(c, w / 2, R + 3, R, cols, outline, seed)",
              "    trunk_hd(c, w // 2, h - 30, h - 6, 9)\n    crown(c, w / 2, R + 8, R, cols, outline, seed)")
s = s.replace("    trunk_hd(c, 22, 30, 52, 7)\n    crown(c, 22, 19, 16.5, cols, outline, seed, n_ring=6)",
              "    trunk_hd(c, 22, 32, 50, 7)\n    crown(c, 22, 22, 16.5, cols, outline, seed, n_ring=6)")
a = s.index('def pine_hd('); b = s.index('def bush_hd(')
s = s[:a] + '''def pine_hd(snow=False, seed=7):
    """layered fir: each tier has ragged needle tips, lit left side, shade under the tier above"""
    c = C(40, 70)
    c.ellipse(20, 65, 13, 3.5, SHADOW)
    trunk_hd(c, 20, 54, 64, 5, canopy_shadow=3)
    t = C(40, 70)
    r = np.random.default_rng(seed)
    tiers = [(5, 8, 10), (12, 11, 12), (20, 14, 13), (29, 17, 14), (39, 19, 13)]
    for ti, (ty, hw, th) in enumerate(reversed(tiers)):
        tip = [r.integers(0, 3) for _ in range(40)]
        for y in range(th):
            p = (y + 1) / th
            half = hw * p + (1.5 if y == th - 1 else 0)
            for x in range(int(20 - half), int(20 + half) + 1):
                rel = (x - (20 - half)) / max(1, 2 * half)
                if y >= th - tip[x % 40] and (x % 3) != 1: continue          # ragged hanging tips
                colr = 'g_hi' if rel < .18 and y < th - 3 else 'g_lt' if rel < .45 else 'g_md' if rel < .75 else 'g_dp'
                if y >= th - 3: colr = 'g_dp' if rel > .35 else 'g_md'
                if y < 3: colr = 'g_dp2' if rel > .5 else 'g_dp'                   # shadow of the tier above
                if (x * 5 + y * 3 + ti) % 9 == 0 and rel < .6: colr = 'g_hi'
                if snow and y < 4 and ((x + ti) % 4 != 0): colr = 'sn' if rel < .55 else 'sn_md'
                t.px(x, ty + y, colr)
    for y in (2, 3, 4): t.px(20, y, 'sn' if snow else 'g_lt')
    t.outline('g_ol2')
    c.paste(t, 0, 0)
    return c


''' + s[b:]
open('nature_hd.py', 'w', encoding='utf8').write(s)
print('ok')
