"""Cut plan + corrected captions for the Tamir Dortal reel.
Writes: tamir/assets/aroll.mp4, tamir/assets/voice.wav, edit.json (segments, word timings in OUTPUT time)."""
import json, subprocess, sys, os
S = sys.argv[1]
P = f"{S}/tamir"

# keep-segments in SOURCE seconds (all boundaries sit inside measured silences)
SEGS = [
    (33.45, 36.62),   # HOOK: "פוף, בגלל החלטה אישית של פקיד, הרישיון שלך נשלל"
    (1.05, 8.25), (8.65, 16.40), (22.72, 26.15), (26.55, 36.62),
    (42.74, 43.70), (44.08, 45.15), (45.34, 46.00), (46.28, 47.82), (48.05, 56.40),
    (58.95, 73.62),
]

w = json.load(open(f"{S}/transcript.json"))
FIX = {18:"הרישיונות",21:"2,600",22:"רישיונות",24:"ב־2025",25:"בלבד.",28:"ביום.",31:"באוקטובר",34:"פיגוע",
       38:"שווה.",54:"פקידים",56:"שם",60:"בספינה.",63:"אותך:",64:"המשרד",65:"לביטחון",66:"לאומי,",73:"הרישיון.",
       77:"למטווחים,",79:"אקדח.",80:"פוף!",85:"פקיד,",86:"הרישיון",88:"נשלל.",109:"פשוטה:",112:"שוללים?",
       114:"מסרה",117:"וסירבה",120:"המספרים.",121:"המשרד",122:"לביטחון",129:"בכלל.",132:"״תיענה",
       133:"בהקדם״.",138:"נמאס",140:"לחכות,",143:"עתירות:",148:"למשרד",149:"לביטחון",150:"לאומי.",
       153:"תשובות:",156:"וכמה.",159:"התפתחויות",173:"לציבור."}
words = [dict(text=FIX.get(i, x["text"]).strip(), s=x["start"], e=x["end"]) for i, x in enumerate(w)]

# speech phrases (source interval, word index range) from silencedetect + chunk re-transcriptions
PHR = [((1.12,8.13),0,20),((8.77,12.82),21,28),((13.35,16.26),29,38),((22.81,23.42),53,54),((23.77,24.30),55,56),
       ((24.75,26.05),57,60),((26.67,27.66),61,63),((28.04,33.33),64,79),((33.57,35.18),80,84),((35.54,36.52),85,88),
       ((42.82,43.65),104,105),((44.13,45.11),106,107),((45.38,47.77),108,109),((48.12,48.85),110,112),
       ((49.23,51.55),113,120),((51.92,55.02),121,131),((55.24,55.88),132,133),((58.99,59.75),137,140),
       ((60.10,62.18),141,143),((62.42,64.47),144,150),((64.84,65.67),151,153),((66.09,67.53),154,156),
       ((67.96,71.68),157,169),((72.02,73.55),170,173)]
src_words = []
for (a, b), i0, i1 in PHR:
    ws = words[i0:i1+1]
    # distribute by character weight inside the measured phrase interval
    wt = [len(x["text"]) + 1.5 for x in ws]; tot = sum(wt); t = a
    for x, k in zip(ws, wt):
        d = (b - a) * k / tot
        src_words.append(dict(text=x["text"], s=round(t, 3), e=round(t + d, 3), idx=words.index(x)))
        t += d

def map_t(t, pref_first=False):
    out = 0.0; hits = []
    for a, b in SEGS:
        if a - 1e-6 <= t <= b + 1e-6: hits.append(out + t - a)
        out += b - a
    return hits

out_words = []
for k, (a, b) in enumerate(SEGS):
    off = sum(y - x for x, y in SEGS[:k])
    for x in src_words:
        mid = (x["s"] + x["e"]) / 2
        if a <= mid <= b:
            out_words.append(dict(text=x["text"], start=round(off + max(x["s"], a) - a, 3),
                                  end=round(off + min(x["e"], b) - a, 3), seg=k))
cuts = []; off = 0
for a, b in SEGS: cuts.append(round(off, 3)); off += b - a
total = round(off, 3)
json.dump(dict(segs=SEGS, cuts=cuts, total=total, words=out_words), open(f"{S}/edit.json", "w"), ensure_ascii=False, indent=1)
print("total", total, "words", len(out_words))

# render a-roll (video + voice) with 12 ms audio fades at every join
if "--render" in sys.argv:
    parts = []; fc = []
    for k, (a, b) in enumerate(SEGS):
        d = b - a
        fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{k}]")
        fc.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d-0.012:.3f}:d=0.012[a{k}]")
        parts.append(f"[v{k}][a{k}]")
    fc.append("".join(parts) + f"concat=n={len(SEGS)}:v=1:a=1[v][a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{P}/assets/raw.mp4", "-filter_complex", ";".join(fc),
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-r", "30",
                    "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000", f"{S}/aroll_tmp.mov"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{S}/aroll_tmp.mov", "-map", "0:v", "-c:v", "copy", "-an",
                    "-movflags", "+faststart", f"{P}/assets/aroll.mp4"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{S}/aroll_tmp.mov", "-map", "0:a", "-c:a", "pcm_s16le",
                    f"{S}/voice.wav"], check=True)
    print("rendered")
