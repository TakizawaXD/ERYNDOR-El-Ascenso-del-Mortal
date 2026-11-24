"""Small warm chiptune synthesizer (numpy): band-limited pulses, plucked strings, bells, flutes, pads, organ, drums,
reverb and echo, plus a tiny song model (notes on beats, buses, seamless loop folding).

Used by music.py (pieces), sfx2.py (effects) and ambience.py (ambient loops). Mono 22 050 Hz, 16-bit WAV.
"""
import math, os, struct, wave
import numpy as np
from scipy.signal import lfilter

SR = 22050
RNG = np.random.default_rng(1234)


# ------------------------------------------------------------------ io
def write_wav(path, x, peak=0.97):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    x = np.asarray(x, dtype=np.float64)
    x = np.clip(x, -peak, peak)
    data = (x * 32767).astype('<i2').tobytes()
    with wave.open(path, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data)


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def secs(n):
    return np.arange(n) / SR


# ------------------------------------------------------------------ filters
def lowpass(x, fc):
    fc = min(fc, SR * 0.45)
    a = 1 - math.exp(-2 * math.pi * fc / SR)
    return lfilter([a], [1, -(1 - a)], x)


def highpass(x, fc):
    return x - lowpass(x, fc)


def biquad(x, kind, f0, q=0.707, gain_db=0.0):
    w0 = 2 * math.pi * min(f0, SR * 0.45) / SR
    alpha = math.sin(w0) / (2 * q)
    cw = math.cos(w0)
    if kind == 'lp':
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == 'hp':
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == 'bp':
        b = [alpha, 0, -alpha]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == 'peak':
        A = 10 ** (gain_db / 40)
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]; a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    else:
        raise ValueError(kind)
    return lfilter(np.array(b) / a[0], np.array(a) / a[0], x)


def formant(x, freqs, qs=None, gains=None):
    """Parallel band-passes (vowel colour)."""
    out = np.zeros_like(x)
    for i, f in enumerate(freqs):
        q = qs[i] if qs else 6.0
        g = gains[i] if gains else 1.0
        out += g * biquad(x, 'bp', f, q)
    return out


def _blockrec(x, d, fn):
    """y computed block by block (block = delay length) so feedback only needs the previous block"""
    n = len(x); y = np.zeros(n); xp = np.zeros(d); yp = np.zeros(d)
    for s in range(0, n, d):
        e = min(n, s + d); L = e - s
        yk = fn(x[s:e], xp[:L], yp[:L])
        y[s:e] = yk
        xp = np.zeros(d); yp = np.zeros(d); xp[:L] = x[s:e]; yp[:L] = yk
    return y


def comb(x, d, g):
    return _blockrec(x, d, lambda xk, xp, yp: xk + g * yp)


def allpass(x, d, g):
    return _blockrec(x, d, lambda xk, xp, yp: -g * xk + xp + g * yp)


def reverb(x, size=1.0, damp=3500, decay=0.82):
    """Schroeder hall: 4 combs + 2 allpasses, damped. Returns the wet signal only."""
    ds = [int(d * size * SR / 44100) for d in (1557, 1617, 1491, 1422)]
    y = sum(comb(x, d, decay) for d in ds) * 0.25
    y = allpass(y, int(225 * SR / 44100), 0.5)
    y = allpass(y, int(556 * SR / 44100), 0.5)
    return lowpass(highpass(y, 120), damp)


def echo(x, delay_s, fb=0.35, mix=1.0):
    d = max(1, int(delay_s * SR))
    return lowpass(_blockrec(x, d, lambda xk, xp, yp: xp + fb * yp), 3000) * mix


def softclip(x, drive=1.0):
    return np.tanh(x * drive) / math.tanh(drive)


# ------------------------------------------------------------------ oscillators
def _blep(t, dt):
    y = np.zeros_like(t)
    m = t < dt
    x = t[m] / dt[m]
    y[m] = 2 * x - x * x - 1
    m2 = t > 1 - dt
    x = (t[m2] - 1) / dt[m2]
    y[m2] = x * x + 2 * x + 1
    return y


def phase_of(freq):
    return np.cumsum(freq) / SR


def saw(freq):
    ph = phase_of(freq) % 1.0
    dt = np.clip(freq / SR, 1e-6, 0.5)
    return 2 * ph - 1 - _blep(ph, dt)


