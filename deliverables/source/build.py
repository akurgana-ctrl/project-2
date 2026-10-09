"""Render the spot in one aspect: python3 build.py <scratch> <h|v>"""
import os, sys, subprocess, math
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import timeline, crop
from edl import FPS, TOTAL, BLUR
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S, ASP = sys.argv[1], sys.argv[2]
OW, OH = (1920, 1080) if ASP == "h" else (1080, 1920)
W = f"{S}/work_{ASP}"; os.makedirs(W, exist_ok=True)
TTF = f"{S}/ttf"
GOLD = (239, 199, 62)  # sampled from the כח התערבות logo
FLASHES = [1.48, 4.72, 5.68, 16.20, 18.60]  # + wake-up and end card, from the timeline

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise SystemExit(" ".join(cmd) + "\n" + r.stderr[-3000:])

shots, audio, caps, cards = timeline()
FLASHES += [a for a, b, txt in caps if "התעוררנו" in txt] + [c["start"] for c in cards if c["kind"] == "end"]

# ---------- 1. shots: crop from 4K, drift, monochrome grade ----------
GRADE = ("hue=s=0,"
         "curves=master='0/0 0.14/0.02 0.32/0.16 0.52/0.50 0.72/0.80 0.88/0.94 1/1',"
         "unsharp=5:5:0.6")
def render_shot(i):
    s = shots[i]
    w, h, x, y = crop(s["fx"], s["fy"], s["size"], ASP)
    bw, bh = int(OW * 1.06) // 2 * 2, int(OH * 1.06) // 2 * 2
    ph = i * 1.7
    dx, dy = (bw - OW) / 2, (bh - OH) / 2
    drift = (f"crop={OW}:{OH}:x='{dx}+{dx*0.6}*sin(2*PI*0.21*t+{ph})+2.5*sin(11*t+{ph})'"
             f":y='{dy}+{dy*0.6}*sin(2*PI*0.17*t+{ph*1.3})+2.5*sin(13*t+{ph})'")
    vf = f"crop={w}:{h}:{x}:{y},scale={bw}:{bh}:flags=lanczos,{drift},fps={FPS},{GRADE},format=yuv420p"
    boxes = [bx for bx in BLUR if bx[0] == s["clip"] and bx[1] < s["src"] + s["dur"] and bx[2] > s["src"]]
    if boxes:  # soft-edged blur over the election poster, applied on the 4K frame before the crop
        pre, last = [], "0:v"
        for k, (_, _, _, x0, y0, x1, y1) in enumerate(boxes):
            X0, Y0 = int(x0 * 3840) // 2 * 2, int(y0 * 2160) // 2 * 2
            BW, BH = int((x1 - x0) * 3840) // 2 * 2, int((y1 - y0) * 2160) // 2 * 2
            F = 40
            pre.append(f"[{last}]split[o{k}][c{k}];[c{k}]crop={BW}:{BH}:{X0}:{Y0},gblur=sigma=38,format=yuva444p,"
                       f"geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='255*min(1,min(min(X,W-X),min(Y,H-Y))/{F})'[p{k}];"
                       f"[o{k}][p{k}]overlay={X0}:{Y0}[m{k}]")
            last = f"m{k}"
        vf = ";".join(pre) + f";[{last}]" + vf + "[vo]"
    out = f"{W}/shot{i:02d}.mp4"
    if os.path.exists(out): return out
    vflag = ["-filter_complex", vf, "-map", "[vo]"] if boxes else ["-vf", vf]
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s['src']:.3f}", "-i", f"{S}/raw/{s['clip']}.mp4",
         "-t", f"{s['dur']:.3f}", "-an", *vflag, "-r", str(FPS),
         "-c:v", "libx264", "-preset", "medium", "-crf", "10", out])
    return out

# ---------- 2. typography cards (PIL + raqm for proper RTL) ----------
def font(name, size): return ImageFont.truetype(f"{TTF}/{name}.ttf", size)
FR = "frank-ruhl-libre-hebrew-900-normal"
KB = "karantina-hebrew-700-normal"
KR = "karantina-hebrew-400-normal"

