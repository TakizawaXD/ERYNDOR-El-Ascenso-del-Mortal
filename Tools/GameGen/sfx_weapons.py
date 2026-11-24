"""Weapon sounds for the combat animation sets (2026-11-21). Uses the synth helpers of sfx2.py; adds new names only.

  python Tools/GameGen/sfx_weapons.py   -> Assets/Game/Audio/sfx_<name>_<1..3>.wav

  wpn_swing_light / wpn_swing_blade / wpn_swing_heavy / wpn_swing_staff / wpn_swing_legend / wpn_thrust  (swing per set)
  wpn_whiff (a blow that hits nothing), hammer_slam (ground impact), bow_draw, bow_release, crossbow_load, crossbow_shot,
  magic_charge, magic_bolt, magic_burst.  Sfx.Play("x") picks sfx_x or a random sfx_x_N.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import sfx2 as S
from synth import write_wav, lowpass, highpass, biquad, sine, tri, noise, saw

ROOT = S.ROOT


def swing(kind, v):
    s = 900 + v * 13
    if kind == 'light':
        x = S.whoosh(.11, 1800 + v * 250, 4200, s, 1.8, .3)
    elif kind == 'blade':
        x = S.mixall(S.whoosh(.17, 900 + v * 150, 3000, s, 1.4, .42), S.env(biquad(S.N(.05, s + 1), 'hp', 6500), .002, .04) * .15)
    elif kind == 'heavy':
        x = S.mixall(S.whoosh(.34, 300 + v * 50, 1200, s, 1.0, .6), S.env(S.tone_sweep(110, 60, .34), .06, .12) * .3)
    elif kind == 'staff':
        x = S.mixall(S.whoosh(.2, 600 + v * 100, 1800, s, 1.1, .45), S.env(S.tone_sweep(160, 120, .18), .01, .1) * .15)
    elif kind == 'legend':
        x = S.mixall(S.whoosh(.22, 1000, 3600, s, 1.5, .4), S.metal([1320 + v * 40, 1980, 2970], [.25, .18, .1], .3, s) * .18)
    else:  # thrust
        x = S.mixall(S.whoosh(.1, 2600, 1700 + v * 200, s, 2.2, .22), S.env(biquad(S.N(.06, s), 'hp', 6000), .002, .05) * .25)
    return S.norm(x, .55)


def whiff(v):
    s = 1300 + v
    return S.norm(S.mixall(S.whoosh(.09, 2500 + v * 300, 1200, s, 2.0, .3)), .32)


def hammer_slam(v):
    s = 1400 + v * 7
    x = S.mixall(S.env(S.tone_sweep(90, 35, .35), .002, .3) * 1.3, S.env(lowpass(S.N(.3, s), 900), .002, .25) * .9,
                 S.at(S.env(lowpass(S.N(.2, s + 1), 3000), .005, .15) * .3, .03))
    return S.norm(x, .8)


def bow_draw(v):
    s = 1500 + v
    creak = S.env(biquad(S.N(.28, s), 'bp', 900 + v * 80, 6), .08, .1)
    return S.norm(S.mixall(creak * .7, S.env(S.tone_sweep(220, 300, .28), .1, .08) * .08), .35)


def bow_release(v):
    s = 1600 + v
    twang = S.env(S.tone_sweep(180 + v * 15, 120, .25), .001, .22)
    return S.norm(S.mixall(twang * .6, S.whoosh(.12, 2200, 1500, s, 2, .2) * .6, S.env(biquad(S.N(.04, s), 'hp', 3000), .001, .02) * .4), .6)


def crossbow_load(v):
    s = 1700 + v
    clicks = S.msum(S.at(S.env(biquad(S.N(.02, s + k), 'bp', 2500, 3), .001, .015), k * .07) for k in range(3))
    return S.norm(S.mixall(clicks, S.env(biquad(S.N(.2, s), 'bp', 700, 4), .05, .05) * .4), .45)


def crossbow_shot(v):
    s = 1800 + v
    thunk = S.env(S.tone_sweep(140, 70, .12), .001, .1)
    return S.norm(S.mixall(thunk * .9, S.env(biquad(S.N(.05, s), 'bp', 2000, 2), .001, .03) * .8, S.whoosh(.1, 2600, 1800, s, 2, .2) * .5), .7)


def magic_charge(v):
    s = 1900 + v
    t = np.arange(int(.6 * S.SR)) / S.SR
    f = 300 + 500 * t / t[-1]
    x = np.sin(2 * np.pi * np.cumsum(f) / S.SR) * .3 + np.sin(4 * np.pi * np.cumsum(f) / S.SR) * .12
    x = x * np.minimum(1, t / .4) * np.minimum(1, (t[-1] - t) / .1)
    return S.norm(S.mixall(x, S.env(biquad(S.N(.6, s), 'bp', 3000 + v * 300, 3), .3, .1) * .2), .45)


def magic_bolt(v):
    s = 2000 + v
    zap = S.env(S.tone_sweep(1400 + v * 100, 500, .22), .002, .2)
    return S.norm(S.mixall(zap * .5, S.env(biquad(S.N(.2, s), 'bp', 4000, 2), .002, .15) * .4, S.metal([2640, 3960], [.15, .1], .2, s) * .2), .55)


def magic_burst(v):
    s = 2100 + v
    boom = S.env(S.tone_sweep(400, 90, .5), .005, .45)
    return S.norm(S.mixall(boom * .6, S.env(lowpass(S.N(.5, s), 4000), .01, .4) * .5, S.metal([1320, 1760, 2640], [.4, .3, .2], .5, s) * .25), .75)


def build():
    made = 0
    def w(name, x):
        nonlocal made
        write_wav(os.path.join(ROOT, f'sfx_{name}.wav'), x); made += 1
    for v in range(3):
        for k in ('light', 'blade', 'heavy', 'staff', 'legend'):
            w(f'wpn_swing_{k}_{v + 1}', swing(k, v))
        w(f'wpn_thrust_{v + 1}', swing('thrust', v))
        w(f'wpn_whiff_{v + 1}', whiff(v))
        w(f'hammer_slam_{v + 1}', hammer_slam(v))
        w(f'bow_draw_{v + 1}', bow_draw(v))
        w(f'bow_release_{v + 1}', bow_release(v))
        w(f'crossbow_load_{v + 1}', crossbow_load(v))
        w(f'crossbow_shot_{v + 1}', crossbow_shot(v))
        w(f'magic_bolt_{v + 1}', magic_bolt(v))
    for v in range(2):
        w(f'magic_charge_{v + 1}', magic_charge(v))
        w(f'magic_burst_{v + 1}', magic_burst(v))
    return made


if __name__ == '__main__':
    print(build(), 'weapon sounds')