def pulse(freq, duty=0.5):
    ph = phase_of(freq) % 1.0
    dt = np.clip(freq / SR, 1e-6, 0.5)
    ph2 = (ph + duty) % 1.0
    s1 = 2 * ph - 1 - _blep(ph, dt)
    s2 = 2 * ph2 - 1 - _blep(ph2, dt)
    return 0.5 * (s1 - s2)


def tri(freq, steps=0):
    ph = phase_of(freq) % 1.0
    v = 4 * np.abs(ph - 0.5) - 1
    if steps:
        v = np.round((v + 1) * (steps - 1) / 2) / ((steps - 1) / 2) - 1
        v = lowpass(v, 6000)
    return v


def sine(freq):
    return np.sin(2 * math.pi * phase_of(freq))


def noise(n, seed=None):
    r = np.random.default_rng(seed) if seed is not None else RNG
    return r.uniform(-1, 1, n)


# ------------------------------------------------------------------ envelopes
def env_adsr(n, gate, a=0.01, d=0.1, s=0.7, r=0.1):
    """n samples total; gate = samples the key is held."""
    t = secs(n)
    e = np.ones(n)
    ga = max(a, 1e-4)
    e = np.where(t < ga, t / ga, s + (1 - s) * np.exp(-(t - ga) / max(d, 1e-4)))
    gt = gate / SR
    level_at_gate = (gt / ga) if gt < ga else s + (1 - s) * math.exp(-(gt - ga) / max(d, 1e-4))
    rel = level_at_gate * np.exp(-(t - gt) / max(r / 4.0, 1e-4))
    return np.where(t < gt, e, rel)


def env_perc(n, decay, a=0.002):
    t = secs(n)
    return np.minimum(1, t / a) * np.exp(-t / decay)


def vibrato(n, f, rate=5.5, depth=0.004, delay=0.18):
    t = secs(n)
    ramp = np.clip((t - delay) / 0.25, 0, 1)
    return f * (1 + depth * ramp * np.sin(2 * math.pi * rate * t))


# ------------------------------------------------------------------ instruments
# every instrument: fn(freq, dur_seconds, vel) -> samples (includes its release tail)

def i_pulse(duty, cutoff=5200, a=0.006, d=0.12, s=0.65, r=0.08, vib=0.004):
    def f(freq, dur, vel):
        n = int((dur + r * 2.5) * SR); g = int(dur * SR)
        x = pulse(vibrato(n, freq, depth=vib), duty)
        return lowpass(x, cutoff) * env_adsr(n, g, a, d, s, r) * vel
    return f


def i_warmlead(cutoff=2600):
    def f(freq, dur, vel):
        n = int((dur + 0.35) * SR); g = int(dur * SR)
        fv = vibrato(n, freq, depth=0.005)
        x = 0.5 * saw(fv * 1.0035) + 0.5 * saw(fv * 0.9965) + 0.3 * pulse(fv * 0.5, 0.5)
        x = lowpass(lowpass(x, cutoff), cutoff * 1.4)
        return x * env_adsr(n, g, 0.025, 0.2, 0.75, 0.14) * vel * 0.8
    return f


def i_flute(breath=0.06):
    def f(freq, dur, vel):
        n = int((dur + 0.3) * SR); g = int(dur * SR)
        fv = vibrato(n, freq, 5.0, 0.006, 0.22)
        ph = phase_of(fv) * 2 * math.pi
        x = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.07 * np.sin(3 * ph)
        b = biquad(noise(n), 'bp', min(freq * 2, 5000), 2.0) * breath
        e = env_adsr(n, g, 0.05, 0.25, 0.85, 0.12)
        return (x + b * (0.6 + 0.4 * np.exp(-secs(n) / 0.08))) * e * vel * 0.7
    return f


def i_pluck(bright=1.0, decay=1.2, harmonics=14, body=0.0):
    """Harp / lute / guitar / oud: additive partials whose upper harmonics die faster."""
    def f(freq, dur, vel):
        ring = min(decay * (220 / max(freq, 60)) ** 0.35, 3.2)
        n = int((min(dur, ring) + 0.25) * SR)
        t = secs(n)
        x = np.zeros(n)
        kmax = max(1, min(harmonics, int((SR * 0.45) / freq)))
        for k in range(1, kmax + 1):
            amp = (1.0 / k ** 1.25) * abs(math.sin(math.pi * k * 0.18)) * 1.6
            rate = 1.0 / ring + 0.9 * (k - 1) ** 1.4 / bright
            x += amp * np.sin(2 * math.pi * freq * k * t * (1 + 0.0004 * k)) * np.exp(-t * rate)
        if body:
            x += body * biquad(x, 'bp', 280, 1.5)
        cut = int(dur * SR)
        if cut < n:   # damp after the note ends
            x[cut:] *= np.exp(-(t[cut:] - t[cut]) / 0.06)
        return x * np.minimum(1, t / 0.0015) * vel * 0.55
    return f


