"""Ambient loops per zone (wind, birds, crickets, waves, lake, lava, swamp, fire, corruption, town, desert).

  python Tools/GameGen/ambience.py -> Assets/Game/Audio/Ambience/amb_<name>.wav

Each loop is rendered a few seconds longer than its length and the extra part is crossfaded onto the start, so it
repeats without a seam. The game mixes up to four of them by region, time of day and interior (AmbienceDirector in Sfx.cs).
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import SR, write_wav, secs, lowpass, highpass, biquad, sine, tri, INSTRUMENTS, midi_hz   # noqa: E402

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Game', 'Audio', 'Ambience'))
XF = 3.0


def rng(seed): return np.random.default_rng(seed)


def place(buf, x, t):
    i = int(t * SR)
    if i >= len(buf): return
    e = min(len(buf), i + len(x)); buf[i:e] += x[:e - i]


def slow_lfo(n, rate, seed, depth=1.0):
    r = rng(seed)
    k = max(4, int(n / SR * rate) + 4)
    pts = r.uniform(-1, 1, k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts) * depth


def loop(x, length):
    n = int(length * SR); f = int(XF * SR)
    out = x[:n].copy()
    w = np.linspace(0, 1, f)
    out[:f] = x[n:n + f] * np.sqrt(1 - w) + x[:f] * np.sqrt(w)
    return out


def norm_rms(x, rms):
    r = math.sqrt(float(np.mean(x ** 2))) or 1
    return np.clip(x * (rms / r), -0.95, 0.95)


def varbp(x, centre_curve, q=0.8, seg=64):
    """band-pass with a slowly moving centre (block-wise)"""
    n = len(x); out = np.zeros(n); L = n // seg
    for k in range(seg):
        a = k * L; b = n if k == seg - 1 else (k + 1) * L
        lo = max(0, a - 2000)
        out[a:b] = biquad(x[lo:b], 'bp', float(centre_curve[(a + b) // 2]), q)[a - lo:]
    return out


def wind(length, seed, strength=1.0, centre=500, hiss=0.0):
    n = int((length + XF) * SR)
    x = rng(seed).uniform(-1, 1, n)
    c = centre * (1 + 0.6 * slow_lfo(n, 0.25, seed + 1))
    y = varbp(x, c, 0.9) * (0.55 + 0.45 * (slow_lfo(n, 0.15, seed + 2) + 1) / 2)
    if hiss: y += highpass(lowpass(x, 7000), 3000) * hiss * (0.5 + 0.5 * slow_lfo(n, 0.3, seed + 3))
    return y * strength


def chirp(f0, f1, dur, seed):
    n = int(dur * SR); t = secs(n)
    f = f0 + (f1 - f0) * np.sin(np.linspace(0, math.pi, n))
    return np.sin(2 * math.pi * np.cumsum(f) / SR) * np.sin(np.linspace(0, math.pi, n)) ** 2


def birds(length, seed):
    n = int((length + XF) * SR); buf = np.zeros(n); r = rng(seed)
    t = 0.3
    while t < length + XF - 1:
        kind = r.integers(0, 3)
        base = r.uniform(2200, 4200)
        if kind == 0:     # little trill
            for k in range(r.integers(3, 7)): place(buf, chirp(base, base * 1.3, 0.05, seed) * 0.5, t + k * 0.07)
        elif kind == 1:   # two-note call
            place(buf, chirp(base, base * 0.8, 0.12, seed) * 0.5, t); place(buf, chirp(base * 0.8, base * 1.1, 0.16, seed) * 0.5, t + 0.2)
        else:             # whistle
            place(buf, chirp(base * 0.6, base * 0.9, 0.35, seed) * 0.35, t)
        t += r.uniform(0.6, 2.8)
    pan = lowpass(rng(seed + 1).uniform(-1, 1, n), 400) * 0.02    # faint leaves
    return buf * 0.6 + pan


def crickets(length, seed):
    n = int((length + XF) * SR); t = secs(n); r = rng(seed)
    out = np.zeros(n)
    for k in range(5):
        f = r.uniform(3800, 5200); rate = r.uniform(14, 22); phase = r.uniform(0, 6)
        gate = (np.sin(2 * math.pi * rate * t + phase) > 0.3).astype(float)
        pulses = (np.sin(2 * math.pi * 0.35 * (k + 1) * t + phase) > -0.2).astype(float)
        out += np.sin(2 * math.pi * f * t) * lowpass(gate * pulses, 300) * r.uniform(0.15, 0.3)
    frogs = np.zeros(n)
    return out * 0.6 + frogs


def waves(length, seed, lake=False):
    n = int((length + XF) * SR); r = rng(seed); x = r.uniform(-1, 1, n)
    period = 3.5 if lake else 7.0
    t = secs(n)
    swell = (0.5 + 0.5 * np.sin(2 * math.pi * t / period + 0.7 * np.sin(2 * math.pi * t / (period * 2.3)))) ** (2.2 if not lake else 1.5)
    body = lowpass(x, 600 if lake else 900) * swell
    foam = highpass(lowpass(x, 6000), 1500) * np.maximum(0, np.gradient(swell) * SR * period * 0.08) * (0.4 if lake else 1.0)
    out = body * 1.2 + foam
    if lake:   # small laps
        for k in range(int(length * 1.2)):
            place(out, biquad(r.uniform(-1, 1, int(0.12 * SR)), 'bp', r.uniform(500, 900), 2) * np.hanning(int(0.12 * SR)) * 0.4, r.uniform(0, length + XF - 0.2))
    return out


def lava(length, seed):
    n = int((length + XF) * SR); r = rng(seed); x = r.uniform(-1, 1, n)
    rumble = lowpass(lowpass(x, 80), 120) * 6 * (0.7 + 0.3 * slow_lfo(n, 0.2, seed))
    out = rumble.copy()
    t = 0.2
    while t < length + XF - 0.5:       # blups and hisses
        d = r.uniform(0.08, 0.2); m = int(d * SR)
        f = r.uniform(80, 200)
        place(out, np.sin(2 * math.pi * np.cumsum(np.linspace(f, f * 2.2, m)) / SR) * np.hanning(m) * 0.5, t)
        if r.random() < 0.3: place(out, highpass(r.uniform(-1, 1, int(0.5 * SR)), 3000) * np.exp(-secs(int(0.5 * SR)) / 0.15) * 0.15, t + d)
        t += r.uniform(0.2, 1.1)
    return out


def swamp(length, seed):
    n = int((length + XF) * SR); r = rng(seed); out = lowpass(r.uniform(-1, 1, n), 300) * 0.3
    t = 0.3
    while t < length + XF - 0.6:
        if r.random() < 0.55:      # frog croak: pulsed low tone
            d = r.uniform(0.25, 0.45); m = int(d * SR); tt = secs(m)
            f = r.uniform(110, 190)
            croak = np.sign(np.sin(2 * math.pi * f * tt)) * (np.sin(2 * math.pi * 28 * tt) > 0) * np.hanning(m)
            place(out, lowpass(croak, 900) * 0.35, t)
        else:                      # bubble
            for k in range(r.integers(1, 4)):
                m = int(0.05 * SR); f = r.uniform(300, 700)
                place(out, np.sin(2 * math.pi * np.cumsum(np.linspace(f, f * 2, m)) / SR) * np.hanning(m) * 0.3, t + k * 0.08)
        t += r.uniform(0.4, 1.6)
    return out + crickets(length, seed + 9) * 0.3


def fire(length, seed):
    n = int((length + XF) * SR); r = rng(seed); x = r.uniform(-1, 1, n)
    out = lowpass(x, 400) * 0.5 * (0.8 + 0.2 * slow_lfo(n, 1.0, seed))
    t = 0.05
    while t < length + XF - 0.1:
        m = int(r.uniform(0.003, 0.012) * SR)
        place(out, highpass(r.uniform(-1, 1, m), 1500) * np.exp(-np.arange(m) / (m / 3)) * r.uniform(0.2, 0.9), t)
        t += r.exponential(0.09)
    return out


def corrupt(length, seed):
    n = int((length + XF) * SR); t = secs(n)
    drone = sum(np.sin(2 * math.pi * f * t * (1 + 0.003 * slow_lfo(n, 0.2, seed + k))) for k, f in enumerate((55, 58.3, 82.4, 116.5))) * 0.25
    whisper = varbp(rng(seed).uniform(-1, 1, n), 1200 * (1 + 0.5 * slow_lfo(n, 0.4, seed + 7)), 3) * 0.4 * (0.5 + 0.5 * slow_lfo(n, 0.2, seed + 8))
    return drone + whisper + wind(length, seed + 3, 0.5, 300)


def town(length, seed):
    """distant murmur of people, a dog now and then, a far hammer"""
    n = int((length + XF) * SR); r = rng(seed)
    murmur = np.zeros(n)
    for k in range(4):
        x = r.uniform(-1, 1, n)
        syl = (np.sin(2 * math.pi * r.uniform(3, 5) * secs(n) + r.uniform(0, 6)) > 0.2).astype(float)
        murmur += varbp(x, 600 + 300 * slow_lfo(n, 2, seed + k), 4) * lowpass(syl, 20) * (0.5 + 0.5 * slow_lfo(n, 0.2, seed + 10 + k))
    out = lowpass(murmur, 1800) * 0.5
    for k in range(3):
        m = int(0.6 * SR); tt = secs(m)
        clang = sum(np.sin(2 * math.pi * f * tt) * np.exp(-tt / d) for f, d in ((1180, .25), (2730, .12)))
        place(out, clang * 0.08, r.uniform(1, length))
    return out + birds(length, seed + 4) * 0.4


AMBIENCES = {
    'wind': (24, lambda: wind(24, 11, 1.0, 450), 0.05),
    'wind_strong': (24, lambda: wind(24, 12, 1.0, 700, hiss=0.25), 0.08),
    'desert': (24, lambda: wind(24, 13, 0.8, 900, hiss=0.5), 0.06),
    'birds': (30, lambda: birds(30, 21), 0.05),
    'crickets': (20, lambda: crickets(20, 31), 0.04),
    'waves': (28, lambda: waves(28, 41), 0.08),
    'lake': (20, lambda: waves(20, 42, lake=True), 0.04),
    'lava': (24, lambda: lava(24, 51), 0.08),
    'swamp': (26, lambda: swamp(26, 61), 0.05),
    'fire': (16, lambda: fire(16, 71), 0.05),
    'corrupt': (24, lambda: corrupt(24, 81), 0.06),
    'town': (30, lambda: town(30, 91), 0.04),
}


def build():
    os.makedirs(OUT, exist_ok=True)
    for name, (length, fn, rms) in AMBIENCES.items():
        x = loop(fn(), length)
        write_wav(os.path.join(OUT, f'amb_{name}.wav'), norm_rms(x, rms))
        print(name, length, flush=True)
    return len(AMBIENCES)


if __name__ == '__main__':
    print(build(), 'ambience loops')
