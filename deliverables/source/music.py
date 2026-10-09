"""Original score: dark intro -> impact -> gritty rock groove -> final slam.
Cue points come from the edit timeline so hits land on cuts."""
import sys
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 48000
TOTAL = 40.0
CARD, DROP, LAUNCH, LOGO, END = 4.72, 5.68, 16.20, 18.60, 34.32
BEAT = 0.5  # 120 BPM, beat 1 lands on DROP
rng = np.random.default_rng(7)
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
    i = int(at * SR)
    if i >= N: return
    sig = sig[: N - i]
    if sig.ndim == 1:
        l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
    mix[i:i + len(sig)] += sig * gain
def saw(f, d):
    t = t_(d); ph = np.cumsum(np.broadcast_to(f, t.shape)) / SR
    return 2 * (ph % 1) - 1

# --- drums -------------------------------------------------------------
def kick(d=0.45, punch=1.0):
    t = t_(d); f = 48 + 140 * np.exp(-t / 0.035)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.16)
    click = hp(rng.standard_normal(len(t)), 2000) * env(len(t), 0.0005, 0.006) * 0.4
    return np.tanh((s + click) * 2.5 * punch) * 0.9
def snare(d=0.35):
    t = t_(d)
    body = np.sin(2 * np.pi * 190 * t) * env(len(t), 0.001, 0.05)
    nz = bp(rng.standard_normal(len(t)), 1500, 9000) * env(len(t), 0.001, 0.11)
    return np.tanh((body * 0.8 + nz * 1.4) * 2.2) * 0.75
def hat(d=0.08, open_=False):
    t = t_(0.35 if open_ else d)
    return hp(rng.standard_normal(len(t)), 7000, 4) * env(len(t), 0.0005, 0.12 if open_ else 0.018) * 0.35
def crash(d=2.5):
    t = t_(d)
    return hp(rng.standard_normal(len(t)), 4000, 2) * env(len(t), 0.002, 0.9) * 0.45

# --- tonal -------------------------------------------------------------
A1, F1, G1, C2 = 55.0, 43.65, 49.0, 65.41
def bass_note(f, d):
    s = saw(f, d) + 0.5 * saw(f * 1.005, d)
    s = np.tanh(lp(s, 900) * 3.0)
    return lp(s, 1400) * env(len(s), 0.004, d * 0.9) * 0.55
def power_chord(f, d, bright=3200):
    s = sum(saw(f * m * dt, d) for m in (2, 3, 4) for dt in (0.997, 1.0, 1.004))
    s = np.tanh(hp(s, 120) * 4.0)
    return lp(s, bright, 4) * env(len(s), 0.006, d * 0.6) * 0.22
def impact(d=3.0):
    t = t_(d); f = 30 + 70 * np.exp(-t / 0.12)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.002, 0.9)
    nz = lp(rng.standard_normal(len(t)), 1800) * env(len(t), 0.001, 0.35)
    return np.tanh((boom * 1.6 + nz * 0.6) * 2.0) * 0.9

# --- intro: drone + heartbeat + riser ---------------------------------
d = CARD
t = t_(d)
drone = lp(saw(A1, d) + saw(A1 * 1.01, d), 220) * np.minimum(t / 1.5, 1) * 0.30
add(drone, 0.0)
for b in np.arange(0.0, CARD - 0.2, 1.0):
    add(kick(0.5, 0.6), b, 0.55); add(kick(0.4, 0.5), b + 0.22, 0.30)
rd = 2.4
riser = bp(rng.standard_normal(int(rd * SR)), 800, 6000) * np.linspace(0, 1, int(rd * SR)) ** 2.5 * 0.35
add(riser, CARD - rd)

# --- card: impact, then reverse swell into the drop ----------------------
add(impact(3.0), CARD, 1.0)
add(power_chord(A1, 1.0, 2400), CARD, 0.9)
sw = 0.55
rev = bp(rng.standard_normal(int(sw * SR)), 500, 8000) * np.linspace(0, 1, int(sw * SR)) ** 3 * 0.5
add(rev, DROP - sw)

# --- groove ------------------------------------------------------------
prog = [A1, A1, F1, G1]  # one chord per bar (4 beats)
beats = np.arange(DROP, END - 1e-6, BEAT)
for i, b in enumerate(beats):
    bar, pos = divmod(i, 4)
    root = prog[bar % 4]
    hot = b >= LAUNCH
    # kick: 1, 3, and-of-3 ; snare: 2, 4
    if pos in (0, 2): add(kick(), b, 1.0)
    if pos == 2: add(kick(0.3, 0.8), b + BEAT / 2, 0.6)
    if pos in (1, 3): add(snare(), b, 0.9)
    # hats: 8ths, 16ths once launched
    for k in range(4 if hot else 2):
        add(hat(open_=(hot and k == 2 and pos == 3)), b + k * BEAT / (4 if hot else 2),
            0.8 if k % 2 == 0 else 0.5, pan=0.3)
    # bass 8ths
    for k in range(2):
        add(bass_note(root, BEAT / 2 * 0.95), b + k * BEAT / 2, 1.0)
    # guitar stab on each bar downbeat (+ push on the and-of-4 once hot)
    if pos == 0: add(power_chord(root, BEAT * 3.6), b, 1.0, pan=-0.25)
    if hot and pos == 3: add(power_chord(prog[(bar + 1) % 4], BEAT * 0.5), b + BEAT / 2, 0.7, pan=0.25)

# launch build + logo crash
rd = 1.6
riser = bp(rng.standard_normal(int(rd * SR)), 1000, 7000) * np.linspace(0, 1, int(rd * SR)) ** 2 * 0.25
add(riser, LAUNCH - rd)
add(crash(), LAUNCH, 0.8, pan=-0.3)
add(crash(), LOGO, 1.0, pan=0.3)
add(impact(1.5), LOGO, 0.45)
# snare fill into the end card
for k in range(8):
    add(snare(0.2), END - 1.0 + k * 0.125, 0.45 + k * 0.06)

# --- end card ------------------------------------------------------------
add(impact(4.0), END, 1.1)
add(crash(4.0), END, 1.0)
add(power_chord(A1, 5.5, 2800), END, 1.4)
tail = END + 2.0
add(kick(0.6), tail, 0.8); add(power_chord(A1, 3.5, 2000), tail, 0.9)

# master: glue + fade
mix = np.tanh(mix * 0.9) * 0.85
fade = int(1.2 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
mix /= np.max(np.abs(mix)) / 0.89
sf.write(sys.argv[1], mix.astype(np.float32), SR, subtype="PCM_24")
print("wrote", sys.argv[1])