def i_fm(ratio=1.0, index=1.5, idecay=0.4, decay=1.5, a=0.002, sustain=False):
    """Electric piano (ratio 1), bell / celesta (ratio 3.5), music box (ratio 4)."""
    def f(freq, dur, vel):
        n = int(((dur + 0.6) if sustain else max(dur, decay * 1.5) + 0.1) * SR)
        t = secs(n)
        I = index * (0.25 + 0.75 * np.exp(-t / idecay))
        x = np.sin(2 * math.pi * freq * t + I * np.sin(2 * math.pi * freq * ratio * t))
        if sustain:
            e = env_adsr(n, int(dur * SR), a, decay, 0.5, 0.4)
        else:
            e = np.minimum(1, t / a) * np.exp(-t / decay)
            cut = int(dur * SR * 1.6)
            if cut < n: e[cut:] *= np.exp(-(t[cut:] - t[cut]) / 0.15)
        return x * e * vel * 0.6
    return f


def i_pad(kind='tri', cutoff=1800, a=0.35, r=0.7, detune=0.006):
    def f(freq, dur, vel):
        n = int((dur + r * 2.2) * SR); g = int(dur * SR)
        osc = tri if kind == 'tri' else saw
        x = sum(osc(np.full(n, freq * (1 + dt))) for dt in (-detune, 0, detune)) / 3
        if kind != 'tri': x = lowpass(lowpass(x, cutoff), cutoff)
        return x * env_adsr(n, g, a, 0.5, 0.85, r) * vel * 0.5
    return f


def i_strings(cutoff=2400):
    def f(freq, dur, vel):
        n = int((dur + 0.5) * SR); g = int(dur * SR)
        fv = vibrato(n, freq, 5.2, 0.005, 0.3)
        x = sum(saw(fv * (1 + d)) for d in (-0.007, 0.0, 0.006)) / 3
        x = lowpass(lowpass(x, cutoff), cutoff * 1.3)
        return x * env_adsr(n, g, 0.14, 0.4, 0.85, 0.25) * vel * 0.55
    return f


def i_choir():
    def f(freq, dur, vel):
        n = int((dur + 0.6) * SR); g = int(dur * SR)
        fv = vibrato(n, freq, 4.8, 0.007, 0.25)
        x = sum(saw(fv * (1 + d)) for d in (-0.008, 0.0, 0.009)) / 3
        x = formant(x, [700, 1150, 2600], [5, 6, 8], [1.0, 0.6, 0.25])
        return x * env_adsr(n, g, 0.25, 0.4, 0.9, 0.35) * vel * 1.6
    return f


def i_organ(bars=(1.0, 0.6, 0.35, 0.3, 0.15, 0.12), trem=0.06):
    mults = (1, 2, 3, 4, 6, 8)
    def f(freq, dur, vel):
        n = int((dur + 0.25) * SR); g = int(dur * SR)
        t = secs(n)
        x = np.zeros(n)
        for m, b in zip(mults, bars):
            if freq * m < SR * 0.45: x += b * np.sin(2 * math.pi * freq * m * t)
        x *= 1 + trem * np.sin(2 * math.pi * 5.8 * t)
        return x * env_adsr(n, g, 0.03, 0.2, 0.9, 0.08) * vel * 0.3
    return f


def i_brass(cutoff=1800):
    def f(freq, dur, vel):
        n = int((dur + 0.3) * SR); g = int(dur * SR)
        fv = vibrato(n, freq, 5.0, 0.004, 0.3)
        x = 0.6 * saw(fv) + 0.4 * saw(fv * 1.004)
        dark = lowpass(lowpass(x, cutoff * 0.35), cutoff * 0.5)
        bright = lowpass(x, cutoff * 1.6)
        fe = env_adsr(n, g, 0.06, 0.25, 0.55, 0.1)
        y = dark * (1 - fe) + bright * fe
        return y * env_adsr(n, g, 0.035, 0.3, 0.8, 0.12) * vel * 0.8
    return f


