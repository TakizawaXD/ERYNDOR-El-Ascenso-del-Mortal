"""Music theory helpers for music.py: modes, chords from scale degrees, voice leading, motif-based melody writing."""
import random

MODES = {
    'major': [0, 2, 4, 5, 7, 9, 11], 'minor': [0, 2, 3, 5, 7, 8, 10], 'dorian': [0, 2, 3, 5, 7, 9, 10],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10], 'lydian': [0, 2, 4, 6, 7, 9, 11], 'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'harmonic': [0, 2, 3, 5, 7, 8, 11], 'phrygdom': [0, 1, 4, 5, 7, 8, 10],
}
NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
        'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


class Key:
    def __init__(self, tonic, mode):
        self.tonic = NOTE[tonic] if isinstance(tonic, str) else tonic
        self.mode = mode
        self.steps = MODES[mode]

    def pc(self, degree):
        """scale degree (1..7, may exceed) -> pitch class offset from C (can be > 11)"""
        d = degree - 1
        return self.tonic + self.steps[d % 7] + 12 * (d // 7)

    def scale_midis(self, lo, hi):
        out = []
        for m in range(lo, hi + 1):
            if (m - self.tonic) % 12 in self.steps: out.append(m)
        return out

    def degree_midi(self, degree, octave=4):
        return 12 * (octave + 1) + self.pc(degree)

    def chord(self, sym):
        """'1', '5', '6', '57' (seventh), '5M' force major, '4m' force minor, 'b7' borrowed major triad,
        '4s' sus4, '1+' augmented, 'o7' diminished on degree 7. Returns pitch classes (root first, 0..11)."""
        s = str(sym)
        borrowed = s.startswith('b')
        if borrowed: s = s[1:]
        deg = int(s[0]); rest = s[1:]
        if borrowed:
            root = (self.tonic + MODES['major'][deg - 1] - 1) % 12
            pcs = [root, root + 4, root + 7]
        else:
            root = self.pc(deg) % 12
            third = self.pc(deg + 2) - self.pc(deg)
            fifth = self.pc(deg + 4) - self.pc(deg)
            if 'M' in rest: third = 4; fifth = 7
            if 'm' in rest: third = 3; fifth = 7
            if '+' in rest: third = 4; fifth = 8
            if 'o' in rest: third = 3; fifth = 6
            pcs = [root, root + third, root + fifth]
            if 's' in rest: pcs = [root, root + 5, root + 7]
            if '7' in rest:
                sev = self.pc(deg + 6) - self.pc(deg)
                pcs.append(root + sev)
        return [p % 12 for p in pcs]


def voice(pcs, prev=None, center=60, size=3):
    """close voicing of the chord's pitch classes nearest to the previous voicing (smooth pads)"""
    best, bestc = None, 1e9
    for base in range(center - 12, center + 7):
        v = []
        for p in pcs[:size]:
            m = base + ((p - base) % 12)
            v.append(m)
        v.sort()
        c = sum(abs(a - b) for a, b in zip(v, prev)) if prev else abs(sum(v) / len(v) - center)
        if c < bestc: best, bestc = v, c
    return best


def nearest(pool, target):
    return min(pool, key=lambda m: (abs(m - target), m))


RHYTHMS = {
    4: [[1, 1, 1, 1], [1.5, .5, 1, 1], [.5, .5, 1, 2], [1, .5, .5, 2], [2, 1, 1], [1.5, .5, 2], [1, 1, 2],
        [.5, .5, .5, .5, 1, 1], [1, 1, .5, .5, 1], [3, 1], [1.5, .5, 1.5, .5]],
    3: [[1, 1, 1], [2, 1], [1.5, .5, 1], [1, .5, .5, 1], [.5, .5, 1, 1], [1, 2]],
    6: [[3, 3], [2, 1, 2, 1], [3, 2, 1], [1, 1, 1, 3], [2, 1, 3], [1, 1, 1, 2, 1], [3, 1, 1, 1]],
}
FAST = {4: [[.5, .5, .5, .5, 1, 1], [1, .5, .5, 1, 1], [.5, .5, 1, .5, .5, 1], [.75, .75, .5, 1, 1], [1.5, .5, 1, 1],
            [.5, .5, .5, .5, .5, .5, 1]]}
CADENCE = {4: [[1, 1, 2], [4], [2, 2], [1.5, .5, 2]], 3: [[3], [2, 1], [1, 2]], 6: [[6], [3, 3], [2, 1, 3]]}


class MelodyWriter:
    """Motif-based melody: a 2-bar motif (rhythm + scale contour) restated and varied over an 8-bar phrase,
    strong beats on chord tones, phrase endings on stable notes."""

    def __init__(self, key, meter, lo, hi, seed, fast=False):
        self.key = key; self.meter = meter; self.lo = lo; self.hi = hi
        self.rng = random.Random(seed)
        self.scale = key.scale_midis(lo - 12, hi + 12)
        self.fast = fast
        bank = FAST.get(meter) if fast and meter in FAST else RHYTHMS[meter]
        self.rA = [self.rng.choice(bank), self.rng.choice(bank)]
        self.rB = [self.rng.choice(bank), self.rng.choice(CADENCE[meter])]
        self.cA = self._contour(sum(len(r) for r in self.rA))
        self.cB = self._contour(sum(len(r) for r in self.rB))
        self.cur = nearest(self.scale, (lo + hi) // 2)

    def _contour(self, n):
        c = []
        direction = self.rng.choice([1, -1])
        for i in range(n):
            if self.rng.random() < 0.25: direction = -direction
            step = self.rng.choice([1, 1, 1, 2, 2, 3]) if i else 0
            if self.rng.random() < 0.12: step = 0
            c.append(step * direction)
        return c

    def _idx(self, m):
        return self.scale.index(nearest(self.scale, m))

    def _realise(self, rhythms, contour, chords, bar0, final=None, invert=False, shift=0):
        """chords: pitch-class list per bar (list of lists). returns [(beat, dur, midi)]"""
        out = []
        k = 0
        for b, rh in enumerate(rhythms):
            pcs = chords[b]
            beat = 0.0
            for j, d in enumerate(rh):
                step = contour[k] * (-1 if invert else 1); k += 1
                i = self._idx(self.cur) + step + (shift if j == 0 and b == 0 else 0)
                i = max(0, min(len(self.scale) - 1, i))
                m = self.scale[i]
                if m > self.hi: m = self.scale[max(0, i - 3)]
                if m < self.lo: m = self.scale[min(len(self.scale) - 1, i + 3)]
                strong = beat == 0 or (self.meter == 4 and beat == 2) or (self.meter == 6 and beat == 3)
                if strong or d >= 1.5:
                    tones = [x for x in self.scale if x % 12 in pcs and self.lo <= x <= self.hi]
                    if tones: m = nearest(tones, m)
                if final is not None and b == len(rhythms) - 1 and j == len(rh) - 1:
                    tones = [x for x in range(self.lo, self.hi + 1) if x % 12 == final % 12]
                    if tones: m = nearest(tones, m)
                out.append((bar0 + b, beat, d, m))
                self.cur = m
                beat += d
        return out

    def phrase(self, chord_bars, tonic_end=True, octave=0):
        """8 (or 4) bars of melody for chord_bars (list of pc lists). Returns [(bar, beat, dur, midi)]."""
        n = len(chord_bars)
        notes = []
        tonic = self.key.tonic
        fifth = self.key.tonic + self.key.steps[4]
        for b in range(0, n, 2):
            seg = chord_bars[b:b + 2]
            if len(seg) < 2: seg = seg + seg
            last = b + 2 >= n
            half = b + 2 == n // 2
            if last:
                notes += self._realise(self.rB, self.cB, seg, b, final=tonic if tonic_end else fifth)
            elif half:
                notes += self._realise(self.rA, self.cA, seg, b, final=fifth, invert=True)
            elif (b // 2) % 2 == 1:
                notes += self._realise(self.rA, self.cA, seg, b, shift=self.rng.choice([-2, 2, 1]))
            else:
                notes += self._realise(self.rA, self.cA, seg, b)
        if octave: notes = [(a, bt, d, m + 12 * octave) for a, bt, d, m in notes]
        return notes
