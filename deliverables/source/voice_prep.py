"""Dialogue prep -> aud/voice_clean.wav (mono, 48k, on the edit timeline).
Per segment: speaker's own lav channel only (L/R are two different mics — summing them
comb-filters), DeepFilterNet3 denoise, then speech-level matching across segments."""
import os, sys, subprocess
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import timeline
from edl import TOTAL

S = sys.argv[1]
A = f"{S}/aud"; os.makedirs(A, exist_ok=True)
SR = 48000
CHANNEL = {"C047_KA": 1}  # bearded speaker wears the R-channel lav; everyone else speaks on L
ATTEN_DB = "28"           # cap the denoiser so the voice stays natural
TARGET_DB = -20.0         # speech-frame RMS target per segment
HANDLE = 0.25             # extra audio either side so the denoiser settles before the cut

_, audio, _, _ = timeline()
out = np.zeros(int(TOTAL * SR))
for i, (clip, a, dur, at) in enumerate(audio):
    ch = CHANNEL.get(clip, 0)
    pre = min(HANDLE, a)
    raw = f"{A}/v{i:02d}_raw.wav"; den = f"{A}/v{i:02d}_dn.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a - pre:.3f}", "-t", f"{dur + pre + HANDLE:.3f}",
                    "-i", f"{S}/raw/{clip}.mp4", "-map", "0:a:0", "-af", f"pan=mono|c0=c{ch}",
                    "-ar", str(SR), "-c:a", "pcm_s24le", raw], check=True)
    subprocess.run([sys.executable, "-I", f"{S}/dfn.py", raw, den, ATTEN_DB], check=True,
                   capture_output=True)
    y, _ = sf.read(den)
    y = y[int(pre * SR): int(pre * SR) + int(dur * SR)]
    # level match on speech frames (top 40% of 50ms frames)
    w = int(0.05 * SR)
    fr = np.array([np.sqrt(np.mean(y[k * w:(k + 1) * w] ** 2)) for k in range(len(y) // w)])
    speech = np.sqrt(np.mean(fr[fr >= np.percentile(fr, 60)] ** 2))
    y = y * 10 ** ((TARGET_DB - 20 * np.log10(speech + 1e-9)) / 20)
    # 12ms edge fades, then place on the timeline
    f = int(0.012 * SR)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    s = int(round(at * SR)); out[s:s + len(y)] += y[: len(out) - s]
    print(f"seg {i:2d} {clip} ch={'LR'[ch]} speech {20*np.log10(speech+1e-9):6.1f} dB -> {TARGET_DB}")
sf.write(f"{A}/voice_clean.wav", out.astype(np.float32), SR, subtype="PCM_24")
print("voice_clean ok")