def text_center(d, cx, y, txt, f, fill, spacing=0):
    bb = d.textbbox((0, 0), txt, font=f, direction="rtl", features=["kern"])
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], y - bb[1]), txt, font=f, fill=fill, direction="rtl")
    return bb[3] - bb[1]

def card_q():
    im = Image.new("RGBA", (OW, OH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sz = 300 if ASP == "h" else 250
    f = font(FR, sz)
    bb = d.textbbox((0, 0), "ובסוף?", font=f, direction="rtl")
    text_center(d, OW / 2, OH / 2 - (bb[3] - bb[1]) / 2, "ובסוף?", f, (245, 242, 235))
    im.save(f"{W}/card_q.png")

LOGO = f"{S}/logos/logo_rev.png"  # reversed כח התערבות logo (see logo_rev.py)

def logo_sized(h=None, w=None):
    lg = Image.open(LOGO)
    if h: return lg.resize((round(lg.width * h / lg.height), h), Image.LANCZOS)
    return lg.resize((w, round(lg.height * w / lg.width)), Image.LANCZOS)

def card_end():
    """Two layers: A = logo, B = CTA (appears later)."""
    v = ASP == "v"
    a = Image.new("RGBA", (OW, OH), (0, 0, 0, 0)); d = ImageDraw.Draw(a)
    cx = OW / 2
    lg = logo_sized(w=760) if v else logo_sized(h=500)
    top = 300 if v else 88
    a.alpha_composite(lg, (int(cx - lg.width / 2), top))
    y = top + lg.height + (55 if v else 36)
    d.rectangle([cx - 70, y, cx + 70, y + 5], fill=GOLD)
    a.save(f"{W}/end_a.png")

    b = Image.new("RGBA", (OW, OH), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    y += 50 if v else 34
    cta = font(KB, 150 if v else 118)
    y += text_center(d, cx, y, "תמכו עכשיו", cta, GOLD) + (34 if v else 22)
    sub = font(KR, 72 if v else 58)
    y += text_center(d, cx, y, "הלינק מתחת לוידאו", sub, (225, 222, 215)) + (34 if v else 24)
    # down arrow, hand-drawn geometry so it matches the type weight
    aw, al = 24, 60 if v else 52
    d.line([cx, y, cx, y + al], fill=GOLD, width=6)
    d.line([cx - aw, y + al - aw, cx, y + al + 2], fill=GOLD, width=6)
    d.line([cx + aw, y + al - aw, cx, y + al + 2], fill=GOLD, width=6)
    b.save(f"{W}/end_b.png")

def bug():
    """Small logo in the corner for the body of the spot."""
    im = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    lg = logo_sized(h=150 if ASP == "v" else 112)
    al = lg.getchannel("A").point(lambda x: int(x * 0.92)); lg.putalpha(al)
    im.alpha_composite(lg, (52, 150) if ASP == "v" else (58, 50))
    im.save(f"{W}/bug.png")

def gate():
    """Rounded film-gate matte like the reference: black outside, soft edge."""
    m = 26 if ASP == "h" else 22
    r = 46
    mask = Image.new("L", (OW, OH), 255); d = ImageDraw.Draw(mask)
    d.rounded_rectangle([m, m, OW - m, OH - m], radius=r, fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(2.2))
    im = Image.new("RGBA", (OW, OH), (0, 0, 0, 255)); im.putalpha(mask)
    im.save(f"{W}/gate.png")

# ---------- 3. captions (ASS / libass) ----------
def ass_time(t):
    cs = int(round(t * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def captions():
    v = ASP == "v"
    size = 118 if v else 104
    margin_v = 560 if v else 120
    gold = "&H003EC7EF&"  # BGR of GOLD
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OW}
PlayResY: {OH}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Karantina,{size},&H00EBF2F5,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,1,0,1,3.2,2.5,2,80,80,{margin_v},-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for a, b, txt in caps:
        if "*" in txt:
            pre, emph = txt.split("*", 1)
            body = (pre + "{\\fnFrank Ruhl Libre Black\\c" + gold + "\\fs" + str(int(size * 1.0)) + "}" + emph)
        else:
            body = txt
        pop = "{\\fad(30,0)\\fscx112\\fscy112\\t(0,110,\\fscx100\\fscy100)}"
        lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b - 0.02)},Cap,,0,0,0,,{pop}{body}")
    open(f"{W}/caps.ass", "w", encoding="utf-8").write(hdr + "\n".join(lines) + "\n")

# ---------- 4. assemble ----------
def assemble(shot_files):
    # base track: shots + black holes for cards, in timeline order
    items = [(s["start"], f) for s, f in zip(shots, shot_files)]
    for c in cards:
        blk = f"{W}/black_{c['start']:.2f}.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s={OW}x{OH}:r={FPS}",
             "-t", f"{c['dur']:.3f}", "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p", blk])
        items.append((c["start"], blk))
    items.sort()
    open(f"{W}/list.txt", "w").write("".join(f"file '{f}'\n" for _, f in items))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{W}/list.txt",
         "-c", "copy", f"{W}/base.mp4"])

    q = [c for c in cards if c["kind"] == "card"][0]
    e = [c for c in cards if c["kind"] == "end"][0]
    eb = e["start"] + 1.6
    flash = "+".join(f"between(t,{f:.2f},{f + 0.08:.2f})" for f in FLASHES)
    fc = (
        f"[0:v]setpts=PTS-STARTPTS,format=gray,split[m][hl];[hl]curves=master='0/0 0.62/0 1/1',gblur=sigma=22[hb];"
        f"[m][hb]blend=all_mode=screen:all_opacity=0.32,format=yuv420p[b];"
        f"[1:v]format=rgba[q];[2:v]format=rgba,fade=t=in:st={e['start']+0.12}:d=0.25:alpha=1[ea];"
        f"[3:v]format=rgba,fade=t=in:st={eb}:d=0.3:alpha=1[eb];[4:v]format=rgba[g];"
        f"[b][q]overlay=enable='between(t,{q['start']+0.04:.2f},{q['start']+q['dur']:.2f})'[v1];"
        f"[v1][ea]overlay=enable='gte(t,{e['start']+0.12:.2f})'[v2];"
        f"[v2][eb]overlay=enable='gte(t,{eb:.2f})'[v3];"
        # halation: bloom of the highlights
        f"[v3]noise=c0s=16:c0f=t+u,vignette=angle=PI/4.2,"
        # exposure flashes on the big cuts
        f"eq=brightness=0.55:enable='{flash}',format=yuv420p[v4];"
        f"[6:v]format=rgba[bg];[v4][bg]overlay=enable='between(t,{q['start']+q['dur']:.2f},{e['start']:.2f})'[v5];"
        f"[v5][g]overlay,ass={W}/caps.ass:fontsdir={TTF},format=yuv420p[vout]"
    )
    run(["ffmpeg", "-v", "error", "-y", "-i", f"{W}/base.mp4",
         "-loop", "1", "-framerate", str(FPS), "-i", f"{W}/card_q.png",
         "-loop", "1", "-framerate", str(FPS), "-i", f"{W}/end_a.png",
         "-loop", "1", "-framerate", str(FPS), "-i", f"{W}/end_b.png",
         "-loop", "1", "-framerate", str(FPS), "-i", f"{W}/gate.png",
         "-i", f"{S}/mix.wav",
         "-loop", "1", "-framerate", str(FPS), "-i", f"{W}/bug.png",
         "-filter_complex", fc, "-map", "[vout]", "-map", "5:a", "-t", f"{TOTAL}",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "16M", "-bufsize", "32M", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
         f"{S}/out_{ASP}.mp4"])

if __name__ == "__main__":
    card_q(); card_end(); bug(); gate(); captions()
    if "--cards-only" in sys.argv: raise SystemExit
    with ThreadPoolExecutor(2) as ex:
        files = list(ex.map(render_shot, range(len(shots))))
    assemble(files)
    print("done", f"{S}/out_{ASP}.mp4")
