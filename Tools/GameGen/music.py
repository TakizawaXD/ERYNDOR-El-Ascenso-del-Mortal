"""Original soundtrack of La Espada del Bosque, composed in code (chord progressions + motif-based melodies + arrangement).

  python Tools/GameGen/music.py            -> Assets/Game/Audio/Music/*.wav  (every piece)
  python Tools/GameGen/music.py menu boss_B -> only those pieces
  python Tools/GameGen/music.py --samples  -> also copies a listening set to Documentation/Audio/

Every looping piece is rendered so its reverb tail wraps onto its start (no click at the loop point). Pieces with a night
layer render a second file of the very same length and harmony (music_<id>_night.wav) that the game crossfades in sync.
Pieces with an intro render music_<id>_intro.wav, played once before the loop.
The main theme (leitmotif) of the game appears in the title screen, the Central Valley, the camp and the victory jingle.
"""
import os, shutil, sys
sys.path.insert(0, os.path.dirname(__file__))
from synth import Song, write_wav, SR          # noqa: E402
from theory import Key, voice, MelodyWriter, nearest   # noqa: E402
import random                                   # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'Assets', 'Game', 'Audio', 'Music')
SAMPLES = os.path.join(ROOT, 'Documentation', 'Audio')

# ---------------------------------------------------------------- the leitmotif (scale degrees, beats) - 8 bars of 4/4
THEME = [
    [(5, 1.5), (6, .5), (5, 1), (3, 1)],
    [(2, 1.5), (3, .5), (5, 2)],
    [(6, 1.5), (8, .5), (7, 1), (6, 1)],
    [(5, 3), (3, 1)],
    [(5, 1.5), (6, .5), (5, 1), (3, 1)],
    [(2, 1), (3, 1), (1, 1), (-1, 1)],      # -1 = the 6th below the tonic
    [(2, 1.5), (3, .5), (4, 1), (3, .5), (2, .5)],
    [(1, 4)],
]
THEME_CHORDS = ['1', '5', '4', '1', '1', '6', '2 5', '1']


def theme_notes(key, octave, bars=THEME, meter=4):
    out = []
    for b, bar in enumerate(bars):
        beat = 0.0
        for deg, d in bar:
            if deg is None: beat += d; continue
            dd = deg if deg > 0 else deg + 7 - 7   # -1 -> degree 6 one octave down
            m = key.degree_midi(6, octave - 1) if deg == -1 else key.degree_midi(dd, octave)
            out.append((b, beat, d, m))
            beat += d
    return out


# ---------------------------------------------------------------- accompaniment patterns
def drum_patterns(style, meter):
    """per bar: {drum: pattern string}; steps: 16ths for 3/4 and 4/4, 16ths of the eighth-beat for 6/8 (2 per beat)"""
    P = {
        (4, 'folk'): {'kick': 'x.......x.......', 'shaker': '..o...o...o...o.', 'snare': '........o.......'},
        (4, 'soft'): {'shaker': 'o.g.o.g.o.g.o.g.', 'kick': 'o...............'},
        (4, 'night'): {'shaker': '........o.......'},
        (4, 'march'): {'kick': 'x.......x.......', 'snare': '....x..g....x.gg', 'hat': 'o.o.o.o.o.o.o.o.'},
        (4, 'drive'): {'kick': 'x.....x.x.......', 'snare': '....x.......x...', 'hat': 'x.o.x.o.x.o.x.o.'},
        (4, 'battle'): {'kick': 'x..x..x.x..x..x.', 'snare': '....x.......x..g', 'hat': 'xoxoxoxoxoxoxoxo', 'tom_lo': '..............o.'},
        (4, 'boss'): {'kick': 'x.x...x.x.x...x.', 'snare': '....x.......x.x.', 'hat': 'x.x.x.x.x.x.x.x.', 'timpani': 'x...............'},
        (4, 'tribal'): {'tom_lo': 'x..x..x...x..x..', 'tom_hi': '....o.....o...oo', 'kick': 'x.......x.......', 'clap': '....x.......x...'},
        (4, 'tabla'): {'tabla_lo': 'x.....x...x.....', 'tabla_hi': '..o.o...o.o.o..o', 'shaker': 'g.g.g.g.g.g.g.g.'},
        (4, 'swamp'): {'brush': 'o..go..go..go..g', 'kick': 'x.....x.........', 'rim': '....o.......o...'},
        (4, 'heart'): {'heart': 'x...............'},
        (4, 'forge'): {'anvil': 'x.....o.....x...', 'kick': 'x.......x.......', 'rim': '....o.......o..o'},
        (4, 'chorale'): {},
        (4, 'none'): {},
        (3, 'waltz'): {'kick': 'x...........', 'shaker': '....o...o...'},
        (3, 'soft'): {'shaker': '....g...g...'},
        (3, 'night'): {},
        (3, 'snow'): {'shaker': 'o.g.o.g.o.g.', 'kick': 'o...........'},
        (3, 'none'): {},
        (6, 'jig'): {'kick': 'x.....x.....', 'tamb': '..o.o...o.o.', 'snare': '......o.....'},
        (6, 'tavern'): {'kick': 'x.....x.....', 'tamb': 'o.o.o.o.o.o.', 'mug': '......x.....'},
        (6, 'sea'): {'kick': 'x.....o.....', 'shaker': '..o.o...o.o.', 'tamb': '......o.....'},
        (6, 'forest'): {'shaker': 'o.g.g.o.g.g.', 'kick': 'o.....o.....'},
        (6, 'macabre'): {'timpani': 'x...........', 'snare': '......o...o.', 'hat': 'o.o.o.o.o.o.'},
        (6, 'night'): {},
        (6, 'none'): {},
    }
    return P.get((meter, style), {})


def steps_per_beat(meter):
    return 2 if meter == 6 else 4


def parse_bar(s):
    return s.split()


