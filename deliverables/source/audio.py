"""Final mix: cleaned dialogue (voice_prep.py) + score -> mix.wav (40s). python3 audio.py <scratch>"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edl import TOTAL

S = sys.argv[1]
VOICE = (
    "highpass=f=80:poles=2,"
    # remove boxiness, add presence and air
    "equalizer=f=200:t=q:w=1.0:g=-3,equalizer=f=450:t=q:w=1.4:g=-1.5,"
    "equalizer=f=3200:t=q:w=1.0:g=3.5,equalizer=f=10000:t=h:w=0.7:g=2.5,"
    "deesser=i=0.35:m=0.5:f=0.5,"
    # level the delivery, then a fast stage for a dense broadcast voice
    "acompressor=threshold=-24dB:ratio=2.5:attack=8:release=150:makeup=4dB:knee=4,"
    "acompressor=threshold=-12dB:ratio=6:attack=1.5:release=60:makeup=2dB,"
    "loudnorm=I=-13:TP=-1.5:LRA=4"
)
fc = (
    f"[0:a]{VOICE},apad,atrim=0:{TOTAL},asplit=3[voice][k0][vst];[k0]apad,atrim=0:{TOTAL}[key];"
    f"[1:a]volume=-9dB,apad,atrim=0:{TOTAL}[mus];"
    # duck the beat under speech; it comes back between lines
    "[mus][key]sidechaincompress=threshold=0.03:ratio=6:attack=5:release=320:makeup=1,asplit[duck][mst];"
    f"[voice][duck]amix=inputs=2:normalize=0:duration=longest,apad,atrim=0:{TOTAL},"
    "alimiter=limit=0.89:attack=3:release=60[out]"
)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{S}/aud/voice_clean.wav", "-i", f"{S}/music.wav",
                "-filter_complex", fc,
                "-map", "[out]", "-ar", "48000", "-ac", "2", f"{S}/mix_pre.wav",
                "-map", "[vst]", f"{S}/stem_voice.wav", "-map", "[mst]", f"{S}/stem_music.wav"], check=True)
# two-pass loudness normalisation -> exactly -14 LUFS / -1 dBTP
import json
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{S}/mix_pre.wav", "-af",
                    "loudnorm=I=-14:TP=-1:LRA=9:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True)
m = json.loads(r.stderr[r.stderr.rindex("{"):])
ln = (f"loudnorm=I=-14:TP=-1:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{S}/mix_pre.wav", "-af", ln + ",aresample=48000",
                "-c:a", "pcm_s24le", f"{S}/mix.wav"], check=True)
print("mix ok")