def i_accordion():
    def f(freq, dur, vel):
        n = int((dur + 0.15) * SR); g = int(dur * SR)
        t = secs(n)
        x = pulse(np.full(n, freq * 1.003), 0.42) + pulse(np.full(n, freq * 0.997), 0.3) * 0.7 + 0.3 * pulse(np.full(n, freq * 2), 0.5)
        x = lowpass(lowpass(x, 3200), 4200) * (1 + 0.08 * np.sin(2 * math.pi * 6.2 * t))
        return x * env_adsr(n, g, 0.03, 0.2, 0.85, 0.06) * vel * 0.5
    return f


def i_bass(kind='tri', cutoff=900):
    def f(freq, dur, vel):
        n = int((dur + 0.08) * SR); g = int(dur * SR)
        if kind == 'tri':
            x = tri(np.full(n, freq), steps=16)
            e = env_adsr(n, g, 0.004, 0.2, 0.85, 0.05)
        elif kind == 'pulse':
            x = lowpass(pulse(np.full(n, freq), 0.5), cutoff) * 1.3
            e = env_adsr(n, g, 0.004, 0.15, 0.7, 0.05)
        elif kind == 'sine':
            x = np.sin(2 * math.pi * freq * secs(n)) + 0.15 * np.sin(4 * math.pi * freq * secs(n))
            e = env_adsr(n, g, 0.01, 0.3, 0.8, 0.08)
        else:  # 'saw' synth bass
            x = lowpass(lowpass(saw(np.full(n, freq)), cutoff), cutoff)
            e = env_adsr(n, g, 0.004, 0.18, 0.75, 0.05)
        return x * e * vel * 0.85
    return f


def i_glock():
    def f(freq, dur, vel):
        n = int((1.6) * SR); t = secs(n)
        x = np.sin(2 * math.pi * freq * t) + 0.35 * np.sin(2 * math.pi * freq * 2.76 * t) * np.exp(-t / 0.15) + 0.15 * np.sin(2 * math.pi * freq * 5.4 * t) * np.exp(-t / 0.06)
        return x * np.minimum(1, t / 0.001) * np.exp(-t / 0.55) * vel * 0.45
    return f


INSTRUMENTS = {
    'pulse12': i_pulse(0.125, 4800), 'pulse25': i_pulse(0.25, 4400), 'pulse50': i_pulse(0.5, 3000),
    'pulse_soft': i_pulse(0.25, 2200, a=0.02, s=0.55, r=0.18),
    'clarinet': i_pulse(0.5, 1500, a=0.04, d=0.3, s=0.8, r=0.1, vib=0.005),
    'warm': i_warmlead(), 'warm_dark': i_warmlead(1500), 'flute': i_flute(), 'whistle': i_flute(0.12),
    'harp': i_pluck(1.0, 1.6, 12), 'lute': i_pluck(1.6, 0.9, 16, 0.3), 'guitar': i_pluck(1.2, 1.3, 14, 0.4),
    'oud': i_pluck(2.2, 0.7, 18, 0.5), 'bass_pluck': i_pluck(0.7, 0.9, 8),
    'epiano': i_fm(1.0, 1.4, 0.25, 1.4), 'bell': i_fm(3.5, 2.2, 0.3, 1.6), 'celesta': i_fm(4.0, 1.2, 0.12, 0.8),
    'musicbox': i_fm(5.0, 0.9, 0.06, 0.9), 'glock': i_glock(),
    'pad': i_pad('tri'), 'pad_saw': i_pad('saw', 1400), 'pad_dark': i_pad('saw', 700, 0.6, 1.0, 0.009),
    'strings': i_strings(), 'strings_dark': i_strings(1200), 'choir': i_choir(),
    'organ': i_organ(), 'organ_soft': i_organ((1.0, 0.4, 0.1, 0.12, 0.0, 0.05), 0.03),
    'brass': i_brass(), 'horn': i_brass(1100), 'accordion': i_accordion(),
    'bass_tri': i_bass('tri'), 'bass_pulse': i_bass('pulse', 700), 'bass_sine': i_bass('sine'), 'bass_saw': i_bass('saw', 600),
}


