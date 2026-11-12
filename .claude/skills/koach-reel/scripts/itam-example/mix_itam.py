"""Mix for the MK Itam reel: voice + MusicGen epic bed + medal clinks / booms. usage: mix_itam.py <scratch> <total> <music.wav>"""
import sys, os, json, wave, subprocess, numpy as np
S, TOTAL, MUS = sys.argv[1], float(sys.argv[2]), sys.argv[3]
os.environ["BEAT_DUR"] = "2"
sys.path.insert(0, os.path.dirname(__file__))
import beat as B
SR = 48000; N = int(SR * TOTAL); D = f"{S}/itam"

def load(p):
    tmp = f"{D}/_tmp48.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-ar", str(SR), "-ac", "2", tmp], check=True)
    w = wave.open(tmp); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a.reshape(-1, 2)
def fit(a):
    z = np.zeros((N, 2)); z[:min(N, len(a))] = a[:N]; return z

voice = fit(load(f"{D}/voice.wav")); voice *= 0.12 / np.sqrt(np.mean(voice[np.abs(voice[:, 0]) > 1e-4] ** 2))
music = fit(load(MUS)); music *= 0.12 / np.sqrt(np.mean(music ** 2) + 1e-9) * 10 ** (-16 / 20)   # bed ~16 dB under voice
t = np.arange(N) / SR; g = np.ones(N)
g *= np.clip(t / 0.4, 0, 1)                                   # quick fade-in
g[t >= 36.2] *= 1.0 + 0.6 * np.clip((t[t >= 36.2] - 36.2) / 0.4, 0, 1)   # swell into the climax
g *= np.clip((TOTAL - t) / 0.5, 0, 1)                         # fade out
music *= g[:, None]

sfx = np.zeros((N, 2))
def hit(sig, at, gain):
    j = int(at * SR); s = sig[: N - j] * gain; sfx[j:j + len(s)] += s[:, None]
def clink(f0):
    n = int(SR * 0.9); tt = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * f0 * k * tt) * np.exp(-tt / (0.35 / k)) / k for k in (1, 2.76, 5.4)) * 0.5
_t = B.war_tom(52); _k = B.kick(); boom = _t.copy(); boom[:len(_k)] += _k * 0.8
hit(boom, 0.04, 0.5)                                          # hook
hit(clink(1480), 7.65, 0.45)                                  # Israeli medal (bill)
hit(boom, 16.75, 0.45)                                        # "גיבורים"
for k, at in enumerate((33.5, 33.85, 34.2, 34.9)): hit(clink(1400 + 140 * k), at, 0.35)
hit(boom, 36.25, 0.7)                                         # Israel slot fills
sfx *= 0.12 * 10 ** (-10 / 20) / 0.3

mix = np.tanh((voice + music + sfx) * 1.15) / 1.15
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
with wave.open(f"{D}/mix_raw.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{D}/mix_raw.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
js = json.loads(r[r.rindex("{"):])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
      f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{D}/mix_raw.wav", "-af", af, "-ar", "48000", f"{D}/proj/assets/mix.wav"], check=True)
print("mix ok")
