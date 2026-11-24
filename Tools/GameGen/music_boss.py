"""Boss battle loop + boss sound effects (same tiny synth as sfx.py).

  python music_boss.py -> Assets/Game/Audio/music_boss_loop.wav, sfx_boss_phase.wav, sfx_quake.wav, sfx_wave.wav,
                          sfx_boss_win.wav, sfx_summon.wav, sfx_ice.wav
"""
import os
from sfx import SR, tone, noise, write

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Game', 'Audio'))
N = {'D2': 73.4, 'F2': 87.3, 'G2': 98, 'A2': 110, 'Bb2': 116.5, 'C3': 130.8, 'D3': 146.8, 'E3': 164.8, 'F3': 174.6,
     'G3': 196, 'A3': 220, 'Bb3': 233.1, 'C4': 261.6, 'Cs4': 277.2, 'D4': 293.7, 'E4': 329.6, 'F4': 349.2, 'G4': 392,
     'A4': 440, 'Bb4': 466.2, 'C5': 523.3, 'D5': 587.3, 'E5': 659.3, 'F5': 698.5}


def put(out, t, at):
    for k, s in enumerate(t):
        if at + k < len(out): out[at + k] += s


def music():
    """D minor, 150 bpm: driving octave bass, harmonic-minor lead, kick/snare/hats. 8 bars x 2."""
    bpm = 150; beat = 60 / bpm; e = beat / 2; L = int(SR * e)
    bass = ("D2 D3 D2 D3 D2 D3 C3 D3 Bb2 Bb3 Bb2 Bb3 A2 A3 A2 Cs4 "
            "D2 D3 D2 D3 F2 F3 G2 G3 Bb2 Bb3 A2 A3 A2 A3 Cs4 A3").split()
    lead = ("D4 . F4 . A4 . . G4 F4 . E4 . F4 . D4 . "
            "Bb4 . A4 . G4 . F4 . E4 . . . Cs4 . E4 . "
            "D5 . C5 . Bb4 . A4 . G4 . A4 . Bb4 . C5 . "
            "D5 . . . Cs4 . E4 . A4 . . . . . . .").split()
    steps = len(lead)
    out = [0.0] * (L * steps * 2)
    for rep in range(2):
        base = rep * steps * L
        for i, n in enumerate(bass * 2):
            if i >= steps: break
            put(out, tone(N[n], N[n], e * .9, .13, .5), base + i * L)
        for i, n in enumerate(lead):
            if n == '.': continue
            ln = 1
            while i + ln < steps and lead[i + ln] == '.' and ln < 4: ln += 1
            put(out, tone(N[n], N[n] * (0.99 if ln > 2 else 1), e * ln * .92, .085 if rep == 0 else .1, .25), base + i * L)
            if rep == 1: put(out, tone(N[n] / 2, N[n] / 2, e * ln * .9, .05, wav='tri'), base + i * L)
        for i in range(steps):
            if i % 4 == 0: put(out, tone(120, 40, .12, .35, wav='sin'), base + i * L)            # kick
            if i % 8 == 4: put(out, noise(.12, .22, .8, .35), base + i * L)                     # snare
            if i % 2 == 1: put(out, noise(.03, .05, .95, .3), base + i * L)                     # hat
    return out


def build():
    write(os.path.join(ROOT, 'music_boss_loop.wav'), music())
    write(os.path.join(ROOT, 'sfx_boss_phase.wav'), [a + b for a, b in zip(tone(60, 180, 1.0, .35, wav='sq', duty=.3), noise(1.0, .25, .2, .9))])
    write(os.path.join(ROOT, 'sfx_quake.wav'), [a + b for a, b in zip(noise(.7, .45, .08, .7), tone(55, 30, .7, .3, wav='sin'))])
    write(os.path.join(ROOT, 'sfx_wave.wav'), [a + b for a, b in zip(noise(.45, .25, .5, .6), tone(300, 80, .45, .12, wav='tri'))])
    write(os.path.join(ROOT, 'sfx_summon.wav'), tone(200, 800, .5, .18, wav='tri') + tone(800, 400, .3, .1, wav='tri'))
    write(os.path.join(ROOT, 'sfx_ice.wav'), [a + b for a, b in zip(tone(1800, 2400, .25, .1, wav='sq', duty=.2), noise(.25, .15, .95, .3))])
    fan = []
    for f, d in ((392, .14), (523.3, .14), (659.3, .14), (784, .5), (659.3, .14), (784, .8)):
        fan += tone(f, f, d, .2, .25)
    write(os.path.join(ROOT, 'sfx_boss_win.wav'), fan)


if __name__ == '__main__':
    build()
    print('ok')
