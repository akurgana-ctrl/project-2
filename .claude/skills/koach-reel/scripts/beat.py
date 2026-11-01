"""Synthesized combative trap beat with weapon foley (no samples, fully original).
usage: python3 beat.py <out.wav> <seconds>"""
import sys, numpy as np, wave

SR = 48000
import os
out, DUR = (sys.argv[1], float(sys.argv[2])) if __name__=="__main__" else (None, float(os.environ.get("BEAT_DUR","60")))
rng = np.random.default_rng(7)
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)

def env(n, a, d):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-t / d)
    return e

def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    s = sig[: N - i] * gain
    L[i:i+len(s)] += s * (1 - max(pan, 0))
    R[i:i+len(s)] += s * (1 + min(pan, 0))

def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1/SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))

# --- weapon foley ---
def click(freq, dur=0.05):
    n = int(SR*dur); t = np.arange(n)/SR
    metal = sum(np.sin(2*np.pi*freq*k*t + rng.random()*6) / k for k in (1, 2.76, 5.4, 8.9))
    return (metal * 0.5 + bp(rng.standard_normal(n), 2000, 9000) * 0.8) * env(n, 0.0005, dur/5)

def gun_cock():  # slide back + slam forward
    a = click(1800, 0.06); b = click(1300, 0.09)
    gap = int(SR*0.11); s = np.zeros(gap + len(b))
    s[:len(a)] += a * 0.7; s[gap:] += b
    return s

def shell(freq):  # brass casing tinkle
    n = int(SR*0.25); t = np.arange(n)/SR
    s = sum(np.sin(2*np.pi*freq*k*t) * np.exp(-t/(0.06/k)) for k in (1, 2.4, 3.9))
    return s * 0.25

def shot():  # muffled distant shot: noise crack + low boom
    n = int(SR*0.9); t = np.arange(n)/SR
    crack = bp(rng.standard_normal(n), 800, 7000) * env(n, 0.0003, 0.025)
    boom = np.sin(2*np.pi*(55 + 120*np.exp(-t/0.03))*t) * env(n, 0.001, 0.25)
    tail = bp(rng.standard_normal(n), 100, 900) * env(n, 0.01, 0.35) * 0.4
    return crack*0.6 + boom*1.0 + tail

# --- drums ---
def kick():
    n = int(SR*0.5); t = np.arange(n)/SR
    f = 48 + 110*np.exp(-t/0.04)
    return np.tanh(2.2*np.sin(2*np.pi*np.cumsum(f)/SR) * env(n, 0.001, 0.18))

def bass808(freq, dur):
    n = int(SR*dur); t = np.arange(n)/SR
    f = freq*(1 + 0.6*np.exp(-t/0.03))
    return np.tanh(1.8*np.sin(2*np.pi*np.cumsum(f)/SR)) * env(n, 0.003, dur*0.6)

def war_tom(freq):
    n = int(SR*0.6); t = np.arange(n)/SR
    f = freq*(1+0.5*np.exp(-t/0.05))
    return (np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,0.001,0.22)
            + bp(rng.standard_normal(n),150,1200)*env(n,0.001,0.04)*0.4)

def drone(n):
    t = np.arange(n)/SR
    s = sum(np.sin(2*np.pi*f*t + p) for f, p in ((36.7, 0), (55, 1), (73.4, 2)))  # D minor-ish pad
    lfo = 0.6 + 0.4*np.sin(2*np.pi*0.07*t)
    return s * lfo * 0.08

BPM = 140; beat = 60/BPM; bar = 4*beat
KICK = kick(); COCK = gun_cock(); SHOT = shot()
# D minor 808 line, one note per bar
roots = [36.7, 36.7, 43.65, 32.7]

def build():
  add(drone(N), 0, 1.0)
  nbars = int(DUR / bar) + 1
  for b in range(nbars):
      t0 = b*bar
      intro = b < 2
      # kicks: trap pattern on 8ths
      for k in ([0, 3.5] if intro else [0, 1.75, 2.5]):
          add(KICK, t0 + k*beat, 0.9)
      if not intro:
          add(bass808(roots[b % 4], bar*0.9), t0, 0.55)
      # snare = gun cock on beat 3 (half time)
      add(COCK, t0 + 2*beat - 0.11, 0.75, pan=0.1)
      # hats = shell casings, 16ths with rolls every 4th bar
      steps = 32 if (b % 4 == 3 and not intro) else 8
      for h in range(steps):
          frac = h/steps*4
          add(shell(3200 + 400*rng.random()), t0 + frac*beat, (0.35 if h % 2 == 0 else 0.22) * (0.5 if intro else 1), pan=0.35*np.sin(h))
      # war toms fill on bar ends
      if b % 4 == 3:
          for j, f in enumerate((110, 98, 82)):
              add(war_tom(f), t0 + (3 + j/3)*beat, 0.5, pan=-0.2+0.2*j)
      # shot accent every 8 bars
      if b % 8 == 0 and b > 0:
          add(SHOT, t0, 0.7)

  mix = np.stack([L, R], 1)
  # fade out last 1.5 s
  fo = int(SR*1.5); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
  mix = np.tanh(mix * 1.1)
  mix /= np.abs(mix).max() / 0.9
  pcm = (mix * 32767).astype(np.int16)
  return mix
  with wave.open(out, "wb") as w:
      w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
  print("ok", out, DUR)

if __name__=="__main__": build()
