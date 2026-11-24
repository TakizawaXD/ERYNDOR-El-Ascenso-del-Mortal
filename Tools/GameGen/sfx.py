"""Tiny 8-bit sound effects + a looping forest tune (square/noise synthesis, 22 kHz mono WAV)."""
import math, os, random, struct, sys, wave

SR = 22050


def write(path, samples):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, s)) * 30000)) for s in samples))


def env(i, n, a=0.01, r=0.6):
    t = i / n
    at = min(1, (i / SR) / a) if a else 1
    return at * (1 - t) ** (1 / max(r, 0.05))


def square(f, t, duty=.5):
    return 1.0 if (f * t) % 1 < duty else -1.0


def tone(f0, f1, dur, vol=.35, duty=.5, wav='sq'):
    n = int(SR * dur); out = []
    ph = 0
    for i in range(n):
        f = f0 + (f1 - f0) * i / n
        ph += f / SR
        if wav == 'sq':
            v = 1.0 if ph % 1 < duty else -1.0
        elif wav == 'tri':
            v = 4 * abs(ph % 1 - .5) - 1
        else:
            v = math.sin(2 * math.pi * ph)
        out.append(v * vol * env(i, n))
    return out


def noise(dur, vol=.35, lp=.5, decay=.6):
    n = int(SR * dur); out = []; last = 0
    rnd = random.Random(7)
    for i in range(n):
        last = last + lp * (rnd.uniform(-1, 1) - last)
        out.append(last * vol * env(i, n, 0.002, decay))
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


def seq(*parts):
    out = []
    for p in parts:
        out += p
    return out


def music():
    """16-bar loop, A minor, square lead + triangle bass + noise hats"""
    bpm = 112; beat = 60 / bpm; eighth = beat / 2
    notes = {'A3': 220, 'C4': 261.6, 'D4': 293.7, 'E4': 329.6, 'G4': 392, 'A4': 440, 'B4': 493.9, 'C5': 523.3, 'D5': 587.3, 'E5': 659.3, 'G3': 196, 'F3': 174.6, 'E3': 164.8}
    lead = ("A4 . C5 . E5 D5 C5 . B4 . G4 . A4 . . . "
            "A4 . C5 . E5 G4 A4 . D5 . C5 B4 A4 . . . "
            "C5 . E5 . D5 C5 B4 . A4 . G4 . E4 . . . "
            "A4 . B4 C5 D5 . E5 . D5 C5 B4 . A4 . . .").split()
    bass = "A3 A3 F3 F3 C4 C4 G3 G3 A3 A3 F3 F3 E3 E3 E3 E3".split()
    L = int(SR * eighth)
    out = [0.0] * (L * len(lead) * 2)
    for rep in range(2):
        for i, n in enumerate(lead):
            if n == '.':
                continue
            dur = eighth * (2 if i + 1 < len(lead) and lead[i + 1] == '.' else 1)
            t = tone(notes[n], notes[n], dur * .95, .12, .25)
            o = (rep * len(lead) + i) * L
            for k, s in enumerate(t):
                if o + k < len(out): out[o + k] += s
        for i, n in enumerate(bass):
            t = tone(notes[n] / 2, notes[n] / 2, beat * 1.9, .16, wav='tri')
            o = rep * len(lead) * L + i * 4 * L
            for k, s in enumerate(t):
                if o + k < len(out): out[o + k] += s
        for i in range(len(lead)):
            if i % 2 == 1:
                h = noise(.03, .05, .9, .3)
                o = (rep * len(lead) + i) * L
                for k, s in enumerate(h):
                    if o + k < len(out): out[o + k] += s
    return out


def build(root):
    fx = {
        'swing': noise(.12, .3, .35, .4),
        'heavy_swing': mix(noise(.22, .35, .25, .5), tone(180, 90, .2, .15)),
        'hit': mix(noise(.08, .5, .8, .3), tone(220, 110, .08, .25)),
        'player_hurt': seq(tone(440, 220, .08, .3), tone(330, 160, .12, .3)),
        'enemy_hurt': tone(300, 150, .1, .3, .25),
        'enemy_die': seq(tone(400, 300, .06, .3), tone(300, 120, .2, .3), noise(.15, .2, .3, .5)),
        'player_die': seq(tone(440, 400, .12, .3), tone(330, 300, .12, .3), tone(220, 110, .4, .3)),
        'coin': seq(tone(988, 988, .05, .25, .25), tone(1319, 1319, .14, .25, .25)),
        'potion': seq(tone(523, 523, .07, .25), tone(659, 659, .07, .25), tone(784, 784, .07, .25), tone(1047, 1047, .14, .25)),
        'chest': seq(noise(.06, .3, .4, .3), tone(392, 392, .08, .25), tone(523, 523, .08, .25), tone(784, 784, .2, .25)),
        'arrow': mix(noise(.1, .2, .9, .3), tone(900, 500, .1, .1, .125)),
        'fireball': mix(noise(.35, .35, .15, .6), tone(150, 60, .35, .15)),
        'spit': mix(noise(.12, .3, .5, .4), tone(200, 400, .12, .15, .25)),
        'roll': noise(.18, .25, .2, .5),
        'break': mix(noise(.18, .4, .6, .4), tone(160, 80, .1, .2)),
        'select': tone(660, 660, .06, .2, .25),
        'confirm': seq(tone(660, 660, .05, .2, .25), tone(990, 990, .1, .2, .25)),
        'step': noise(.03, .08, .3, .3),
        'boss_roar': mix(noise(.8, .4, .12, .8), tone(110, 55, .8, .25)),
        'victory': seq(*[tone(f, f, d, .25) for f, d in [(523, .12), (659, .12), (784, .12), (1047, .3), (784, .12), (1047, .5)]]),
        'gameover': seq(*[tone(f, f, d, .25, wav='tri') for f, d in [(392, .25), (330, .25), (262, .25), (196, .6)]]),
        'block': mix(tone(1200, 900, .07, .2, .125), noise(.05, .2, .9, .3)),
        'levelup': seq(*[tone(f, f, .07, .2, .25) for f in (523, 659, 784, 1047, 1319)]),
    }
    for k, v in fx.items():
        write(os.path.join(root, f'sfx_{k}.wav'), v)
    write(os.path.join(root, 'music_forest_loop.wav'), music())
    return len(fx) + 1


if __name__ == '__main__':
    print(build(sys.argv[1]))
    import sfx2   # the second-generation effects replace these ones (variants, voices, surfaces)
    print(sfx2.build(sys.argv[1]), 'effects (sfx2)')
