"""Sound design for the outro: riser -> cinematic impact -> metallic tail.

Usage: python3 audio.py out.wav
The voice-over slot is 1.70s–3.20s; the bed is ducked there so the VO sits on top.
"""
import sys
import wave

import numpy as np

SR, DUR = 48000, 4.0
N = int(SR * DUR)
T_IMPACT = 1.60
t = np.arange(N) / SR
rng = np.random.default_rng(3)


def env(x, a, b):
    return np.clip((x - a) / (b - a), 0, 1)


def onepole_lp(x, fc):
    """Time-varying one-pole lowpass; fc can be an array."""
    fc = np.broadcast_to(fc, x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def fft_conv(x, ir):
    n = len(x) + len(ir)
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[:len(x)]


# --- riser: filtered noise swell + rising tone
p = env(t, 0.15, T_IMPACT)
noise = rng.normal(0, 1, N)
riser = onepole_lp(noise, 200 + 7000 * p ** 2.2) - onepole_lp(noise, 80 + 900 * p ** 2)
riser *= (p ** 2.4) * (t < T_IMPACT + 0.02) * 0.9
tone_f = 90 + 260 * p ** 2
tone = np.sin(2 * np.pi * np.cumsum(tone_f) / SR) * (p ** 3) * (t < T_IMPACT) * 0.18

# --- reverse-swell "suck" right before the hit
suck = onepole_lp(rng.normal(0, 1, N), 2500) * env(t, T_IMPACT - 0.35, T_IMPACT) ** 3 * (t < T_IMPACT) * 0.8

# --- impact
h = np.maximum(t - T_IMPACT, 0)
on = (t >= T_IMPACT).astype(float)
boom_f = 32 + 70 * np.exp(-h * 18)
boom = np.sin(2 * np.pi * np.cumsum(boom_f * on) / SR) * np.exp(-h * 2.6) * on * 1.0
crack = onepole_lp(rng.normal(0, 1, N), 6000) * np.exp(-h * 38) * on * 0.9
body = onepole_lp(rng.normal(0, 1, N), 400) * np.exp(-h * 9) * on * 1.6
# metallic ring: inharmonic partials
ring = np.zeros(N)
for f, a, d in [(196, 0.5, 1.6), (311, 0.35, 2.0), (523, 0.25, 2.6), (742, 0.18, 3.2),
                (1043, 0.12, 4.0), (1567, 0.07, 5.0)]:
    ring += a * np.sin(2 * np.pi * f * h + rng.uniform(0, 6)) * np.exp(-h * d)
ring *= on * 0.28

# --- low drone pad under everything
pad = (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t + 1) + 0.3 * np.sin(2 * np.pi * 110.3 * t))
pad *= (0.04 + 0.10 * env(t, T_IMPACT, T_IMPACT + 0.3)) * env(t, 0, 0.6) * 0.6

dry = riser + tone + suck + boom + crack + body + ring + pad

# --- stereo + reverb
ir_len = int(SR * 2.2)
irt = np.arange(ir_len) / SR
irL = rng.normal(0, 1, ir_len) * np.exp(-irt * 3.0)
irR = rng.normal(0, 1, ir_len) * np.exp(-irt * 3.0)
irL[:int(0.012 * SR)] = 0
irR[:int(0.017 * SR)] = 0
wet_src = crack + body + ring + tone + riser * 0.5
L = dry + fft_conv(wet_src, irL) * 0.035
R = dry + fft_conv(wet_src, irR) * 0.035
# subtle stereo movement on the riser
pan = 0.5 + 0.35 * np.sin(2 * np.pi * 0.9 * t)
L += riser * (1 - pan) * 0.3
R += riser * pan * 0.3

# duck the bed under the VO slot, fade out at the end
duck = 1 - 0.45 * (env(t, 1.65, 1.8) - env(t, 3.1, 3.4))
fade = 1 - env(t, 3.55, 4.0) ** 1.5
st = np.stack([L, R], 1) * (duck * fade)[:, None]
st = np.tanh(st / np.abs(st).max() * 1.6) / np.tanh(1.6) * 0.89   # soft-clip, ~-1 dBFS

with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((st * 32767).astype("<i2").tobytes())
