# Real-sound mix for the explainer: CC0 effects from sfx-kit, a CC BY music track from Openverse (Jamendo), the narration.
# usage: python mix_real.py <project dir> <sfx-kit dir> <music file> <music peak s> <film hit s>
# The CUES list below is the example film's (תיק שלו): rewrite it for each film from its window.EV / scene times.
import json, os, sys, subprocess
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
from scipy.ndimage import uniform_filter1d

HERE, KIT, MUSIC = sys.argv[1], sys.argv[2], sys.argv[3]
PEAK, HIT = float(sys.argv[4]), float(sys.argv[5])
SR = 48000
DUR = json.load(open(os.path.join(HERE, 'events.json')))['dur']
N = int(DUR * SR)
db = lambda x: 10 ** (x / 20)

def load(path, offset=0.0, dur=None):
    """any file → float stereo @48k via ffmpeg"""
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(offset)] + (['-t', str(dur)] if dur else []) + ['-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).reshape(-1, 2).astype(float)

# ---------- sfx-kit ----------
kit = {s['id']: s for s in json.load(open(os.path.join(KIT, 'sounds.json')))['sounds']}
SFX = np.zeros((N, 2)); used = set()
def place(sid, t, gain_db=0.0, pan=0.0):
    s = kit[sid]; used.add(sid)
    x = load(os.path.join(KIT, s['file']))
    start = t - s['sync']['at']                      # the sync point meets the picture
    i = int(round(start * SR))
    if i < 0: x = x[-i:]; i = 0
    x = x[: max(0, N - i)] * db(gain_db)
    l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
    SFX[i:i + len(x), 0] += x[:, 0] * l; SFX[i:i + len(x), 1] += x[:, 1] * r

CUES = [
    # 1. the appeal flies into the Knesset
    ('pop-large-in', 0.05, 0), ('whoosh-medium-soft', 0.80, -2), ('foley-paper-touch', 1.25, 0), ('impact-medium-firm', 1.26, -4), ('pop-medium-in', 1.70, -2),
    # 2. the MK, the pin, the passports
    ('move-spring', 2.70, -2), ('pop-medium-in', 2.65, -3), ('tone-ding-mid', 3.10, -6), ('pop-small-in', 3.35, -3),
    ('foley-card-slide', 4.25, -1, -0.5), ('foley-card-slide', 4.50, -1, 0.5),
    # 3. the law: banner, three rows, three question marks, the seat, the X, the ruling
    ('whoosh-fast-soft', 4.87, -3), ('pop-large-in', 5.10, -2), ('writing-marker-write', 5.55, -6),
    ('foley-card-slide', 6.25, -3), ('foley-card-slide', 6.70, -3), ('foley-card-slide', 7.15, -3),
    ('tone-step-1', 7.47, -5), ('tone-step-2', 7.65, -5), ('tone-step-3', 7.83, -5),
    ('whoosh-medium-medium', 8.90, -4), ('impact-heavy-firm', 9.30, -2), ('impact-deep-hard', 9.20, 0), ('pop-large-in', 9.35, -3),
    # 4. the plenary vote: boxes land, ballots drop, his bounces back
    ('whoosh-fast-soft', 11.08, -3), ('impact-light-firm', 11.45, -3), ('impact-light-firm', 11.52, -3, 0.3), ('impact-light-firm', 11.59, -3, -0.3), ('impact-light-firm', 11.66, -3),
    ('foley-card-touch', 12.00, -2, -0.6), ('foley-card-touch', 12.12, -2, -0.2), ('foley-card-touch', 12.36, -2, 0.6),
    ('move-bounce', 12.45, 0, 0.3), ('notification-error' if 'notification-error' in kit else 'tone-ding-low', 12.40, -4), ('pop-large-in', 12.55, -2),
    # 5. the hand and the sheet
    ('whoosh-medium-soft', 12.95, -3), ('reverse-whoosh-medium-strong', 14.20, -3), ('foley-fabric-slide', 14.30, 0), ('impact-heavy-soft', 14.45, 0),
    ('boom-hit-soft', 14.30, -4), ('pop-large-in', 14.40, -2), ('whoosh-slow-soft', 14.75, -6),
    # 6. the search, the signs, the crowd
    ('whoosh-fast-soft', 15.67, -3), ('appear-flip-quick', 15.95, -3), ('foley-glass-slide', 16.10, -6), ('foley-glass-slide', 16.60, -7),
    ('pop-medium-in', 17.20, -2), ('pop-medium-in', 17.32, -2), ('pop-medium-in', 17.44, -2), ('celebration-applause-small', 17.10, -10),
    # 7. the verdict: riser into a silence, then the lock and the slam
    ('whoosh-fast-soft', 17.98, -3), ('pop-large-in', 18.20, -1), ('impact-heavy-firm', 18.65, -3), ('riser-1s-strong', 19.03, -6),
    ('cinematic-slam-big', 19.36, 0), ('mechanical-lock-heavy', 19.42, -2), ('boom-hit-strong', 19.36, -3),
    # 8. end card
    ('whoosh-medium-medium', 20.30, -3), ('sting-bold-short', 20.62, -2), ('pop-medium-in', 21.10, -3), ('pop-large-in', 21.95, -2),
]
for c in CUES:
    sid, t, g = c[0], c[1], c[2]; pan = c[3] if len(c) > 3 else 0.0
    if sid not in kit: print('missing', sid); continue
    place(sid, t, g, pan)

# ---------- music (Openverse / Jamendo, CC BY 3.0) ----------
OFF = PEAK - HIT               # the track's peak beat lands on the film's biggest hit
M = load(MUSIC, OFF, DUR)
M = np.vstack([M, np.zeros((max(0, N - len(M)), 2))])[:N]
fi = int(0.4 * SR); M[:fi] *= np.linspace(0, 1, fi)[:, None]

# ---------- voice ----------
v, vsr = sf.read(os.path.join(HERE, 'assets/voice.wav'))
assert vsr == SR
v = sosfilt(butter(2, 80, 'high', fs=SR, output='sos'), v)
env = uniform_filter1d(np.abs(v), int(0.01 * SR)); thr = 0.12
v = v * np.where(env > thr, (thr + (env - thr) / 3) / np.maximum(env, 1e-9), 1.0)
V = np.zeros((N, 2)); n = min(len(v), N); V[:n, 0] = v[:n]; V[:n, 1] = v[:n]

rms = lambda x: np.sqrt(np.mean(x ** 2) + 1e-12)
vr = rms(V[:n, 0])
M *= vr / (rms(M[:int(20.3 * SR)]) + 1e-9) * db(-9)                     # bed 9 dB under the voice
act = uniform_filter1d((np.abs(V[:, 0]) > 0.02).astype(float), int(0.3 * SR))
duck = 1 - 0.30 * np.clip(act * 3, 0, 1)                                # ~3 dB more while he speaks
t = np.arange(N) / SR
gate = np.where((t >= 19.05) & (t < 19.33), 0.0, 1.0)                   # the silence before the stamp
gate = uniform_filter1d(gate, int(0.02 * SR))
lift = 1 + (db(7) - 1) * np.clip((t - 20.25) / 0.2, 0, 1)               # music up on the end card
M *= (duck * gate * lift)[:, None]
SFX *= vr / (rms(SFX[np.abs(SFX[:, 0]) > 1e-4]) + 1e-9) * db(-4)        # effects sit just under the voice

def widen(x, k):
    mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2 * k
    return np.stack([mid + side, mid - side], 1)
M = widen(M, 2.2); SFX = widen(SFX, 1.8)
mix = V + M + SFX
fo = int(0.9 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.3) * 0.9
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
sf.write(os.path.join(HERE, 'out/mix.wav'), mix, SR, subtype='PCM_16')
sf.write(os.path.join(HERE, 'out/stem_music.wav'), M, SR, subtype='PCM_16')
sf.write(os.path.join(HERE, 'out/stem_sfx.wav'), SFX / (np.abs(SFX).max() + 1e-9) * 0.9, SR, subtype='PCM_16')
json.dump(sorted(used), open(os.path.join(HERE, 'out/sfx_used.json'), 'w'), indent=1)
print('mix', DUR, 's ·', len(used), 'sfx-kit sounds')
