"""Resolve the EDL into an output timeline: shots with absolute times and crops."""
from edl import SEGMENTS, SIZES, SRC_W, SRC_H, TOTAL, FPS

def fr(t):  # snap to frame grid
    return round(t * FPS) / FPS

def crop(fx, fy, size, aspect):
    zw, zh = SIZES[size]
    if aspect == "h":  # 16:9
        w = zw * SRC_W; h = w * 9 / 16; face_y = 0.36
    else:              # 9:16
        h = zh * SRC_H; w = h * 9 / 16; face_y = 0.30
    w, h = int(w) // 2 * 2, int(h) // 2 * 2
    x = min(max(fx * SRC_W - w / 2, 0), SRC_W - w)
    y = min(max(fy * SRC_H - h * face_y, 0), SRC_H - h)
    return w, h, int(x) // 2 * 2, int(y) // 2 * 2

def timeline():
    t = 0.0
    shots, audio, caps, cards = [], [], [], []
    for s in SEGMENTS:
        if s["kind"] == "seg":
            dur = fr(s["b"] - s["a"])
            audio.append((s["clip"], s["a"], dur, t))
            offs = [o for *_, o in s["shots"]] + [dur]
            for i, (clip, sin, fx, fy, size, o) in enumerate(s["shots"]):
                d = fr(offs[i + 1]) - fr(o)
                shots.append(dict(clip=clip, src=sin, start=fr(t + o), dur=d,
                                  fx=fx, fy=fy, size=size))
            starts = [c[0] for c in s["caps"]]
            for i, (cs, text) in enumerate(s["caps"]):
                ce = starts[i + 1] if i + 1 < len(starts) else s["b"]
                caps.append((t + max(cs - s["a"], 0), t + min(ce - s["a"], dur), text))
            t = fr(t + dur)
        elif s["kind"] == "card":
            cards.append(dict(kind="card", start=t, dur=s["dur"], text=s["text"]))
            t = fr(t + s["dur"])
        else:
            cards.append(dict(kind="end", start=t, dur=fr(TOTAL - t)))
            t = TOTAL
    return shots, audio, caps, cards

if __name__ == "__main__":
    sh, au, ca, cd = timeline()
    for s in sh: print(s)
    for c in cd: print(c)
    print("speech ends", au[-1][3] + au[-1][2])
