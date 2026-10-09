"""Original score: combative classic trap (no vocals), cued to the edit.
Dark marching intro -> impact on the card -> trap drop -> brass build into the logo ->
drum dropout before "התעוררנו" and a slam on it -> final hit on the end card."""
import os
import sys
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import timeline

SR = 48000
TOTAL = 40.0
_, _, _caps, _cards = timeline()
CARD, DROP, LAUNCH, LOGO = 4.72, 5.68, 16.20, 18.60
END = [c for c in _cards if c["kind"] == "end"][0]["start"]
WAKE = [a for a, b, t in _caps if "התעוררנו" in t][0]
BPM = 140
BEAT = 60 / BPM
BAR = 4 * BEAT
DROPOUT = WAKE - 2 * BEAT * 2  # one bar of silence for the drums before the slam

rng = np.random.default_rng(11)
N = int(TOTAL * SR)
mix = np.zeros((N, 2))

def t_(d): return np.arange(int(d * SR)) / SR
def lp(x, f, o=2): return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], "band", fs=SR, output="sos"), x)
def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-t / d)
def add(sig, at, gain=1.0, pan=0.0):
    i = int(round(at * SR))
    if i >= N or i < 0: return
    sig = sig[: N - i]
    if sig.ndim == 1:
        l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
    mix[i:i + len(sig)] += sig * gain
def osc_saw(freq, d):
    ph = np.cumsum(np.broadcast_to(freq, (int(d * SR),))) / SR
    return 2 * (ph % 1) - 1

# ---------------- drums ----------------
def kick(d=0.32):
    t = t_(d); f = 55 + 160 * np.exp(-t / 0.025)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.0005, 0.09)
    click = hp(rng.standard_normal(len(t)), 3000) * env(len(t), 0.0003, 0.004) * 0.5
    return np.tanh((s + click) * 3.0) * 0.8

def eight08(f0, d, glide_to=None):
    t = t_(d)
    f = np.full(len(t), f0)
    if glide_to:  # classic 808 slide in the last third
        k = int(len(t) * 0.55)
        f[k:] = f0 * (glide_to / f0) ** np.linspace(0, 1, len(t) - k) ** 0.6
    f = f * (1 + 0.6 * np.exp(-t / 0.012))  # pitch punch
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    e = np.minimum(t / 0.002, 1) * np.exp(-t / (d * 0.55))
    s = np.tanh(s * e * 2.6)  # saturation -> audible on phones
    return lp(s, 1800) * 0.95

def clap(d=0.4):
    t = t_(d)
    nz = bp(rng.standard_normal(len(t)), 900, 7000)
    e = np.zeros(len(t))
    for o in (0.0, 0.011, 0.022):  # three-slap clap
        i = int(o * SR); e[i:] += env(len(t) - i, 0.0005, 0.010 if o < 0.02 else 0.14)
    body = np.sin(2 * np.pi * 210 * t) * env(len(t), 0.001, 0.04)
    return np.tanh((nz * e * 1.6 + body * 0.6) * 1.8) * 0.8

def hat(open_=False):
    t = t_(0.4 if open_ else 0.06)
    return hp(rng.standard_normal(len(t)), 8000, 4) * env(len(t), 0.0003, 0.12 if open_ else 0.014) * 0.33

def march_snare():
    t = t_(0.18)
    nz = bp(rng.standard_normal(len(t)), 1800, 9000) * env(len(t), 0.0005, 0.05)
    body = np.sin(2 * np.pi * 240 * t) * env(len(t), 0.0005, 0.025)
    return np.tanh((nz * 1.2 + body * 0.7) * 1.6) * 0.5

def crash(d=2.8):
    t = t_(d)
    return hp(rng.standard_normal(len(t)), 4500, 2) * env(len(t), 0.002, 0.9) * 0.38

def impact(d=3.0):
    t = t_(d); f = 32 + 80 * np.exp(-t / 0.10)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.002, 0.8)
    nz = lp(rng.standard_normal(len(t)), 2200) * env(len(t), 0.001, 0.25)
    return np.tanh((boom * 1.7 + nz * 0.7) * 2.0) * 0.9

def riser(d, lo=600, hi=7000, g=0.3):
    n = int(d * SR)
    return bp(rng.standard_normal(n), lo, hi) * np.linspace(0, 1, n) ** 2.6 * g

# ---------------- tonal (A harmonic minor: war colour) ----------------
A1, F1, G1, E1 = 55.0, 43.65, 49.0, 41.2
def note(n): return 440.0 * 2 ** ((n - 69) / 12)  # midi -> Hz

def brass(midis, d, bright=1800, g=0.18):
    """Dark synth-brass stab: detuned saws, slow-ish attack, lowpassed."""
    s = 0
    for m in midis:
        for dt in (0.994, 1.0, 1.006):
            s = s + osc_saw(note(m) * dt, d)
    t = t_(d)
    e = np.minimum(t / 0.035, 1) * np.exp(-t / (d * 0.5))
    s = lp(np.tanh(s * 0.6), bright, 4) * e
    return s * g

def bell(m, d=1.6, g=0.16):
    t = t_(d); f = note(m)
    s = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) + 0.2 * np.sin(2 * np.pi * f * 5.4 * t))
    return s * env(len(t), 0.002, 0.45) * g

def pad(f, d, g=0.22):
    t = t_(d)
    s = lp(osc_saw(f, d) + osc_saw(f * 1.5, d) * 0.5 + osc_saw(f * 2.003, d) * 0.4, 600)
    return s * np.minimum(t / 1.2, 1) * g