# ------------------------------------------------------------------ drums
def drum(name, vel=1.0, seed=None):
    r = np.random.default_rng(seed)
    def nz(n): return r.uniform(-1, 1, n)
    if name == 'kick':
        n = int(0.32 * SR); t = secs(n)
        f = 48 + 110 * np.exp(-t / 0.035)
        x = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t / 0.14) + 0.15 * lowpass(nz(n), 2000) * np.exp(-t / 0.006)
        return x * vel * 0.9
    if name == 'snare':
        n = int(0.24 * SR); t = secs(n)
        body = np.sin(2 * math.pi * 185 * t) * np.exp(-t / 0.05) * 0.5
        sn = biquad(nz(n), 'hp', 1200) * np.exp(-t / 0.075)
        return (body + 0.8 * lowpass(sn, 7000)) * vel * 0.55
    if name == 'brush':
        n = int(0.22 * SR); t = secs(n)
        return lowpass(biquad(nz(n), 'hp', 1500), 6000) * np.minimum(1, t / 0.015) * np.exp(-t / 0.08) * vel * 0.3
    if name in ('hat', 'ohat'):
        n = int((0.05 if name == 'hat' else 0.25) * SR); t = secs(n)
        return biquad(nz(n), 'hp', 7000) * np.exp(-t / (0.018 if name == 'hat' else 0.09)) * vel * 0.28
    if name == 'shaker':
        n = int(0.09 * SR); t = secs(n)
        return biquad(nz(n), 'bp', 6500, 1.2) * np.minimum(1, t / 0.02) * np.exp(-t / 0.03) * vel * 0.35
    if name == 'tamb':
        n = int(0.2 * SR); t = secs(n)
        jingle = sum(np.sin(2 * math.pi * f * t) for f in (5100, 6300, 7400)) / 3
        return (0.6 * biquad(nz(n), 'hp', 6000) + 0.4 * jingle) * np.exp(-t / 0.06) * vel * 0.3
    if name in ('tom_lo', 'tom_hi', 'tabla_lo', 'tabla_hi'):
        base = {'tom_lo': 95, 'tom_hi': 150, 'tabla_lo': 110, 'tabla_hi': 330}[name]
        n = int(0.4 * SR); t = secs(n)
        bend = 1.25 if name.startswith('tabla') else 1.5
        f = base * (1 + (bend - 1) * np.exp(-t / 0.04)) if not name == 'tabla_lo' else base * (1 + 0.6 * np.minimum(t / 0.12, 1))
        x = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t / (0.18 if name.startswith('tom') else 0.12))
        x += 0.2 * lowpass(nz(n), 3000) * np.exp(-t / 0.01)
        return x * vel * 0.7
    if name == 'timpani':
        n = int(1.3 * SR); t = secs(n)
        x = sum(a * np.sin(2 * math.pi * 73.4 * m * t) for m, a in ((1, 1), (1.5, 0.5), (1.98, 0.3), (2.44, 0.15)))
        x = x * np.exp(-t / 0.5) + 0.3 * lowpass(nz(n), 500) * np.exp(-t / 0.03)
        return x * vel * 0.65
    if name == 'roll':   # timpani roll (one beat of it)
        n = int(0.5 * SR); x = np.zeros(n)
        for k in range(10):
            h = drum('timpani', 0.35 + 0.05 * k, seed=k)[:n - int(k * 0.05 * SR)]
            x[int(k * 0.05 * SR):int(k * 0.05 * SR) + len(h)] += h
        return x * vel * 0.5
    if name == 'clap':
        n = int(0.2 * SR); t = secs(n)
        e = sum(np.exp(-np.maximum(t - o, 0) / 0.01) * (t >= o) for o in (0, 0.01, 0.022))
        return biquad(nz(n), 'bp', 1400, 1.5) * (e + 0.5 * np.exp(-t / 0.08)) * vel * 0.6
    if name == 'rim':
        n = int(0.06 * SR); t = secs(n)
        return (np.sin(2 * math.pi * 1700 * t) + 0.5 * biquad(nz(n), 'bp', 3000, 3)) * np.exp(-t / 0.012) * vel * 0.4
    if name == 'anvil':
        n = int(0.9 * SR); t = secs(n)
        x = sum(a * np.sin(2 * math.pi * f * t) * np.exp(-t / d) for f, a, d in ((1180, 1, 0.35), (2730, 0.6, 0.2), (3990, 0.4, 0.12), (5210, 0.25, 0.08)))
        x += 0.4 * biquad(nz(n), 'hp', 3000) * np.exp(-t / 0.008)
        return x * vel * 0.3
    if name == 'crash':
        n = int(1.4 * SR); t = secs(n)
        return biquad(nz(n), 'hp', 4000) * np.exp(-t / 0.5) * vel * 0.22
    if name == 'mug':   # wooden mug knock (tavern)
        n = int(0.12 * SR); t = secs(n)
        return (np.sin(2 * math.pi * 420 * t) + 0.5 * np.sin(2 * math.pi * 990 * t)) * np.exp(-t / 0.03) * vel * 0.4
    if name == 'heart':
        n = int(0.5 * SR); t = secs(n)
        def thump(o, a):
            tt = np.maximum(t - o, 0)
            return a * np.sin(2 * math.pi * 55 * tt) * np.exp(-tt / 0.07) * (t >= o)
        return (thump(0, 1) + thump(0.16, 0.7)) * vel * 0.9
    raise ValueError(name)


