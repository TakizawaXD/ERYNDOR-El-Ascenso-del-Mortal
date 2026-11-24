"""Sound effects, second generation: every effect re-synthesised with filtered noise, inharmonic metal, formant voices and
several variants (sfx_<name>_1.wav, _2, _3) that the game picks at random together with a small pitch/volume change.

  python Tools/GameGen/sfx2.py            -> Assets/Game/Audio/sfx_*.wav (replaces the ones of sfx.py / sfx_extra.py)

Boss effects of music_boss.py (boss_phase, quake, wave, summon, ice, boss_win) are left untouched.
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import (SR, write_wav, secs, lowpass, highpass, biquad, formant, saw, pulse, sine, tri, noise,  # noqa: E402
                   env_perc, env_adsr, reverb, softclip, INSTRUMENTS, midi_hz, drum)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Game', 'Audio'))
VOWELS = {'a': (800, 1200, 2500), 'e': (500, 1800, 2500), 'i': (300, 2200, 2900), 'o': (500, 900, 2400),
          'u': (330, 800, 2300), 'aa': (700, 1100, 2400), 'm': (250, 1100, 2300)}


def N(n_or_s, seed):
    n = n_or_s if isinstance(n_or_s, int) else int(n_or_s * SR)
    return np.random.default_rng(seed).uniform(-1, 1, n)


def pad(x, n):
    return np.concatenate([x, np.zeros(max(0, n - len(x)))])[:n] if len(x) < n else x


def mixall(*xs):
    n = max(len(x) for x in xs)
    return sum(pad(x, n) for x in xs)


def msum(gen):
    return mixall(*list(gen))


def cat(*xs, gap=0.0):
    out = []
    for x in xs:
        out.append(x)
        if gap: out.append(np.zeros(int(gap * SR)))
    return np.concatenate(out)


def at(x, t, n=None):
    """x delayed by t seconds"""
    return np.concatenate([np.zeros(int(t * SR)), x])


def tone_sweep(f0, f1, dur, wave='sine', curve=1.0):
    n = int(dur * SR); k = np.linspace(0, 1, n) ** curve
    f = f0 + (f1 - f0) * k
    return {'sine': sine, 'saw': saw, 'tri': tri}[wave](f) if wave != 'sq' else pulse(f, 0.5)


def metal(freqs, decays, dur, seed=0, amps=None):
    t = secs(int(dur * SR))
    r = np.random.default_rng(seed)
    x = np.zeros(len(t))
    for i, (f, d) in enumerate(zip(freqs, decays)):
        a = amps[i] if amps else 1.0 / (i + 1) ** 0.6
        x += a * np.sin(2 * math.pi * f * (1 + r.uniform(-0.01, 0.01)) * t + r.uniform(0, 6)) * np.exp(-t / d)
    return x


def whoosh(dur, f0, f1, seed, q=1.2, peak=0.45):
    """band-passed noise whose centre sweeps; amplitude bell-shaped (sword swing, roll, gust)"""
    n = int(dur * SR); x = N(n, seed)
    seg = 8; out = np.zeros(n)
    for k in range(seg):
        a = k * n // seg; b = (k + 1) * n // seg
        fc = f0 + (f1 - f0) * (k + 0.5) / seg
        out[a:b] = biquad(x, 'bp', fc, q)[a:b]
    t = np.linspace(0, 1, n)
    e = np.where(t < peak, (t / peak) ** 1.5, ((1 - t) / (1 - peak)) ** 2)
    return out * e * 2.0


def voice(f0_curve, vowels, dur, seed=0, breath=0.15, rough=0.0, nasal=0.0, scale=1.0, src='saw'):
    """formant voice: pitch curve (list of (t, hz)), vowel sequence (list of (t, vowel)), formants scaled by `scale`"""
    n = int(dur * SR); t = secs(n)
    pts_t = [p[0] * dur for p in f0_curve]; pts_f = [p[1] for p in f0_curve]
    f = np.interp(t, pts_t, pts_f)
    r = np.random.default_rng(seed)
    f = f * (1 + 0.01 * lowpass(r.uniform(-1, 1, n), 30) * 5)          # jitter
    s = saw(f) if src == 'saw' else pulse(f, 0.3)
    if rough: s = s * (1 + rough * lowpass(r.uniform(-1, 1, n), 60) * 4)
    s = s + breath * r.uniform(-1, 1, n)
    out = np.zeros(n)
    vt = [v[0] * dur for v in vowels]
    filt = [formant(s, [x * scale for x in VOWELS[v[1]]], [6, 8, 10], [1, 0.7, 0.35]) for v in vowels]
    for i in range(len(vowels)):
        # triangular weight around each vowel's time
        left = vt[i - 1] if i > 0 else -1; right = vt[i + 1] if i + 1 < len(vowels) else dur + 1
        w = np.clip(np.minimum((t - left) / max(vt[i] - left, 1e-3), (right - t) / max(right - vt[i], 1e-3)), 0, 1)
        if i == 0: w = np.where(t <= vt[0], 1, w)
        if i == len(vowels) - 1: w = np.where(t >= vt[-1], 1, w)
        out += filt[i] * w
    if nasal: out += nasal * biquad(s, 'bp', 250 * scale, 4)
    return out


def env(x, a=0.01, r=0.1):
    n = len(x); t = secs(n); d = n / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.clip((d - t) / max(r, 1e-4), 0, 1)
    return x * e


def norm(x, peak=0.8):
    m = float(np.max(np.abs(x))) or 1.0
    return x * (peak / m)


def verb(x, amount=0.2, size=0.6):
    y = np.concatenate([x, np.zeros(int(0.8 * SR))])
    return y + reverb(y, size) * amount * 3


# =============================================================== the effects
def steps(surface, v):
    s = 100 + v * 17 + hash(surface) % 50
    d = {
        'grass': lambda: mixall(env(biquad(N(.09, s), 'bp', 3000 + v * 300, 0.9), .004, .07) * 0.5, env(lowpass(N(.05, s + 1), 400), .002, .04) * 0.6),
        'dirt': lambda: mixall(env(lowpass(N(.07, s), 900 + v * 80), .002, .06), env(biquad(N(.05, s + 2), 'bp', 2200, 2), .002, .03) * 0.3),
        'stone': lambda: mixall(env(biquad(N(.04, s), 'bp', 2200 + v * 200, 2.5), .001, .03) * 0.8, env(tone_sweep(170 + v * 10, 120, .05), .001, .04) * 0.5),
        'wood': lambda: mixall(env(tone_sweep(210 + v * 15, 170, .09), .001, .08) * 0.8, env(biquad(N(.06, s), 'bp', 900, 3), .001, .05) * 0.6),
        'sand': lambda: env(lowpass(highpass(N(.12, s), 1500), 6000), .03, .08) * 0.4,
        'snow': lambda: msum(at(env(biquad(N(.012, s + k), 'bp', 2500 + 300 * k, 3), .001, .01), k * 0.012 + v * 0.002) for k in range(7)) * 0.5,
        'water': lambda: mixall(env(biquad(N(.18, s), 'bp', 1300, 1.2), .01, .15) * 0.6, env(tone_sweep(700, 1400 + v * 200, .06), .002, .05) * 0.15),
        'mud': lambda: mixall(env(lowpass(N(.14, s), 600), .01, .12), voice([(0, 90), (1, 70)], [(0, 'o'), (1, 'u')], .14, s, 0.6) * 0.15),
        'ash': lambda: mixall(env(lowpass(N(.06, s), 1500), .002, .05), msum(at(env(biquad(N(.01, s + k), 'bp', 3500, 4), .001, .008), k * .015) for k in range(4)) * 0.4),
    }[surface]()
    return norm(d, 0.45)


def swing(kind, v):
    s = 300 + v * 7
    if kind == 'light': x = whoosh(.13, 1500 + v * 200, 3800, s, 1.6, .35)
    elif kind == 'heavy': x = mixall(whoosh(.3, 400 + v * 60, 1400, s, 1.1, .55), env(tone_sweep(120, 70, .3), .05, .1) * 0.25)
    elif kind == 'thrust': x = mixall(whoosh(.11, 2500, 1800 + v * 200, s, 2.0, .2), env(biquad(N(.08, s), 'hp', 6000), .002, .06) * 0.2)
    else: x = whoosh(.18, 800 + v * 150, 2600, s, 1.3, .45)
    return norm(x, 0.55)


def hit(kind, v):
    s = 500 + v * 11
    thud = env(tone_sweep(150 + v * 10, 60, .12), .001, .1)
    if kind == 'blade':
        x = mixall(env(biquad(N(.1, s), 'hp', 2500), .001, .06) * 0.7, metal([2900 + v * 100, 4300, 6100], [.04, .03, .02], .12, s) * 0.25, thud * 0.7)
    elif kind == 'blunt':
        x = mixall(env(tone_sweep(110, 45, .2), .001, .18) * 1.2, env(lowpass(N(.12, s), 1200), .001, .08) * 0.8)
    elif kind == 'pierce':
        x = mixall(env(biquad(N(.05, s), 'bp', 3500, 2), .001, .03), env(lowpass(N(.1, s + 1), 700), .005, .07) * 0.6, thud * 0.5)
    elif kind == 'fire':
        x = mixall(env(lowpass(N(.35, s), 2500), .01, .3) * 0.6, msum(at(env(biquad(N(.01, s + k), 'hp', 3000), .001, .008), k * .03) for k in range(8)) * 0.5, thud * 0.4)
    elif kind == 'frost':
        x = mixall(metal([3100, 4700, 6900, 8200], [.15, .1, .07, .05], .35, s) * 0.4, env(biquad(N(.08, s), 'hp', 4000), .001, .05) * 0.5, thud * 0.4)
    elif kind == 'venom':
        x = mixall(env(biquad(N(.3, s), 'bp', 5000, 1.5), .02, .25) * 0.6, thud * 0.5)
    elif kind == 'holy':
        x = mixall(metal([1320, 1980, 2640, 3960], [.4, .3, .2, .1], .5, s) * 0.35, thud * 0.5)
    elif kind == 'crit':
        x = mixall(hit('blade', v), metal([1760, 2640, 3520], [.25, .15, .1], .3, s) * 0.35, thud)
    elif kind == 'flesh':   # player gets hit
        x = mixall(env(lowpass(N(.1, s), 1000), .001, .08), thud)
    else:
        x = mixall(env(biquad(N(.08, s), 'bp', 1800, 0.8), .001, .06), thud * 0.8)
    return norm(x, 0.7)


def vox(species, act, v):
    """enemy voices: orc (low growl), demon (hiss + distorted growl), blood (wet gurgle)"""
    s = 900 + v * 13 + len(act)
    if species == 'orc':
        f = {'alert': [(0, 95), (.4, 120), (1, 85)], 'attack': [(0, 110), (.3, 130), (1, 90)], 'hurt': [(0, 150), (1, 100)], 'die': [(0, 130), (.3, 110), (1, 55)]}[act]
        vw = {'alert': [(0, 'u'), (.5, 'aa')], 'attack': [(0, 'aa'), (1, 'a')], 'hurt': [(0, 'u'), (1, 'o')], 'die': [(0, 'aa'), (.6, 'o'), (1, 'u')]}[act]
        d = {'alert': .5, 'attack': .3, 'hurt': .22, 'die': .8}[act]
        x = voice([(t, h * (1 + v * 0.05)) for t, h in f], vw, d, s, 0.25, rough=0.5, scale=0.75)
    elif species == 'demon':
        d = {'alert': .55, 'attack': .3, 'hurt': .25, 'die': .9}[act]
        f = {'alert': [(0, 70), (1, 60)], 'attack': [(0, 80), (1, 65)], 'hurt': [(0, 120), (1, 80)], 'die': [(0, 90), (1, 35)]}[act]
        growl = voice(f, [(0, 'o'), (1, 'aa')], d, s, 0.3, rough=0.9, scale=0.6)
        hiss = env(biquad(N(d, s), 'hp', 3500), .03, d * 0.6) * 0.6
        x = softclip(mixall(growl, hiss) * 2, 2)
    elif species == 'blood':
        d = {'alert': .5, 'attack': .3, 'hurt': .25, 'die': .8}[act]
        bubbles = msum(at(env(tone_sweep(300 + 90 * k, 700 + 60 * k, .05), .002, .04), k * d / 7 + v * .01) for k in range(7)) * 0.3
        gurg = voice([(0, 160), (1, 110)], [(0, 'o'), (.5, 'u'), (1, 'o')], d, s, 0.3, rough=0.8, scale=0.9) * 0.8
        x = mixall(gurg, bubbles, env(lowpass(N(d, s), 800), .02, d * .5) * 0.4)
    else:  # player
        d = {'hurt': .2, 'die': .7, 'tired': .5}[act]
        if act == 'tired':
            x = cat(env(formant(N(.18, s), VOWELS['a'], [3, 4, 5]), .03, .12), env(formant(N(.2, s + 1), VOWELS['o'], [3, 4, 5]), .03, .14), gap=0.08)
        else:
            f = [(0, 220), (1, 170)] if act == 'hurt' else [(0, 200), (.4, 180), (1, 90)]
            x = voice(f, [(0, 'u'), (1, 'a')] if act == 'hurt' else [(0, 'aa'), (1, 'o')], d, s, 0.3, scale=1.0)
    return norm(env(x, .01, .08), 0.7)


def animal(kind, v):
    s = 1300 + v * 7
    if kind == 'chicken':
        clucks = []
        for k in range(3 + v % 2):
            f0 = 520 + 40 * ((k + v) % 3)
            clucks.append(voice([(0, f0), (1, f0 * 1.2)], [(0, 'o'), (1, 'a')], .07, s + k, 0.2, scale=1.8))
        x = cat(*clucks, gap=0.06)
        if v == 2: x = cat(x, voice([(0, 600), (.5, 900), (1, 700)], [(0, 'a'), (1, 'e')], .35, s, 0.2, scale=1.8), gap=0.05)
    elif kind == 'pig':
        g = lambda k: voice([(0, 180 + 20 * k), (1, 140)], [(0, 'o'), (1, 'u')], .13, s + k, 0.3, rough=0.6, nasal=0.8, scale=1.0)
        x = cat(g(0), g(1), gap=0.05) if v != 1 else cat(g(0), gap=0)
    elif kind == 'cow':
        x = voice([(0, 115), (.2, 125), (.8, 110), (1, 95)], [(0, 'm'), (.25, 'o'), (.8, 'u')], 1.1 + v * .15, s, 0.15, nasal=0.6, scale=0.8)
    elif kind == 'sheep':
        n = int((0.6 + v * .1) * SR); t = secs(n)
        x = voice([(0, 300), (1, 270)], [(0, 'm'), (.15, 'e'), (1, 'a')], n / SR, s, 0.25, scale=1.3)
        x *= 1 + 0.6 * np.sin(2 * math.pi * 9 * t)
    elif kind == 'cat_meow':
        d = 0.55 + v * 0.08
        x = voice([(0, 520 + v * 40), (.35, 760 + v * 30), (1, 480)], [(0, 'i'), (.4, 'aa'), (1, 'u')], d, s, 0.12, scale=1.7)
    elif kind == 'cat_purr':
        n = int(2.0 * SR); t = secs(n)
        pulses = (0.5 + 0.5 * np.sin(2 * math.pi * 26 * t)) ** 3
        x = lowpass(N(n, s), 300) * pulses * (1 + 0.3 * np.sin(2 * math.pi * 0.7 * t)) + 0.3 * np.sin(2 * math.pi * 26 * t) * pulses
        x = env(x, .2, .3)
    return norm(env(x, .005, .05), 0.6)


def ui(kind):
    I = INSTRUMENTS
    def nt(inst, midi, dur, vel=0.6, t0=0.0): return at(I[inst](midi_hz(midi), dur, vel), t0)
    if kind == 'select': return norm(nt('pulse12', 84, .03, .5), .25)
    if kind == 'confirm': return norm(mixall(nt('pulse25', 79, .05), nt('pulse25', 86, .08, .6, .05), nt('bell', 91, .1, .3, .05)), .35)
    if kind == 'cancel': return norm(mixall(nt('pulse25', 79, .05), nt('pulse25', 72, .09, .6, .05)), .3)
    if kind == 'menu_open': return norm(mixall(whoosh(.12, 900, 2400, 3, 1.5, .5) * .4, nt('harp', 74, .2, .5, .02), nt('harp', 81, .2, .5, .06)), .35)
    if kind == 'menu_close': return norm(mixall(whoosh(.1, 2200, 900, 4, 1.5, .3) * .4, nt('harp', 81, .2, .5), nt('harp', 74, .2, .5, .04)), .3)
    if kind == 'inv_open':   # leather bag
        return norm(mixall(env(lowpass(N(.15, 5), 1500), .01, .1), env(biquad(N(.08, 6), 'bp', 2500, 2), .005, .05) * 0.5, at(metal([2400, 3100], [.05, .04], .1, 2) * .2, .07)), .4)
    if kind == 'buy': return norm(mixall(coin(0), at(metal([1600, 2300, 3300], [.3, .2, .1], .4, 9) * .4, .08), nt('bell', 96, .2, .3, .1)), .55)
    if kind == 'sell': return norm(mixall(coin(1), nt('pulse25', 88, .05, .4, .05)), .5)
    if kind == 'equip': return norm(mixall(env(lowpass(N(.1, 8), 2000), .01, .08) * .6, metal([1800, 2700, 4100], [.12, .08, .05], .2, 4) * .4), .45)
    if kind == 'error': return norm(mixall(nt('pulse50', 50, .07, .5), nt('pulse50', 49, .1, .5, .08)), .3)
    if kind == 'page': return norm(env(biquad(N(.12, 11), 'bp', 3500, 1), .03, .07), .25)
    raise ValueError(kind)


def coin(v):
    return mixall(metal([2637 + v * 50, 3951, 5274], [.18, .12, .08], .3, 20 + v) * .5, at(metal([3520 + v * 60, 5274], [.2, .1], .3, 30 + v) * .4, .06))


def world(kind, v=0):
    I = INSTRUMENTS
    def nt(inst, midi, dur, vel=0.6, t0=0.0): return at(I[inst](midi_hz(midi), dur, vel), t0)
    s = 2000 + v * 5
    if kind == 'door_open':
        creak = voice([(0, 90), (.5, 140), (1, 110)], [(0, 'o'), (1, 'e')], .45, s, 0.1, rough=1.5, scale=1.4, src='pulse') * 0.4
        latch = env(biquad(N(.04, s), 'bp', 2500, 3), .001, .03)
        return norm(verb(mixall(latch, at(creak, .04)), .15), .5)
    if kind == 'door_close':
        return norm(verb(mixall(env(tone_sweep(120, 70, .2), .002, .15) * 1.2, env(lowpass(N(.1, s), 900), .002, .08), at(env(biquad(N(.03, s), 'bp', 2500, 3), .001, .02), .12) * .5), .2), .55)
    if kind == 'gate':
        return norm(verb(mixall(whoosh(.7, 300, 2400, s, 1.0, .5) * .6, nt('celesta', 76, .5, .3, .1), nt('celesta', 83, .5, .3, .2), nt('celesta', 88, .6, .3, .3)), .35, 1.2), .5)
    if kind == 'chest':
        creak = voice([(0, 120), (1, 170)], [(0, 'o'), (1, 'a')], .3, s, 0.1, rough=1.2, scale=1.3, src='pulse') * .35
        sparkle = msum(nt('celesta', m, .2, .35, .25 + i * .06) for i, m in enumerate([79, 83, 86, 91]))
        return norm(verb(mixall(creak, sparkle), .25), .6)
    if kind == 'coin': return norm(coin(v), .5)
    if kind == 'potion':
        gulp = cat(*[env(tone_sweep(300 + 40 * k, 180, .07), .005, .05) for k in range(2)], gap=.06)
        return norm(mixall(gulp * .8, at(msum(nt('bell', m, .25, .3, i * .07) for i, m in enumerate([79, 84, 88])), .2)), .5)
    if kind == 'eat': return norm(cat(env(lowpass(N(.07, s), 2500), .003, .05), env(lowpass(N(.07, s + 1), 2200), .003, .05), env(lowpass(N(.08, s + 2), 2000), .003, .06), gap=.07), .45)
    if kind == 'gather': return norm(mixall(env(biquad(N(.12, s), 'bp', 2500, .9), .01, .1) * .6, nt('pluck' if False else 'harp', 81 + v * 2, .15, .5, .05)), .45)
    if kind == 'pickup': return norm(mixall(nt('pulse25', 81, .04, .5), nt('pulse25', 88, .07, .5, .04)), .35)
    if kind == 'break':
        cracks = msum(at(env(biquad(N(.05, s + k), 'bp', 1200 + 400 * k, 2), .001, .04), k * .03) for k in range(4))
        return norm(mixall(cracks, env(tone_sweep(160, 70, .15), .001, .12) * .8, at(env(lowpass(N(.2, s), 2000), .01, .15) * .4, .05)), .6)
    if kind == 'anvil': return norm(mixall(drum('anvil', 1, seed=v), env(biquad(N(.03, s), 'hp', 3000), .001, .02) * .4), .5)
    if kind == 'craft': return norm(mixall(env(lowpass(N(.1, s), 2000), .01, .08) * .5, nt('harp', 72, .2, .5, .05), nt('harp', 79, .2, .5, .11), nt('bell', 84, .3, .3, .17)), .45)
    if kind == 'talk':
        syll = [voice([(0, 260 + 30 * k), (1, 240)], [(0, 'a' if k % 2 else 'e'), (1, 'o')], .06, s + k, .1, scale=1.1, src='pulse') for k in range(3)]
        return norm(cat(*syll, gap=.02), .3)
    if kind == 'bomb':
        return norm(verb(mixall(env(lowpass(N(.9, s), 900), .002, .7) * 1.3, env(tone_sweep(90, 30, .6), .001, .5) * 1.2, env(biquad(N(.2, s), 'hp', 3000), .001, .1) * .5), .3, 1.0), .8)
    if kind == 'arrow':
        twang = env(INSTRUMENTS['bass_pluck'](midi_hz(43 + v), .12, 1), .001, .1)
        return norm(mixall(twang * .8, at(whoosh(.18, 2500, 1500, s, 2.0, .2) * .5, .03)), .5)
    if kind == 'fireball':
        return norm(mixall(whoosh(.5, 300, 1200, s, .8, .3) * .8, env(lowpass(N(.5, s + 1), 1200), .05, .4) * .6, msum(at(env(biquad(N(.008, s + k), 'hp', 3000), .001, .006), k * .05) for k in range(8)) * .4), .6)
    if kind == 'spit':
        return norm(mixall(env(biquad(N(.15, s), 'bp', 1800, 1.5), .005, .12), env(tone_sweep(400, 900, .08), .005, .06) * .3), .5)
    if kind == 'spell':
        return norm(verb(mixall(whoosh(.4, 600, 3000, s, 1.5, .6) * .4, msum(nt('celesta', m, .25, .3, i * .05) for i, m in enumerate([72, 79, 84, 91]))), .3, 1.0), .5)
    if kind == 'heal':
        return norm(verb(msum(nt('bell', m, .4, .35, i * .08) for i, m in enumerate([72, 76, 79, 84, 88])), .3, 1.1), .5)
    if kind == 'blink':
        return norm(mixall(tone_sweep(1800, 300, .2, 'tri') * env(np.ones(int(.2 * SR)), .005, .1) * .4, whoosh(.2, 3000, 800, s, 2.0, .2) * .5), .45)
    if kind == 'block':     # shield clang
        return norm(mixall(metal([820 + v * 30, 1270, 2110, 3170], [.18, .12, .08, .05], .35, s), env(biquad(N(.05, s), 'hp', 2000), .001, .03) * .6, env(tone_sweep(140, 90, .08), .001, .06) * .6), .65)
    if kind == 'parry':
        return norm(verb(mixall(metal([2350, 3560, 4710, 6120], [.45, .3, .2, .12], .7, s), env(biquad(N(.05, s), 'hp', 3000), .001, .03) * .8, at(whoosh(.15, 3000, 1500, s, 2, .3) * .3, .02)), .3), .7)
    if kind == 'riposte':
        return norm(mixall(swing('heavy', v), at(hit('crit', v), .1)), .75)
    if kind == 'guard_break':
        return norm(mixall(metal([700, 1050, 1690], [.1, .07, .05], .2, s), env(lowpass(N(.25, s), 1500), .002, .2), env(tone_sweep(300, 90, .3, 'tri'), .002, .25) * .4), .7)
    if kind == 'roll':
        return norm(mixall(whoosh(.25, 500, 1200, s, .9, .4) * .6, at(env(lowpass(N(.08, s), 500), .002, .06), .2) * .7), .45)
    if kind == 'boss_roar':
        return norm(verb(softclip(voice([(0, 70), (.3, 95), (1, 55)], [(0, 'o'), (.4, 'aa'), (1, 'u')], 1.2, s, 0.4, rough=1.2, scale=0.55) * 3, 2), .3, 1.2), .8)
    if kind == 'levelup':   # short sparkle (the full fanfare is jingle_levelup)
        return norm(mixall(msum(nt('pulse25', m, .06, .5, i * .05) for i, m in enumerate([72, 76, 79, 84, 88])), nt('bell', 96, .3, .3, .25)), .45)
    if kind == 'victory':   # quest done / gift (short)
        return norm(verb(mixall(*[nt('brass', m, d, .55, t) for m, d, t in ((74, .12, 0), (78, .12, .12), (81, .12, .24), (86, .4, .36))]), .2), .5)
    if kind == 'gameover':
        return norm(verb(mixall(*[nt('flute', m, .3, .5, i * .3) for i, m in enumerate([69, 65, 62, 57])]), .3), .45)
    if kind == 'splash':
        return norm(mixall(env(biquad(N(.35, s), 'bp', 1200, .8), .005, .3), msum(at(env(tone_sweep(500 + 200 * k, 1500, .04), .002, .03), .05 + k * .04) for k in range(4)) * .3), .55)
    if kind == 'fire_ignite':
        return norm(mixall(whoosh(.5, 200, 900, s, .7, .3), msum(at(env(biquad(N(.008, s + k), 'hp', 2500), .001, .006), .1 + k * .04) for k in range(10)) * .5), .5)
    raise ValueError(kind)


def build(root=ROOT):
    made = 0
    def w(name, x):
        nonlocal made
        write_wav(os.path.join(root, f'sfx_{name}.wav'), x); made += 1
    for surf in ('grass', 'dirt', 'stone', 'wood', 'sand', 'snow', 'water', 'mud', 'ash'):
        for v in range(3): w(f'step_{surf}_{v + 1}', steps(surf, v))
    for v in range(3): w(f'step_{v + 1}', steps('dirt', v))
    for v in range(3):
        w(f'swing_{v + 1}', swing('sword', v)); w(f'swing_light_{v + 1}', swing('light', v))
        w(f'heavy_swing_{v + 1}', swing('heavy', v)); w(f'swing_thrust_{v + 1}', swing('thrust', v))
        w(f'hit_{v + 1}', hit('generic', v))
        for k in ('blade', 'blunt', 'pierce', 'fire', 'frost', 'venom', 'holy', 'crit', 'flesh'): w(f'hit_{k}_{v + 1}', hit(k, v))
    for sp in ('orc', 'demon', 'blood'):
        for act in ('alert', 'attack', 'hurt', 'die'):
            for v in range(2): w(f'vox_{sp}_{act}_{v + 1}', vox(sp, act, v))
    for v in range(2):
        w(f'player_hurt_{v + 1}', mixall(vox('player', 'hurt', v), hit('flesh', v) * .6))
        w(f'enemy_hurt_{v + 1}', hit('generic', v)); w(f'enemy_die_{v + 1}', mixall(hit('blunt', v), world('break', v) * .3))
    w('player_die', vox('player', 'die', 0)); w('tired', vox('player', 'tired', 0))
    for a in ('chicken', 'pig', 'cow', 'sheep', 'cat_meow'):
        for v in range(3): w(f'{a}_{v + 1}', animal(a, v))
    w('cat_purr', animal('cat_purr', 0))
    for k in ('select', 'confirm', 'cancel', 'menu_open', 'menu_close', 'inv_open', 'buy', 'sell', 'equip', 'error', 'page'): w(k, ui(k))
    for k in ('door_open', 'door_close', 'gate', 'chest', 'potion', 'eat', 'pickup', 'talk', 'bomb', 'spell', 'heal', 'blink', 'boss_roar',
              'levelup', 'victory', 'gameover', 'guard_break', 'splash', 'fire_ignite', 'craft'):
        w(k, world(k))
    for k in ('coin', 'gather', 'break', 'anvil', 'arrow', 'fireball', 'spit', 'block', 'parry', 'riposte', 'roll'):
        for v in range(3 if k not in ('riposte', 'parry') else 2): w(f'{k}_{v + 1}', world(k, v))
    # the plain names that used to exist stay as aliases of variant 1 (old saves / code that asks for them exactly)
    import shutil
    for k in ('step', 'swing', 'heavy_swing', 'hit', 'player_hurt', 'enemy_hurt', 'enemy_die', 'coin', 'gather', 'break', 'anvil',
              'arrow', 'fireball', 'spit', 'block', 'parry', 'riposte', 'roll'):
        p = os.path.join(root, f'sfx_{k}.wav')
        if os.path.exists(p): os.remove(p)
        if os.path.exists(p + '.meta'): os.remove(p + '.meta')
    return made


if __name__ == '__main__':
    print(build(sys.argv[1] if len(sys.argv) > 1 else ROOT), 'effects')
