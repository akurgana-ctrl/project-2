"""Cut + corrected word timings for the MK Itamar Itam reel. usage: edit_itam.py <scratch> [--render]"""
import json, subprocess, sys
S = sys.argv[1]; D = f"{S}/itam"; P = f"{D}/proj"
SEGS = [
    (14.40, 17.12),                    # HOOK: "אתם קודם כל הגיבורים שלנו"
    (0.68, 7.40), (7.88, 9.62), (10.05, 17.12), (17.62, 27.05), (27.40, 39.77),
]
w = json.load(open(f"{D}/words.json"))["transcription"]
toks = [dict(text=t["text"].strip(), s=t["offsets"]["from"] / 1000, e=t["offsets"]["to"] / 1000) for t in w if t["text"].strip()]
FIX = {"כוח": "כח", "איתור": "עיטור", "מאתרים": "מעטרים", "צהל,": "צה״ל,", "בעולם": "בעולם.", "בנו": "באנו", "לעבוד": "לעבוד.", "שלנו": "שלנו"}
for t in toks: t["text"] = FIX.get(t["text"], t["text"])
# phrases between measured silences; words are spread inside each by character weight
PHR = [(0.74, 3.96), (4.52, 7.31), (7.95, 9.56), (10.11, 14.16), (14.46, 17.07), (17.70, 20.68), (20.88, 21.67),
       (22.00, 23.28), (23.60, 26.98), (27.47, 31.60), (31.90, 35.62), (35.99, 37.41), (38.25, 38.92)]
src_words = []
for a, b in PHR:
    ws = [t for t in toks if a - 0.45 <= (t["s"] + t["e"]) / 2 <= b + 0.2 and t not in [x["_t"] for x in src_words]]
    wt = [len(x["text"]) + 1.5 for x in ws]; tot = sum(wt) or 1; t0 = a
    for x, k in zip(ws, wt):
        d = (b - a) * k / tot
        src_words.append(dict(text=x["text"], s=round(t0, 3), e=round(t0 + d, 3), _t=x)); t0 += d
words = []
for k, (a, b) in enumerate(SEGS):
    off = sum(y - x for x, y in SEGS[:k])
    for x in src_words:
        m = (x["s"] + x["e"]) / 2
        if a <= m <= b:
            words.append(dict(text=x["text"], start=round(off + max(x["s"], a) - a, 3), end=round(off + min(x["e"], b) - a, 3), seg=k))
cuts, off = [], 0
for a, b in SEGS: cuts.append(round(off, 3)); off += b - a
json.dump(dict(segs=SEGS, cuts=cuts, total=round(off, 3), words=words), open(f"{D}/edit.json", "w"), ensure_ascii=False, indent=1)
print("total", round(off, 3)); print(" ".join(f"{x['text']}[{x['start']:.1f}]" for x in words))
if "--render" in sys.argv:
    fc, parts = [], []
    for k, (a, b) in enumerate(SEGS):
        d = b - a
        fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos,unsharp=5:5:0.6[v{k}]")
        fc.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d-0.012:.3f}:d=0.012[a{k}]")
        parts.append(f"[v{k}][a{k}]")
    fc.append("".join(parts) + f"concat=n={len(SEGS)}:v=1:a=1[v][a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{D}/src/raw.mov", "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-r", "30", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000",
                    f"{D}/aroll_tmp.mov"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{D}/aroll_tmp.mov", "-map", "0:v", "-c:v", "copy", "-an", "-movflags", "+faststart",
                    f"{P}/assets/aroll.mp4"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{D}/aroll_tmp.mov", "-map", "0:a", "-c:a", "pcm_s16le", f"{D}/voice.wav"], check=True)
    print("rendered")
