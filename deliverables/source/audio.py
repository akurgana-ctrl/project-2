"""Dialogue edit + music mix -> mix.wav (40s). python3 audio.py <scratch>"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import timeline
from edl import TOTAL

S = sys.argv[1]
_, audio, _, _ = timeline()
inputs, chains, labels = [], [], []
for i, (clip, a, dur, at) in enumerate(audio):
    inputs += ["-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", f"{S}/raw/{clip}.mp4"]
    chains.append(f"[{i}:a:0]pan=mono|c0=0.5*c0+0.5*c1,aresample=48000,"
                  f"afade=t=in:d=0.012,afade=t=out:st={dur-0.02:.3f}:d=0.02,"
                  f"adelay={int(at*1000)}|{int(at*1000)}[s{i}]")
    labels.append(f"[s{i}]")
m = len(audio)
fc = ";".join(chains) + ";" + "".join(labels) + (
    f"amix=inputs={m}:normalize=0,apad,atrim=0:{TOTAL},"
    "highpass=f=85,afftdn=nf=-30,"
    "equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=3.5,equalizer=f=9000:t=h:w=0.7:g=2,"
    "acompressor=threshold=-22dB:ratio=4:attack=4:release=90:makeup=6dB,"
    "loudnorm=I=-16:TP=-2:LRA=7,asplit[voice][k0];[k0]apad,atrim=0:40[key];"
    f"[{m}:a]volume=-6dB,apad,atrim=0:{TOTAL}[mus];"
    "[mus][key]sidechaincompress=threshold=0.04:ratio=3.5:attack=8:release=260:makeup=1[duck];"
    "[voice][duck]amix=inputs=2:normalize=0:duration=longest,apad,atrim=0:40,alimiter=limit=0.89:attack=3:release=60,"
    "loudnorm=I=-14:TP=-1:LRA=9[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-i", f"{S}/music.wav",
                "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-ac", "2",
                f"{S}/mix.wav"], check=True)
print("mix ok")
