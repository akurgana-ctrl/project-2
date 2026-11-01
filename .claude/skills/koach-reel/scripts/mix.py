"""Final mix: voice + weapon trap beat (ducked, automated) + weapon SFX hits. usage: mix.py <scratch> <total>"""
import sys, os, json, wave, subprocess, numpy as np
S, TOTAL = sys.argv[1], float(sys.argv[2])
HOOK = 3.17                       # beat drops when the hook ends
os.environ["BEAT_DUR"] = str(TOTAL - HOOK + 0.5)
sys.path.insert(0, os.path.dirname(__file__))
import beat as B
SR = 48000; N = int(SR * TOTAL)

def readwav(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = a.reshape(-1, w.getnchannels()); return a if a.shape[1] == 2 else np.repeat(a, 2, 1)

voice = np.zeros((N, 2)); v = readwav(f"{S}/voice.wav")[:N]; voice[:len(v)] = v
rms_v = np.sqrt(np.mean(voice[voice[:, 0] != 0] ** 2))
voice *= 0.12 / rms_v                        # voice RMS ~ -18 dBFS

music = np.zeros((N, 2)); m = B.build(); i = int(HOOK * SR); music[i:i + len(m)] = m[:N - i]
music *= 0.12 / np.sqrt(np.mean(m ** 2)) * 10 ** (-17.5 / 20)   # ~17.5 dB under the voice

# automation (output seconds): silence for "לפי מה שוללים?", swell on the CTA, out with the end card
t = np.arange(N) / SR
g = np.ones(N)
def ramp(t0, t1, a, b):
    sel = (t >= t0) & (t < t1); g[sel] = a + (b - a) * (t[sel] - t0) / (t1 - t0)
ramp(35.55, 35.75, 1, 0); g[(t >= 35.75) & (t < 36.95)] = 0; ramp(36.95, 37.0, 0, 1)
ramp(58.9, TOTAL, 1, 0)
music *= g[:, None]

sfx = np.zeros((N, 2))
def hit(sig, at, gain):
    j = int(at * SR); s = sig[: N - j] * gain; sfx[j:j + len(s)] += s[:, None]
SHOT = B.shot(); COCK = B.gun_cock()
_t = B.war_tom(55); _k = B.kick(); boom = _t.copy(); boom[:len(_k)] += _k * 0.8
hit(SHOT, 0.02, 0.55)          # hook: "פוף!"
hit(COCK, 2.95, 0.5)           # cock into the drop
hit(boom, 10.45, 0.6)          # 2,600
hit(COCK, 18.05, 0.45)         # ship scene
hit(SHOT, 28.52, 0.5)          # "פוף!" in the body
hit(boom, 36.95, 0.55)         # back in after the question
hit(boom, 45.35, 0.55)         # "והגשנו שתי עתירות" (gavel)
hit(COCK, 53.0, 0.4)           # CTA
hit(SHOT, 58.85, 0.45)         # end card
sfx *= 0.12 * 10 ** (-9 / 20) / 0.3

mix = voice + music + sfx
mix = np.tanh(mix * 1.2) / 1.2
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
with wave.open(f"{S}/mix_raw.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
# two-pass loudnorm to -14 LUFS / -1.5 dBTP
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{S}/mix_raw.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                    "-f", "null", "-"], capture_output=True, text=True).stderr
js = json.loads(r[r.rindex("{"):])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
      f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{S}/mix_raw.wav", "-af", af, "-ar", "48000",
                f"{S}/tamir/assets/mix.wav"], check=True)
print("mix ok", js["input_i"])