_DRUM_CACHE = {}


def drum_cached(name, vel, variant):
    key = (name, variant)
    if key not in _DRUM_CACHE:
        _DRUM_CACHE[key] = drum(name, 1.0, seed=variant * 31 + len(name))
    return _DRUM_CACHE[key] * vel


# ------------------------------------------------------------------ song model
class Song:
    """Notes placed on beats into named buses; render() mixes, adds reverb/echo and folds the tail for a seamless loop."""

    def __init__(self, bpm, beats, loop=True, reverb_size=1.0, reverb_mix=0.22, echo_beats=0.75, swing=0.0):
        self.bpm = bpm; self.beats = beats; self.loop = loop
        self.spb = 60.0 / bpm
        self.length = int(round(beats * self.spb * SR))
        self.tail = int(3.5 * SR)
        self.buses = {}
        self.sends = {}           # bus -> (reverb, echo)
        self.gains = {}
        self.reverb_size = reverb_size; self.reverb_mix = reverb_mix
        self.echo_s = echo_beats * self.spb
        self.swing = swing

    def bus(self, name, gain=1.0, rev=0.25, echo=0.0):
        if name not in self.buses:
            self.buses[name] = np.zeros(self.length + self.tail)
        self.gains[name] = gain; self.sends[name] = (rev, echo)
        return name

    def _at(self, beat):
        if self.swing and abs((beat * 2) % 2 - 1) < 1e-6:   # off-beat eighths get pushed late
            beat += self.swing * 0.5
        return int(round(beat * self.spb * SR))

    def _add(self, bus, x, start):
        if bus not in self.buses: self.bus(bus)
        b = self.buses[bus]
        end = min(len(b), start + len(x))
        if start < 0 or start >= len(b): return
        b[start:end] += x[:end - start]

    def note(self, bus, inst, beat, dur_beats, midi, vel=0.8):
        if midi is None: return
        fn = INSTRUMENTS[inst] if isinstance(inst, str) else inst
        x = fn(midi_hz(midi), max(0.03, dur_beats * self.spb), vel)
        self._add(bus, x, self._at(beat))

    def hit(self, bus, name, beat, vel=0.8, variant=0):
        self._add(bus, drum_cached(name, vel, variant % 4), self._at(beat))

    def raw(self, bus, x, beat):
        self._add(bus, x, self._at(beat))

    def render(self, target_rms=0.16, master_lp=9000):
        n = self.length + self.tail
        dry = np.zeros(n); rsend = np.zeros(n); esend = np.zeros(n)
        for name, b in self.buses.items():
            g = self.gains.get(name, 1.0); rv, ec = self.sends.get(name, (0.25, 0))
            dry += b * g; rsend += b * g * rv; esend += b * g * ec
        mix = dry
        if esend.any(): mix = mix + echo(esend, self.echo_s, 0.32)
        if rsend.any(): mix = mix + reverb(rsend, self.reverb_size) * (self.reverb_mix * 4)
        mix = lowpass(mix, master_lp)
        mix = highpass(mix, 30)
        if self.loop:
            out = mix[:self.length].copy()
            out[:self.tail] += mix[self.length:self.length + self.tail][:min(self.tail, self.length)]
        else:
            # one-shot: trim silence at the end
            out = mix
            nz = np.nonzero(np.abs(out) > 1e-4)[0]
            out = out[:nz[-1] + int(0.05 * SR)] if len(nz) else out
            fade = min(len(out), int(0.05 * SR))
            out[-fade:] *= np.linspace(1, 0, fade)
        rms = math.sqrt(float(np.mean(out ** 2))) or 1.0
        out = out * (target_rms / rms)
        out = softclip(out, 1.2) * 0.95
        return out
