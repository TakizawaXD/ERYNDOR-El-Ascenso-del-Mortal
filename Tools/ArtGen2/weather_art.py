"""Weather + wind art (2026-11-20).

Assets/Art/World/Nature/grass_tufts_16x16.png   6 tall-grass tufts that sway in the wind (dark-fantasy greens, 2 with blue flowers)
Assets/Art/World/Effects/rain_drop.png            one rain streak (2x9)
Assets/Art/World/Effects/rain_splash_anim_8x8.png 4-frame splash ring
Assets/Game/Audio/amb_rain_loop.wav               8 s seamless rain loop (filtered noise + drop ticks)
usage: python Tools/ArtGen2/weather_art.py
"""
import os, sys, wave
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from painter_dark import DARK      # noqa: E402  (same palette as the ground)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
WA = os.path.join(ROOT, 'Assets', 'Art', 'World')


def c(name, a=255):
    r, g, b = DARK[name][:3]
    return (r, g, b, a)


def tufts():
    rng = np.random.default_rng(7)
    sheet = np.zeros((16, 16 * 6, 4), np.uint8)
    for v in range(6):
        a = np.zeros((16, 16, 4), np.uint8)
        n = 5 + v % 3 * 2
        for i in range(n):
            x0 = 8 + int(rng.integers(-5, 6))
            h = int(rng.integers(6, 14))
            lean = rng.uniform(-0.45, 0.45)
            for k in range(h):
                y = 15 - k
                x = int(round(x0 + lean * k * k / h))
                if not (0 <= x < 16): continue
                t = k / h
                col = c('g_dk2') if t < 0.25 else c('g_dk') if t < 0.5 else c('g_md') if t < 0.8 else c('g_mo')
                if k == h - 1: col = c('g_lt' if i % 2 else 'g_hi')
                a[y, x] = col
                if k < 3 and x + 1 < 16 and a[y, x + 1, 3] == 0: a[y, x + 1] = c('g_ol')
        if v in (2, 5):                                    # glowing blue flower on a stem
            fx, fy = 8 + (v - 3), 4
            for k in range(fy + 1, 13): a[k, fx] = c('g_md')
            for dx, dy, cc in ((0, 0, 'bl_hi'), (-1, 0, 'bl'), (1, 0, 'bl'), (0, -1, 'bl'), (0, 1, 'bl_dk')):
                a[fy + dy, fx + dx] = c(cc)
        sheet[:, v * 16:(v + 1) * 16] = a
    Image.fromarray(sheet).save(os.path.join(WA, 'Nature', 'grass_tufts_16x16.png'))


def rain():
    d = np.zeros((9, 2, 4), np.uint8)
    for y in range(9):
        al = int(40 + 170 * y / 8)
        d[y, 0] = (196, 220, 240, al)
        d[y, 1] = (150, 180, 214, al // 2)
    Image.fromarray(d).save(os.path.join(WA, 'Effects', 'rain_drop.png'))
    s = np.zeros((8, 32, 4), np.uint8)
    rings = [(1.2, 230), (2.2, 190), (3.1, 130), (3.8, 70)]
    for f, (r, al) in enumerate(rings):
        for y in range(8):
            for x in range(8):
                dx, dy = (x + .5 - 4) / 1.0, (y + .5 - 4.5) / 0.55
                dd = (dx * dx + dy * dy) ** .5
                if abs(dd - r * 1.0) < 0.75 and y < 8:
                    s[y, f * 8 + x] = (200, 222, 240, al)
        if f == 0:
            s[2, 3] = s[1, 4] = (220, 236, 250, 220)          # little crown
        if f == 1:
            s[1, 2] = s[0, 5] = (210, 230, 248, 160)
    Image.fromarray(s).save(os.path.join(WA, 'Effects', 'rain_splash_anim_8x8.png'))


def rain_sound():
    sr, secs = 22050, 8.0
    n = int(sr * secs)
    rng = np.random.default_rng(3)
    w = rng.standard_normal(n + sr).astype(np.float64)
    # soft hiss: one-pole low-pass + a bit of high band
    lp = np.zeros_like(w); a = 0.12
    for i in range(1, len(w)): lp[i] = lp[i - 1] + a * (w[i] - lp[i - 1])
    hiss = lp * 0.9 + np.diff(np.concatenate([[0], w])) * 0.05
    # drop ticks
    ticks = np.zeros_like(w)
    for t in rng.integers(0, len(w) - 400, 900):
        L = int(rng.integers(60, 260)); amp = rng.uniform(0.2, 1.0)
        env = np.exp(-np.arange(L) / (L / 5))
        ticks[t:t + L] += rng.standard_normal(L) * env * amp
    lp2 = np.zeros_like(ticks); a2 = 0.35
    for i in range(1, len(ticks)): lp2[i] = lp2[i - 1] + a2 * (ticks[i] - lp2[i - 1])
    sig = hiss * 0.55 + lp2 * 0.5
    # seamless loop: crossfade the extra second into the start
    body, tail = sig[:n].copy(), sig[n:n + sr]
    fade = np.linspace(0, 1, sr)
    body[:sr] = body[:sr] * fade + tail * (1 - fade)
    body /= np.abs(body).max() + 1e-9
    pcm = (body * 0.7 * 32767).astype(np.int16)
    with wave.open(os.path.join(ROOT, 'Assets', 'Game', 'Audio', 'amb_rain_loop.wav'), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(pcm.tobytes())


if __name__ == '__main__':
    tufts(); rain(); rain_sound()
    print('weather art ok')