# ---------------- intro: drone + marching snare + bell motif ----------------
add(pad(A1 * 2, CARD + 0.4), 0.0, 1.0)
add(pad(A1, CARD + 0.4, 0.15), 0.0)
step = BEAT / 4
for i, b in enumerate(np.arange(0.4, CARD - 0.05, step)):
    prog = (b - 0.4) / (CARD - 0.4)
    accent = 1.0 if i % 4 == 0 else 0.55
    add(march_snare(), b, (0.15 + 0.7 * prog ** 1.6) * accent, pan=0.15)
for k, m in enumerate([69, 72, 71, 68]):  # A C B G#  (harmonic minor)
    add(bell(m), 0.4 + k * BAR / 2, 1.0, pan=-0.2)
add(riser(2.2), CARD - 2.2)

# ---------------- card: impact ----------------
add(impact(3.0), CARD, 1.0)
add(brass([45, 52, 57], 1.4, 1500, 0.30), CARD, 1.0)
add(riser(0.5, 400, 9000, 0.45), DROP - 0.5)

# ---------------- trap groove ----------------
prog = [A1, A1, F1, E1]                       # 808 root per bar
brass_ch = [[57, 60, 64], [57, 60, 64], [53, 57, 60], [52, 56, 59]]  # Am Am F E (E major = harmonic minor V)
# 808/kick pattern per bar, in 16ths (0..15): classic bounce
K808 = [0, 3, 6, 10, 11]
HAT_ROLL_BARS = {1, 3}                        # triplet / 32nd rolls at the end of these bars (mod 4)

bars = np.arange(DROP, END - 1e-6, BAR)
for bi, b0 in enumerate(bars):
    root, chord = prog[bi % 4], brass_ch[bi % 4]
    hot = b0 >= LAUNCH - 1e-6
    for s16 in range(16):
        t = b0 + s16 * BEAT / 4
        if t >= END: break
        drums_on = not (DROPOUT <= t < WAKE)
        # 808 + kick
        if s16 in K808:
            nxt = [x for x in K808 if x > s16] + [16]
            dur = (nxt[0] - s16) * BEAT / 4 + 0.05
            glide = prog[(bi + 1) % 4] if (s16 == 11 and bi % 4 == 3) else None
            add(eight08(root, max(dur, 0.25), glide), t, 1.0)
            if drums_on: add(kick(), t, 0.85)
        if not drums_on:
            continue
        # clap on beat 3 (half-time)
        if s16 == 8: add(clap(), t, 1.0)
        # hats: 8ths, 16ths once hot; rolls at end of bars
        roll = (bi % 4) in HAT_ROLL_BARS and s16 >= 12
        if roll:
            if s16 in (12, 13):  # triplet 16ths
                for k in range(3): add(hat(), t + k * BEAT / 6, 0.7, pan=0.3)
            else:                # 32nds
                for k in range(2): add(hat(), t + k * BEAT / 8, 0.55 + 0.1 * k, pan=0.3)
        elif hot or s16 % 2 == 0:
            add(hat(open_=(s16 == 14 and bi % 2 == 0)), t, 0.75 if s16 % 2 == 0 else 0.45, pan=0.3)
    # brass stab on the bar, answer on the "and" of 2 once hot
    add(brass(chord, BAR * 0.45), b0, 1.0, pan=-0.2)
    if hot:
        add(brass([c + 12 for c in chord[:2]], BEAT * 0.6, 2200, 0.12), b0 + BEAT * 1.5, 1.0, pan=0.25)
    # bell counter-line in the first section
    if not hot and bi % 2 == 1:
        add(bell(chord[-1] + 12, 1.0, 0.10), b0 + BEAT * 2, 1.0, pan=-0.3)

# launch build + logo
add(riser(1.6, 800, 8000, 0.28), LAUNCH - 1.6)
add(crash(), LAUNCH, 0.8, pan=-0.3)
add(crash(), LOGO, 1.0, pan=0.3)
add(impact(1.6), LOGO, 0.5)
add(brass([45, 52, 57, 64], 1.2, 2400, 0.22), LOGO, 1.0)

# dropout + wake-up slam
add(riser(WAKE - DROPOUT, 500, 6000, 0.25), DROPOUT)
add(impact(2.0), WAKE, 1.0)
add(crash(2.5), WAKE, 1.0, pan=-0.2)
add(brass([45, 52, 57, 60], 1.4, 2600, 0.30), WAKE, 1.0)

# snare roll into the end card (marching, accelerating)
roll_t = END - 1.2
k = 0
while roll_t < END - 0.02:
    add(march_snare(), roll_t, 0.35 + 0.5 * (1 - (END - roll_t) / 1.2), pan=0.1)
    roll_t += max(BEAT / 8, BEAT / 3 * (END - roll_t) / 1.2); k += 1

# ---------------- end card ----------------
add(impact(4.0), END, 1.15)
add(crash(4.0), END, 1.0)
add(eight08(A1, 3.5), END, 1.1)
add(brass([45, 52, 57, 60, 64], 3.0, 2200, 0.32), END, 1.0)
add(bell(81, 2.5, 0.14), END + 0.9, 1.0)
add(kick(), END + 2.4, 0.8); add(eight08(A1, 2.4), END + 2.4, 0.9)

# master: glue + soft clip + fade
mix = np.tanh(mix * 0.95) * 0.88
fade = int(1.2 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
mix /= np.max(np.abs(mix)) / 0.89
sf.write(sys.argv[1], mix.astype(np.float32), SR, subtype="PCM_24")
print("wrote", sys.argv[1], "END", round(END, 2), "WAKE", round(WAKE, 2))