# ---------------------------------------------------------------- generic arranger
class Piece:
    def __init__(self, pid, tonic, mode, bpm, meter, sections, order, day, night=None, lead=(67, 84), seed=0,
                 theme=None, rev=(1.0, 0.22), swing=0.0, intro=None, fast=False, tonic_end='AB', extra=None):
        self.id = pid; self.key = Key(tonic, mode); self.bpm = bpm; self.meter = meter
        self.sections = sections; self.order = order.split(); self.day = day; self.night = night
        self.lead = lead; self.seed = seed or sum(map(ord, pid)); self.theme = theme
        self.rev = rev; self.swing = swing; self.intro = intro; self.fast = fast; self.tonic_end = tonic_end
        self.extra = extra
        self._melodies = {}

    # ------------------------------------------------ helpers
    def bar_beats(self):
        return self.meter

    def chord_list(self, sec):
        """[(bar, beat, dur, pcs)] for section sec (letter)"""
        out = []
        for b, s in enumerate(self.sections[sec]):
            parts = parse_bar(s)
            d = self.meter / len(parts)
            for k, sym in enumerate(parts):
                out.append((b, k * d, d, self.key.chord(sym)))
        return out

    def bar_pcs(self, sec):
        """chord tones per bar (union of the bar's chords, first chord first)"""
        res = []
        for s in self.sections[sec]:
            pcs = []
            for sym in parse_bar(s):
                for p in self.key.chord(sym):
                    if p not in pcs: pcs.append(p)
            res.append(pcs)
        return res

    def melody(self, letter):
        if letter in self._melodies: return self._melodies[letter]
        if letter == 'A' and self.theme is not None:
            mel = theme_notes(self.key, self.theme)
        else:
            w = MelodyWriter(self.key, self.meter, self.lead[0], self.lead[1], self.seed * 7 + ord(letter), self.fast)
            mel = w.phrase(self.bar_pcs(letter), tonic_end=letter in self.tonic_end)
        self._melodies[letter] = mel
        return mel

    # ------------------------------------------------ render
    def build(self, night=False):
        arr = self.night if night else self.day
        bars_total = sum(len(self.sections[s[0]]) for s in self.order)
        song = Song(self.bpm, bars_total * self.meter, True, self.rev[0], self.rev[1] * (1.25 if night else 1), 0.75, self.swing)
        song.bus('lead', arr.get('lead_gain', 1.0), arr.get('lead_rev', 0.3), arr.get('lead_echo', 0.18))
        song.bus('counter', 0.8, 0.35, 0.1)
        song.bus('harm', arr.get('harm_gain', 0.55), 0.35)
        song.bus('pad', arr.get('pad_gain', 0.4), 0.5)
        song.bus('bass', arr.get('bass_gain', 0.8), 0.08)
        song.bus('drums', arr.get('drum_gain', 0.6), 0.12)
        rng = random.Random(self.seed + (99 if night else 0))
        bar0 = 0
        prev = None
        for token in self.order:
            letter = token[0]; variant = token[1:]
            chords = self.chord_list(letter)
            nb = len(self.sections[letter])
            b0 = bar0 * self.meter
            # pad / harmony
            for (b, bt, d, pcs) in chords:
                v = voice(pcs, prev, arr.get('pad_center', 60)); prev = v
                at = b0 + b * self.meter + bt
                if arr.get('pad'):
                    for m in v: song.note('pad', arr['pad'], at, d * 0.98, m, 0.5)
                self.arp(song, arr, at, d, v, pcs, rng)
                self.bass(song, arr, at, d, pcs, b, bt, chords)
            # melody
            mel = self.melody(letter)
            lead_inst = arr.get('lead2') if (variant == '2' and arr.get('lead2')) else arr.get('lead')
            octv = arr.get('lead_oct', 0) + (arr.get('lead2_oct', 0) if variant == '2' else 0)
            if lead_inst and not (variant == 'x'):
                for (b, bt, d, m) in mel:
                    at = b0 + b * self.meter + bt + rng.uniform(-0.008, 0.008)
                    vel = arr.get('lead_vel', 0.7) * (1.0 if bt == 0 else 0.9) * rng.uniform(0.92, 1.05)
                    song.note('lead', lead_inst, at, d * arr.get('legato', 0.92), m + 12 * octv, vel)
                if variant == '2' and arr.get('counter'):
                    scale = self.key.scale_midis(40, 100)
                    for (b, bt, d, m) in mel:
                        if d < 1 and self.meter != 6: continue
                        idx = scale.index(nearest(scale, m))
                        cm = scale[max(0, idx - (2 if rng.random() < 0.7 else 5))] + 12 * arr.get('counter_oct', 0)
                        song.note('counter', arr['counter'], b0 + b * self.meter + bt, d * 0.95, cm, arr.get('counter_vel', 0.45))
            # drums
            style = arr.get('drums', 'none')
            if variant == 'x' and arr.get('drums_x'): style = arr['drums_x']
            pat = drum_patterns(style, self.meter)
            spb = steps_per_beat(self.meter)
            for b in range(nb):
                fill = (b == nb - 1) and arr.get('fills', False)
                for name, p in pat.items():
                    for i, ch in enumerate(p):
                        if ch == '.': continue
                        vel = {'x': 0.9, 'o': 0.6, 'g': 0.3}[ch] * rng.uniform(0.9, 1.05)
                        song.hit('drums', name, b0 + b * self.meter + i / spb, vel * arr.get('drum_vel', 1.0), rng.randrange(4))
                if fill:
                    for i in range(4):
                        song.hit('drums', 'snare' if self.meter != 6 else 'tom_hi', b0 + b * self.meter + self.meter - 1 + i * 0.25, 0.35 + 0.12 * i, i)
            if self.extra: self.extra(self, song, night, b0, letter, variant, nb, rng)
            bar0 += nb
        return song.render(arr.get('rms', 0.15 if not night else 0.11))

    def arp(self, song, arr, at, d, v, pcs, rng):
        a = arr.get('arp')
        if not a: return
        inst, style = a
        vel = arr.get('arp_vel', 0.45)
        notes = v + [v[0] + 12]
        if style in ('up8', 'up16', 'updown8', 'slow'):
            step = {'up8': 0.5, 'up16': 0.25, 'updown8': 0.5, 'slow': 1.0}[style]
            if self.meter == 6: step = 1.0
            seq = [0, 1, 2, 3] if style != 'updown8' else [0, 1, 2, 3, 2, 1]
            k = 0; t = 0.0
            while t < d - 1e-6:
                m = notes[seq[k % len(seq)]] + 12 * arr.get('arp_oct', 0)
                song.note('harm', inst, at + t, step * 1.6, m, vel * (1 if k % len(seq) == 0 else 0.8))
                k += 1; t += step
        elif style == 'broken':      # finger-picked: low root, then the upper voices
            pat = [0, 2, 1, 2, 3, 2, 1, 2] if self.meter != 3 else [0, 2, 1, 3, 1, 2]
            step = 0.5 if self.meter != 6 else 1.0
            t = 0.0; k = 0
            low = (v[0] - 12)
            while t < d - 1e-6:
                idx = pat[k % len(pat)]
                m = low if idx == 0 else notes[idx] + 12 * arr.get('arp_oct', 0)
                song.note('harm', inst, at + t, step * 2.5, m, vel * (1.05 if idx == 0 else 0.75))
                t += step; k += 1
        elif style == 'waltz':       # 3/4: chord on beats 2 and 3
            for bt in (1, 2):
                if bt < d:
                    for m in v: song.note('harm', inst, at + bt, 0.8, m + 12 * arr.get('arp_oct', 0), vel * 0.6)
        elif style == 'jig':         # 6/8 broken eighths
            t = 0.0; k = 0
            seq = [0, 1, 2, 3, 2, 1]
            while t < d - 1e-6:
                song.note('harm', inst, at + t, 1.4, notes[seq[k % 6]] + 12 * arr.get('arp_oct', 0), vel * (1 if k % 3 == 0 else 0.75))
                t += 1; k += 1
        elif style == 'stabs':       # off-beat chord stabs
            for bt in [x * 0.5 for x in range(int(d * 2)) if x % 2 == 1]:
                for m in v: song.note('harm', inst, at + bt, 0.3, m + 12 * arr.get('arp_oct', 0), vel * 0.7)
        elif style == 'block':
            for m in v: song.note('harm', inst, at, d * 0.95, m + 12 * arr.get('arp_oct', 0), vel)
        elif style == 'gliss':       # harp sweep on each chord
            for i in range(8):
                m = notes[i % 4] + 12 * (i // 4) + 12 * arr.get('arp_oct', 0)
                song.note('harm', inst, at + i * 0.125, 2.0, m, vel * (0.6 + 0.05 * i))

    def bass(self, song, arr, at, d, pcs, b, bt, chords):
        bdef = arr.get('bass')
        if not bdef: return
        inst, style = bdef
        lo = arr.get('bass_lo', 36)
        root = lo + ((pcs[0] - lo) % 12)
        fifth = root + 7 if root + 7 <= lo + 14 else root - 5
        vel = arr.get('bass_vel', 0.7)
        n = song.note
        if style == 'root':
            n('bass', inst, at, d * 0.95, root, vel)
        elif style == 'root5':
            if d >= 2:
                n('bass', inst, at, d / 2 * 0.9, root, vel); n('bass', inst, at + d / 2, d / 2 * 0.9, fifth, vel * 0.85)
            else:
                n('bass', inst, at, d * 0.9, root, vel)
        elif style in ('pump8', 'octave8'):
            t = 0.0; k = 0
            while t < d - 1e-6:
                m = root + (12 if style == 'octave8' and k % 2 else 0)
                n('bass', inst, at + t, 0.42, m, vel * (1 if k % 2 == 0 else 0.8))
                t += 0.5; k += 1
        elif style == 'gallop':
            t = 0.0
            while t < d - 1e-6:
                n('bass', inst, at + t, 0.4, root, vel); n('bass', inst, at + t + 0.5, 0.2, root, vel * 0.7); n('bass', inst, at + t + 0.75, 0.2, root + 12, vel * 0.7)
                t += 1
        elif style == 'walk':
            third = root + (pcs[1] - pcs[0]) % 12
            seq = [root, third, fifth, root + 12 if fifth < root else fifth + 2]
            for i in range(int(d)):
                n('bass', inst, at + i, 0.9, seq[i % 4], vel * (1 if i == 0 else 0.8))
        elif style == 'waltz':
            n('bass', inst, at, 0.9, root, vel)
            if d >= 3: pass
        elif style == 'jig':
            n('bass', inst, at, 2.6, root, vel)
            if d >= 6: n('bass', inst, at + 3, 2.6, fifth, vel * 0.85)
        elif style == 'pedal':
            n('bass', inst, at, d * 0.98, lo + ((self.key.tonic - lo) % 12), vel)
        elif style == 'march':
            n('bass', inst, at, 0.9, root, vel)
            if d >= 2: n('bass', inst, at + 2, 0.9, fifth, vel * 0.85)
            if d >= 4: n('bass', inst, at + 3.5, 0.4, fifth, vel * 0.6)

    # ------------------------------------------------ intro: chord swell into the loop
    def build_intro(self):
        if not self.intro: return None
        bars, style = self.intro
        arr = self.day
        song = Song(self.bpm, bars * self.meter, False, self.rev[0], self.rev[1])
        song.bus('pad', 0.5, 0.5); song.bus('harm', 0.55, 0.4); song.bus('drums', 0.7, 0.2); song.bus('lead', 0.9, 0.3)
        first = self.chord_list(self.order[0][0])[0][3]
        v = voice(first, None, 60)
        L = bars * self.meter
        if style == 'swell':
            for m in v: song.note('pad', arr.get('pad') or 'strings', 0, L, m, 0.55)
            for i in range(int(L * 2)):
                m = (v + [v[0] + 12])[i % 4] + 12 * (i // 8 % 2)
                song.note('harm', arr.get('arp', ('harp', ''))[0], i * 0.5, 2, m, 0.3 + 0.4 * i / (L * 2))
        elif style == 'boss':
            for m in v: song.note('pad', 'choir', 0, L, m, 0.45); song.note('pad', 'strings_dark', 0, L, m - 12, 0.5)
            for i in range(int(L)): song.hit('drums', 'roll', i, 0.4 + 0.5 * i / L, i)
            song.hit('drums', 'timpani', 0, 1.0); song.hit('drums', 'crash', 0, 0.7)
            for i in range(4): song.hit('drums', 'tom_lo', L - 1 + i * 0.25, 0.5 + 0.12 * i, i)
            song.note('lead', arr.get('lead', 'brass'), 0, L * 0.9, v[0] - 12, 0.5)
        elif style == 'fanfare':
            for k, bt in enumerate([0, 0.5, 0.75, 1, 2]):
                for m in v: song.note('harm', 'brass', bt, 0.4 if k < 4 else 1.8, m, 0.55)
            song.hit('drums', 'timpani', 0, 0.8); song.hit('drums', 'roll', 2, 0.6); song.hit('drums', 'roll', 3, 0.8)
        x = song.render(0.13)
        n = int(round(L * 60 / self.bpm * SR))
        if len(x) < n:
            import numpy as np
            x = np.concatenate([x, np.zeros(n - len(x))])
        return x[:n]


# ---------------------------------------------------------------- extra layers for particular pieces
def forge_extra(p, song, night, b0, letter, variant, nb, rng):
    # hammer blows and bellows breathing every few bars
    for b in range(nb):
        if b % 2 == 1:
            song.hit('drums', 'anvil', b0 + b * 4 + 3.5, 0.35, b)


def corrupt_extra(p, song, night, b0, letter, variant, nb, rng):
    # a wrong-sounding bell a tritone away, now and then
    for b in range(0, nb, 4):
        m = p.key.degree_midi(1, 5) + 6
        song.note('counter', 'bell', b0 + b * p.meter + 2.5, 2, m, 0.25)


def boss_extra(p, song, night, b0, letter, variant, nb, rng):
    for b in range(nb):
        if b % 4 == 3: song.hit('drums', 'crash', b0 + (b + 1) * p.meter - 0.01, 0.35, b)


def tavern_extra(p, song, night, b0, letter, variant, nb, rng):
    for b in range(nb):
        if rng.random() < 0.3: song.hit('drums', 'mug', b0 + b * p.meter + rng.choice([2, 5]), 0.4, b)


# ---------------------------------------------------------------- the soundtrack
def V(**k):
    return k


DAY_NIGHT_NIGHT = dict(drums='night', bass_gain=0.6)

PIECES = [
    # ---------------- menus
    Piece('menu', 'D', 'major', 72, 4,
          {'A': THEME_CHORDS, 'B': ['6', '4', '1', '5', '6', '4', '2', '5s 5']},
          'A B A2', V(lead='flute', lead2='strings', lead2_oct=0, counter='harp', counter_oct=0, arp=('harp', 'broken'), arp_vel=0.4,
                       bass=('bass_sine', 'root'), pad='pad', pad_gain=0.3, drums='night', lead_vel=0.6, rms=0.13),
          theme=4, lead=(66, 81), rev=(1.3, 0.3), intro=(2, 'swell')),
    Piece('classselect', 'Bb', 'major', 100, 4,
          {'A': ['1', '4', '1', '5', '6', '4', '5', '1'], 'B': ['4', '5', '3', '6', '2', '5', '1', '1']},
          'A B', V(lead='horn', lead2='brass', arp=('harp', 'up8'), arp_vel=0.35, bass=('bass_pluck', 'march'), pad='strings',
                    drums='march', drum_vel=0.7, fills=True), lead=(65, 82)),

    # ---------------- overworld regions (day + night layer, same length)
    Piece('region_a', 'D', 'major', 104, 4,       # Valle Central: the main theme of the world
          {'A': THEME_CHORDS, 'B': ['4', '5', '3', '6', '4', '1', '2', '5']},
          'A B A2', V(lead='pulse25', lead2='warm', counter='flute', arp=('lute', 'up8'), bass=('bass_tri', 'root5'),
                       pad='pad', pad_gain=0.25, drums='folk', fills=True),
          night=V(lead='flute', lead2='bell', counter='harp', arp=('harp', 'slow'), arp_vel=0.35, bass=('bass_sine', 'root'),
                  pad='pad', pad_gain=0.35, drums='night', lead_vel=0.55), theme=5, lead=(69, 86)),
    Piece('region_b', 'E', 'dorian', 210, 6,      # Bosque del Oeste: 6/8, flute and lute
          {'A': ['1', '4', '1', '4', '3', '7', '4', '4'], 'B': ['3', '7', '1', '4', '3', '7', '4', '5']},
          'A B A2', V(lead='flute', lead2='whistle', counter='lute', arp=('lute', 'jig'), bass=('bass_pluck', 'jig'),
                       pad='pad', pad_gain=0.2, drums='forest'),
          night=V(lead='bell', lead2='flute', counter='harp', arp=('harp', 'jig'), arp_vel=0.3, bass=('bass_sine', 'jig'),
                  pad='pad', pad_gain=0.35, drums='night', lead_vel=0.5), lead=(64, 83)),
    Piece('region_c', 'F', 'lydian', 76, 4,       # Lago Espejo: shimmering lydian
          {'A': ['1', '2', '6', '5', '1', '2', '3', '2'], 'B': ['6', '3', '2', '1', '6', '5', '2', '2']},
          'A B A2', V(lead='celesta', lead2='flute', counter='harp', arp=('harp', 'up16'), arp_vel=0.3, bass=('bass_sine', 'root'),
                       pad='pad', pad_gain=0.4, drums='soft', drum_vel=0.6),
          night=V(lead='bell', lead2='celesta', counter='pad', arp=('harp', 'up8'), arp_vel=0.25, bass=('bass_sine', 'root'),
                  pad='pad', pad_gain=0.45, drums='night', lead_vel=0.45), lead=(67, 88), rev=(1.5, 0.32)),
    Piece('region_d', 'C', 'phrygian', 88, 4,     # Pantano Carmesí: swampy swing
          {'A': ['1', '2', '1', '7', '6', '2', '1', '1'], 'B': ['4', '7', '6', '2', '4', '5M', '1', '5M']},
          'A B A2', V(lead='clarinet', lead2='warm_dark', counter='bass_pluck', counter_oct=-1, arp=('lute', 'stabs'), arp_vel=0.3,
                       bass=('bass_pluck', 'walk'), drums='swamp', pad='pad_dark', pad_gain=0.3),
          night=V(lead='warm_dark', lead2='clarinet', counter='pad', arp=('harp', 'slow'), arp_vel=0.25, bass=('bass_sine', 'walk'),
                  drums='night', pad='pad_dark', pad_gain=0.4, lead_vel=0.5), lead=(58, 77), swing=0.33),
    Piece('region_e', 'A', 'minor', 92, 3,        # Picos Nevados: airy waltz
          {'A': ['1', '6', '3', '7', '4', '6', '7', '1'], 'B': ['6', '7', '1', '1', '4', '5', '6', '7']},
          'A B A2', V(lead='glock', lead2='flute', counter='strings', arp=('celesta', 'waltz'), arp_vel=0.35, bass=('bass_sine', 'waltz'),
                       pad='strings', pad_gain=0.35, drums='snow'),
          night=V(lead='celesta', lead2='bell', counter='pad', arp=('harp', 'waltz'), arp_vel=0.25, bass=('bass_sine', 'waltz'),
                  pad='pad', pad_gain=0.45, drums='night', lead_vel=0.45), lead=(69, 88), rev=(1.6, 0.34)),
    Piece('region_f', 'E', 'phrygdom', 112, 4,    # Arenas Rojas: oud and tabla
          {'A': ['1', '2', '1', '2', '7', '2', '1', '1'], 'B': ['4', '7', '2', '1', '4', '2', '2', '1']},
          'A B A2', V(lead='oud', lead2='whistle', counter='oud', arp=('oud', 'stabs'), arp_vel=0.3, bass=('bass_pluck', 'pedal'),
                       pad='pad_saw', pad_gain=0.2, drums='tabla', lead_vel=0.8),
          night=V(lead='flute', lead2='oud', counter='bell', arp=('harp', 'slow'), arp_vel=0.25, bass=('bass_sine', 'pedal'),
                  pad='pad', pad_gain=0.35, drums='night', lead_vel=0.5), lead=(64, 83)),
    Piece('region_g', 'D', 'harmonic', 96, 4,     # Monte Ceniza: heavy, brass and timpani
          {'A': ['1', '6', '1', '5', '1', '6', '4', '5'], 'B': ['4', '5', '1', '6', '4', '6', '5', '5']},
          'A B A2', V(lead='horn', lead2='brass', counter='choir', arp=('strings_dark', 'block'), arp_vel=0.35, bass=('bass_saw', 'octave8'),
                       pad='choir', pad_gain=0.25, drums='tribal', drum_vel=0.7, fills=True),
          night=V(lead='warm_dark', lead2='horn', counter='choir', arp=('strings_dark', 'block'), arp_vel=0.3, bass=('bass_sine', 'root'),
                  pad='pad_dark', pad_gain=0.4, drums='heart', lead_vel=0.5), lead=(57, 76)),
    Piece('region_h', 'B', 'minor', 72, 4,        # Bosque Corrupto: uneasy, borrowed chords, heartbeat
          {'A': ['1', 'b2', '1', '6m', '1', 'b2', '4m', '5M'], 'B': ['6m', 'b2', '4m', '1', '6m', 'b2', '5M', '5M']},
          'A B A2', V(lead='bell', lead2='warm_dark', counter='choir', arp=('harp', 'updown8'), arp_vel=0.25, bass=('bass_sine', 'pedal'),
                       pad='pad_dark', pad_gain=0.45, drums='heart'),
          night=V(lead='choir', lead2='bell', counter='pad_dark', arp=('celesta', 'slow'), arp_vel=0.2, bass=('bass_sine', 'pedal'),
                  pad='pad_dark', pad_gain=0.5, drums='heart', lead_vel=0.45), lead=(62, 81), rev=(1.6, 0.35), extra=corrupt_extra),
    Piece('region_i', 'G', 'mixolydian', 108, 4,  # Ciudadela del Rey (camino real): royal march
          {'A': ['1', '4', '1', '5', '1', '7', '4', '1'], 'B': ['6', '3', '4', '1', '2', '5', '1', '5']},
          'A B A2', V(lead='brass', lead2='horn', counter='strings', arp=('harp', 'up8'), arp_vel=0.3, bass=('bass_pluck', 'march'),
                       pad='strings', pad_gain=0.3, drums='march', fills=True),
          night=V(lead='horn', lead2='flute', counter='harp', arp=('harp', 'slow'), arp_vel=0.25, bass=('bass_sine', 'root'),
                  pad='strings', pad_gain=0.35, drums='night', lead_vel=0.5), lead=(65, 84)),
    Piece('region_j', 'A', 'major', 220, 6,       # Costa del Puerto: sailing 6/8
          {'A': ['1', '4', '1', '5', '1', '4', '5', '1'], 'B': ['6', '2', '5', '1', '4', '1', '2', '5']},
          'A B A2', V(lead='accordion', lead2='whistle', counter='lute', arp=('lute', 'jig'), bass=('bass_pluck', 'jig'),
                       pad='pad', pad_gain=0.2, drums='sea'),
          night=V(lead='flute', lead2='accordion', counter='harp', arp=('harp', 'jig'), arp_vel=0.25, bass=('bass_sine', 'jig'),
                  pad='pad', pad_gain=0.35, drums='night', lead_vel=0.5), lead=(64, 83)),

    # ---------------- towns (peaceful, each its own colour, with night layer)
    Piece('city_valle', 'G', 'major', 108, 3,     # Villa del Valle: pastoral waltz
          {'A': ['1', '4', '1', '5', '1', '6', '2', '5'], 'B': ['4', '1', '4', '5', '3', '6', '2', '5']},
          'A B A2', V(lead='flute', lead2='lute', counter='harp', arp=('lute', 'waltz'), arp_vel=0.4, bass=('bass_pluck', 'waltz'),
                       pad='pad', pad_gain=0.2, drums='waltz', drum_vel=0.6),
          night=V(lead='musicbox', lead2='flute', counter='harp', arp=('harp', 'waltz'), arp_vel=0.25, bass=('bass_sine', 'waltz'),
                  pad='pad', pad_gain=0.35, drums='night', lead_vel=0.45), lead=(67, 86)),
    Piece('city_ciudadela', 'Eb', 'major', 84, 4,  # Ciudadela: stately and calm
          {'A': ['1', '3', '4', '1', '6', '2', '5', '5'], 'B': ['4', '5', '3', '6', '2', '5', '1', '1']},
          'A B A2', V(lead='horn', lead2='strings', counter='flute', arp=('harp', 'broken'), arp_vel=0.35, bass=('bass_sine', 'root5'),
                       pad='organ_soft', pad_gain=0.3, drums='soft', drum_vel=0.5),
          night=V(lead='celesta', lead2='horn', counter='strings', arp=('harp', 'slow'), arp_vel=0.25, bass=('bass_sine', 'root'),
                  pad='organ_soft', pad_gain=0.35, drums='night', lead_vel=0.45), lead=(63, 82), rev=(1.4, 0.3)),
    Piece('city_puerto', 'C', 'major', 230, 6,    # Puerto: bouncy jig
          {'A': ['1', '1', '4', '5', '1', '6', '2', '5'], 'B': ['4', '1', '5', '1', '4', '1', '5', '5']},
          'A B A2', V(lead='accordion', lead2='whistle', counter='guitar', arp=('guitar', 'jig'), arp_vel=0.4, bass=('bass_pluck', 'jig'),
                       drums='jig'),
          night=V(lead='guitar', lead2='accordion', counter='harp', arp=('harp', 'jig'), arp_vel=0.25, bass=('bass_sine', 'jig'),
                  pad='pad', pad_gain=0.3, drums='night', lead_vel=0.5), lead=(67, 86)),

    # ---------------- interiors
    Piece('int_casa', 'F', 'major', 80, 4,
          {'A': ['1', '6', '2', '5', '1', '6', '4', '5'], 'B': ['4', '3', '2', '5', '4', '1', '2s', '5']},
          'A B', V(lead='musicbox', arp=('epiano', 'broken'), arp_vel=0.3, bass=('bass_sine', 'root'), pad='pad', pad_gain=0.25,
                    drums='none', lead_vel=0.55, rms=0.11), lead=(72, 91), rev=(0.8, 0.22)),
    Piece('int_posada', 'D', 'major', 250, 6,
          {'A': ['1', '4', '1', '5', '1', '4', '5', '1'], 'B': ['6', '5', '4', '5', '6', '2', '5', '5']},
          'A B A2', V(lead='whistle', lead2='lute', counter='lute', arp=('lute', 'jig'), arp_vel=0.45, bass=('bass_pluck', 'jig'),
                       drums='tavern', rms=0.13), lead=(69, 88), rev=(0.7, 0.18), extra=tavern_extra),
    Piece('int_capilla', 'F', 'major', 60, 4,
          {'A': ['1', '4', '6', '5', '1', '4', '5', '1'], 'B': ['6', '3', '4', '1', '2', '5', '1', '1']},
          'A B', V(lead='organ_soft', counter='choir', arp=('choir', 'block'), arp_vel=0.3, bass=('organ', 'root'), bass_lo=36,
                    pad='organ', pad_gain=0.3, drums='chorale', lead_vel=0.55, legato=0.99, rms=0.11), lead=(65, 81), rev=(2.0, 0.42)),
    Piece('int_herreria', 'D', 'mixolydian', 96, 4,
          {'A': ['1', '7', '1', '7', '4', '1', '7', '1'], 'B': ['4', '4', '1', '1', '7', '4', '5m', '1']},
          'A B', V(lead='horn', arp=('guitar', 'stabs'), arp_vel=0.35, bass=('bass_pluck', 'octave8'), drums='forge', drum_vel=0.8,
                    pad='pad_saw', pad_gain=0.15, rms=0.13), lead=(57, 76), rev=(0.6, 0.15), extra=forge_extra),

    # ---------------- camp / rest: the main theme, slow and intimate
    Piece('camp', 'D', 'major', 66, 4,
          {'A': THEME_CHORDS, 'B': ['6', '3', '4', '1', '6', '4', '2', '5']},
          'A B', V(lead='guitar', counter='flute', arp=('guitar', 'broken'), arp_vel=0.35, bass=('bass_sine', 'root'), drums='none',
                    lead_vel=0.6, rms=0.11), theme=4, lead=(62, 79), rev=(1.1, 0.25)),

    # ---------------- battle
    Piece('combat', 'E', 'minor', 152, 4,
          {'A': ['1', '1', '6', '7', '1', '1', '4', '5M'], 'B': ['6', '7', '1', '1', '4', '5M', '6', '5M']},
          'A B A2 B', V(lead='pulse25', lead2='warm', counter='pulse12', arp=('pulse12', 'up16'), arp_vel=0.22, bass=('bass_tri', 'octave8'),
                         drums='drive', fills=True, rms=0.16), lead=(64, 83), fast=True),
    Piece('combat_elite', 'C#', 'harmonic', 160, 4,
          {'A': ['1', '6', '4', '5', '1', '6', 'b7', '5'], 'B': ['6', 'b7', '1', '1', '4', '6', '5', '5']},
          'A B A2 B', V(lead='brass', lead2='pulse25', counter='choir', arp=('strings', 'stabs'), arp_vel=0.35, bass=('bass_saw', 'gallop'),
                         pad='choir', pad_gain=0.25, drums='battle', fills=True, rms=0.17), lead=(61, 80), fast=True, extra=boss_extra),

    # ---------------- LAS CATACUMBAS DEL REY OLVIDADO: one dark piece per zone (no night layer: there is no sky down there)
    Piece('region_k', 'C', 'phrygian', 64, 4,     # Cementerio subterráneo: bells over a slow heartbeat
          {'A': ['1', 'b2', '1', '7', '6', 'b2', '1', '1'], 'B': ['4m', 'b2', '1', '1', '6', '7', '1', '5M']},
          'A B A2', V(lead='bell', lead2='choir', counter='pad_dark', arp=('celesta', 'slow'), arp_vel=0.2, bass=('bass_sine', 'pedal'),
                       pad='pad_dark', pad_gain=0.5, drums='heart', lead_vel=0.45, rms=0.12), lead=(60, 79), rev=(2.0, 0.42), extra=corrupt_extra),
    Piece('region_l', 'D', 'phrygian', 84, 4,     # Galerías de los mineros: pick strikes and low strings
          {'A': ['1', '1', 'b2', '1', '7', '1', 'b2', '5M'], 'B': ['6', '7', '1', '1', '4m', 'b2', '5M', '5M']},
          'A B A2', V(lead='warm_dark', lead2='bell', counter='strings_dark', arp=('strings_dark', 'stabs'), arp_vel=0.25, bass=('bass_pluck', 'pedal'),
                       pad='pad_dark', pad_gain=0.4, drums='forge', drum_vel=0.5, lead_vel=0.5, rms=0.12), lead=(57, 76), rev=(1.6, 0.36), extra=forge_extra),
    Piece('region_m', 'A', 'harmonic', 72, 4,     # Criptas de los caballeros: a funeral march
          {'A': ['1', '6', '4', '5', '1', '6', 'b2', '5'], 'B': ['6', '4', '1', '5', '6', '2o', '5', '5']},
          'A B A2', V(lead='horn', lead2='choir', counter='strings_dark', arp=('strings_dark', 'block'), arp_vel=0.3, bass=('bass_sine', 'march'),
                       pad='choir', pad_gain=0.3, drums='march', drum_vel=0.45, lead_vel=0.5, rms=0.12), lead=(57, 76), rev=(1.8, 0.4)),
    Piece('region_n', 'F#', 'harmonic', 66, 4,    # Santuario de los sacrificios: ritual choir and organ
          {'A': ['1', '1', 'b2', '1', '6', '6', 'b2', '5'], 'B': ['4m', '5', '1', '6', '4m', 'b2', '5', '5']},
          'A B A2', V(lead='choir', lead2='organ_soft', counter='bell', arp=('bell', 'slow'), arp_vel=0.2, bass=('organ', 'root'), bass_lo=36,
                       pad='organ', pad_gain=0.3, drums='chorale', lead_vel=0.5, legato=0.99, rms=0.12), lead=(61, 80), rev=(2.2, 0.45)),
    Piece('region_o', 'E', 'minor', 58, 4,        # Puente de los condenados: wind over the abyss, a lonely bell
          {'A': ['1', '6', '1', '7', '1', '6', 'b2', '1'], 'B': ['6', '7', '1', '1', '6', '4m', '5M', '5M']},
          'A B A2', V(lead='celesta', lead2='bell', counter='pad_dark', arp=('harp', 'slow'), arp_vel=0.18, bass=('bass_sine', 'pedal'),
                       pad='pad_dark', pad_gain=0.55, drums='night', lead_vel=0.4, rms=0.11), lead=(64, 83), rev=(2.4, 0.48), extra=corrupt_extra),
    Piece('region_p', 'C#', 'harmonic', 60, 4,    # Trono del Rey Sepultado: the king's theme, still asleep
          {'A': ['1', '6', '4', '5', '1', '6', 'b2', '5'], 'B': ['6', 'b2', '1', '1', '4m', '2o', '5', '5']},
          'A B A2', V(lead='organ_soft', lead2='choir', counter='bell', arp=('celesta', 'slow'), arp_vel=0.18, bass=('organ', 'root'), bass_lo=36,
                       pad='choir', pad_gain=0.35, drums='heart', lead_vel=0.45, rms=0.12), lead=(61, 80), rev=(2.4, 0.46)),
    # El Rey Sepultado: organ, choir and bells, a heavy march that breaks into a gallop
    Piece('boss_R', 'C#', 'harmonic', 144, 4,
          {'A': ['1', '1', '6', '5', '1', '1', 'b2', '5'], 'B': ['6', 'b2', '1', '1', '4m', '6', '5', '5']},
          'A B A2 B', V(lead='organ', lead2='brass', counter='choir', arp=('bell', 'up16'), arp_vel=0.2, bass=('bass_saw', 'gallop'),
                         pad='choir', pad_gain=0.3, drums='boss', fills=True, rms=0.17), lead=(61, 80), fast=True, intro=(4, 'boss'), extra=boss_extra),

    # ---------------- bosses (intro + loop)
    Piece('boss_I', 'F#', 'harmonic', 132, 4,     # El Invocador: ritual, choir and bells
          {'A': ['1', '1', '6', '5', '1', '1', '4', '5'], 'B': ['6', '4', '6', '5', '6', '4', '2o', '5']},
          'A B A2 B', V(lead='choir', lead2='bell', counter='celesta', arp=('bell', 'up16'), arp_vel=0.18, bass=('bass_tri', 'octave8'),
                         pad='pad_dark', pad_gain=0.35, drums='drive', fills=True, rms=0.16), lead=(61, 80), intro=(2, 'boss'), extra=boss_extra),
    Piece('boss_K', 'A', 'phrygian', 140, 4,      # Gorgrak el Caudillo: war drums
          {'A': ['1', '1', '2', '1', '1', '1', '7', '2'], 'B': ['6', '7', '1', '1', '6', '7', '2', '2']},
          'A B A2 B', V(lead='brass', lead2='horn', counter='choir', arp=('strings_dark', 'stabs'), arp_vel=0.35, bass=('bass_saw', 'gallop'),
                         drums='tribal', drum_vel=1.0, fills=True, rms=0.17), lead=(57, 76), fast=True, intro=(2, 'boss'), extra=boss_extra),
    Piece('boss_Q', 'G', 'harmonic', 198, 6,      # Madre de Sangre: macabre waltz
          {'A': ['1', '1', '4', '5', '1', '6', '4', '5'], 'B': ['6', '4', '5', '1', '6', '2o', '5', '5']},
          'A B A2 B', V(lead='organ', lead2='strings', counter='choir', arp=('harp', 'jig'), arp_vel=0.3, bass=('bass_saw', 'jig'),
                         pad='strings_dark', pad_gain=0.3, drums='macabre', fills=True, rms=0.16), lead=(62, 81), intro=(2, 'boss'), extra=boss_extra),
    Piece('boss_B', 'D', 'minor', 156, 4,         # Señor Demonio: the final battle
          {'A': ['1', '6', '7', '1', '1', '6', '4', '5M'], 'B': ['4', '5M', '1', '6', '4', '6', '5M', '5M']},
          'A B A2 B', V(lead='organ', lead2='brass', counter='choir', arp=('pulse12', 'up16'), arp_vel=0.2, bass=('bass_saw', 'octave8'),
                         pad='choir', pad_gain=0.3, drums='boss', fills=True, rms=0.17), lead=(62, 81), fast=True, intro=(4, 'boss'), extra=boss_extra),
    Piece('boss_F', 'B', 'minor', 124, 4,         # Coloso de Escarcha: crystalline and heavy
          {'A': ['1', '4M', '1', '4M', '6', '7', '5', '5'], 'B': ['6', '7', '1', '4M', '6', '7', '5', '5']},
          'A B A2 B', V(lead='strings', lead2='brass', counter='glock', arp=('celesta', 'up16'), arp_vel=0.25, bass=('bass_tri', 'octave8'),
                         pad='pad', pad_gain=0.3, drums='boss', fills=True, rms=0.16), lead=(62, 83), intro=(2, 'boss'), extra=boss_extra),
]


# ---------------------------------------------------------------- jingles (one-shots)
def jingle(kind):
    key = Key('D', 'major')
    if kind == 'victory':                 # the leitmotif as a fanfare
        s = Song(120, 8, False, 1.2, 0.25)
        s.bus('lead', 1, 0.3); s.bus('harm', 0.6, 0.4); s.bus('drums', 0.6, 0.2); s.bus('bass', 0.8, 0.1)
        line = [(0, .5, 5), (.5, .5, 6), (1, .5, 5), (1.5, .5, 3), (2, .75, 2), (2.75, .25, 3), (3, 1, 5), (4, 4, 8)]
        for bt, d, deg in line:
            s.note('lead', 'brass', bt, d * 0.95, key.degree_midi(deg, 4), 0.8)
            s.note('lead', 'pulse25', bt, d * 0.95, key.degree_midi(deg, 5), 0.3)
        for bt, ch in ((0, '1'), (2, '5'), (4, '1')):
            for m in voice(key.chord(ch), None, 62): s.note('harm', 'strings', bt, 2 if bt < 4 else 4, m, 0.5)
            s.note('bass', 'bass_tri', bt, 2, key.degree_midi(int(ch), 2), 0.7)
        for i in range(8): s.note('harm', 'harp', 4 + i * 0.125, 2, voice(key.chord('1'), None, 72)[i % 3] + 12 * (i // 3), 0.4)
        s.hit('drums', 'timpani', 0, 0.6); s.hit('drums', 'roll', 3, 0.6); s.hit('drums', 'timpani', 4, 0.9); s.hit('drums', 'crash', 4, 0.6)
        return s.render(0.17)
    if kind == 'defeat':
        k = Key('D', 'minor')
        s = Song(70, 6, False, 1.6, 0.35)
        s.bus('lead', 1, 0.4); s.bus('harm', 0.6, 0.5); s.bus('bass', 0.8, 0.2)
        for bt, d, deg in [(0, 1, 5), (1, 1, 4), (2, .5, 3), (2.5, .5, 2), (3, 3, 1)]:
            s.note('lead', 'flute', bt, d * 0.95, k.degree_midi(deg, 4), 0.6)
        for bt, ch in ((0, '4'), (2, '5M'), (3, '1')):
            for m in voice(k.chord(ch), None, 58): s.note('harm', 'strings_dark', bt, 3 if bt == 3 else 1, m, 0.5)
        s.note('bass', 'bass_sine', 0, 6, k.degree_midi(1, 2), 0.6)
        return s.render(0.13)
    if kind == 'levelup':
        s = Song(140, 6, False, 1.0, 0.25)
        s.bus('lead', 1, 0.3); s.bus('harm', 0.6, 0.35)
        for i, deg in enumerate([1, 3, 5, 8, 10, 12]):
            s.note('lead', 'pulse25', i * 0.25, 0.3, key.degree_midi(deg, 4), 0.55)
            s.note('harm', 'bell', i * 0.25, 1, key.degree_midi(deg, 5), 0.25)
        for m in voice(key.chord('1'), None, 74): s.note('harm', 'strings', 1.5, 2.5, m, 0.5)
        s.note('lead', 'warm', 1.5, 2.5, key.degree_midi(8, 5), 0.6)
        return s.render(0.15)
    if kind == 'discover':
        k = Key('A', 'lydian')
        s = Song(90, 6, False, 1.5, 0.35)
        s.bus('lead', 1, 0.4); s.bus('harm', 0.6, 0.45)
        for bt, d, deg in [(0, .5, 1), (.5, .5, 4), (1, .5, 5), (1.5, 2.5, 7)]:
            s.note('lead', 'celesta', bt, d, k.degree_midi(deg, 5), 0.6)
        for m in voice(k.chord('1'), None, 64): s.note('harm', 'pad', 0, 3, m, 0.45)
        for m in voice(k.chord('2'), None, 66): s.note('harm', 'harp', 1.5, 2, m, 0.35)
        return s.render(0.13)
    raise ValueError(kind)


JINGLES = ['victory', 'defeat', 'levelup', 'discover']


def build(only=None, samples=False):
    os.makedirs(OUT, exist_ok=True)
    made = []
    for p in PIECES:
        if only and p.id not in only: continue
        day = p.build(False)
        write_wav(os.path.join(OUT, f'music_{p.id}_loop.wav'), day); made.append(f'music_{p.id}_loop.wav')
        if p.night:
            night = p.build(True)
            assert len(night) == len(day), p.id
            write_wav(os.path.join(OUT, f'music_{p.id}_night.wav'), night); made.append(f'music_{p.id}_night.wav')
        intro = p.build_intro()
        if intro is not None:
            write_wav(os.path.join(OUT, f'music_{p.id}_intro.wav'), intro); made.append(f'music_{p.id}_intro.wav')
        print(f'{p.id:16s} {len(day) / SR:5.1f}s' + ('  +night' if p.night else '') + ('  +intro' if intro is not None else ''), flush=True)
    for j in JINGLES:
        if only and ('jingle_' + j) not in only: continue
        write_wav(os.path.join(OUT, f'jingle_{j}.wav'), jingle(j)); made.append(f'jingle_{j}.wav')
    if samples:
        os.makedirs(SAMPLES, exist_ok=True)
        for f in made: shutil.copy(os.path.join(OUT, f), os.path.join(SAMPLES, f))
    return made


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    print(len(build(set(args) if args else None, '--samples' in sys.argv)), 'files')
