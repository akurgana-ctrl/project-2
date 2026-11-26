#!/usr/bin/env python3
"""Simple edit of a talking-head video (koach-reel "simple edit" mode, Nov 2026).

Usage: python3 -I build_simple.py <project-dir> <edit.json>

edit.json:
{
  "speech_end": 79.88,                 # length of assets/tamir.mp4 (the cut, graded base)
  "music_volume": 0.08,                 # optional, default 0.08 (user: music quieter, voice louder) (see the rotation table in simple_edit.md)
  "name": "תמיר דורטל", "title": "מייסד כח התערבות",
  "caps": [["text", start, end, {"word": "gold|red|blue|gold big"}], ...],   # times on the CUT timeline
  "sfx":  [["whoosh", 0.25, 1.5, 0.35], ["pop", 0.42, 0.2, 0.45], ...]       # file, start, dur, volume
}
Assets in <project>/assets/: tamir.mp4, logo-blue.png, music.mp3, fonts/heebo-*.woff2, and the sfx mp3s.
"""
import sys, os, html, json

P = sys.argv[1]
E = json.load(open(sys.argv[2]))
SPEECH_END = float(E["speech_end"])
TOTAL = round(SPEECH_END + 0.22, 2)

CAPS = [tuple(x) for x in E["caps"]]

FONT = """
@font-face { font-family: 'Heebo'; font-weight: 100 900; font-display: block;
  src: url('assets/fonts/heebo-hebrew.woff2') format('woff2');
  unicode-range: U+0307-0308, U+0590-05FF, U+200C-2010, U+20AA, U+25CC, U+FB1D-FB4F; }
@font-face { font-family: 'Heebo'; font-weight: 100 900; font-display: block;
  src: url('assets/fonts/heebo-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }
"""
esc = lambda s: html.escape(s, quote=False)

groups, js = [], []
for i, (text, s, e, emph) in enumerate(CAPS):
    words = [f'<span class="w {emph.get(w, "")}">{esc(w)}</span>' for w in text.split(" ")]
    groups.append(f'    <div id="cap-{i}" class="cap"><div class="cap-in">{" ".join(words)}</div></div>')
    js.append(f'  pop("#cap-{i}", {s:.2f}, {e:.2f});')

captions = f"""<template>
  <style>
    {FONT}
    #root {{ position: absolute; inset: 0; pointer-events: none; }}
    .cap {{ position: absolute; left: 0; right: 0; top: 1060px; text-align: center;
      direction: rtl; opacity: 0; visibility: hidden; overflow: visible; }}
    .cap-in {{ display: inline-block; padding: 6px 28px 14px; font-family: 'Heebo', sans-serif;
      font-weight: 900; font-size: 88px; line-height: 1.05; color: #fff; max-width: 980px;
      -webkit-text-stroke: 3px #000; paint-order: stroke fill;
      text-shadow: 0 6px 0 rgba(0,0,0,.85), 0 0 28px rgba(0,0,0,.55); }}
    .w {{ display: inline-block; }}
    .w.gold {{ color: #FFC20E; }}
    .w.red {{ color: #FF3B3B; }}
    .w.blue {{ color: #5EA8FF; }}
    .w.big {{ font-size: 1.2em; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(groups)}
  </div>
  <script>
  const tl = gsap.timeline({{ paused: true }});
  function pop(sel, s, e) {{
    tl.set(sel, {{ visibility: "visible" }}, s);
    tl.fromTo(sel, {{ opacity: 0, scale: 0.84, y: 16 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.14, ease: "back.out(2.4)", immediateRender: false }}, s);
    tl.to(sel, {{ opacity: 0, duration: 0.07, ease: "power2.in" }}, e - 0.07);
    tl.set(sel, {{ opacity: 0, visibility: "hidden" }}, e);
  }}
{chr(10).join(js)}
  window.__timelines["captions"] = tl;
  </script>
</template>
"""

overlays = f"""<template>
  <style>
    {FONT}
    #root {{ position: absolute; inset: 0; pointer-events: none; font-family: 'Heebo', sans-serif; direction: rtl; }}
    .lt {{ position: absolute; right: 70px; top: 1225px; padding: 12px 30px 14px; border-right: 10px solid #FFC20E; border-radius: 8px;
      background: rgba(10,22,60,.9); box-shadow: 0 12px 30px rgba(0,0,0,.5); text-align: right; opacity: 0; }}
    .lt-name {{ color: #fff; font-weight: 900; font-size: 54px; line-height: 1.05; }}
    .lt-sub {{ color: #FFC20E; font-weight: 700; font-size: 36px; }}
  </style>
  <div id="root" data-composition-id="overlays" data-width="1080" data-height="1920">
    <div id="lt-tamir" class="lt"><div class="lt-name">{esc(E["name"])}</div><div class="lt-sub">{esc(E["title"])}</div></div>
  </div>
  <script>
  const tl = gsap.timeline({{ paused: true }});
  tl.set("#lt-tamir", {{ opacity: 0 }}, 0);
  tl.fromTo("#lt-tamir", {{ opacity: 0, x: 80 }}, {{ opacity: 1, x: 0, duration: 0.35, ease: "back.out(1.8)", immediateRender: false }}, 0.40);
  tl.to("#lt-tamir", {{ opacity: 0, x: 60, duration: 0.25, ease: "power2.in" }}, 5.6);
  window.__timelines["overlays"] = tl;
  </script>
</template>
"""

sfx = [tuple(x) for x in E.get("sfx", [])]
sfx_html = "\n".join(
    f'      <audio id="sfx-{i}" class="clip" src="assets/{f}.mp3" data-start="{s:.2f}" data-duration="{d}" data-volume="{v}" data-track-index="{10 + (i % 3)}"></audio>'
    for i, (f, s, d, v) in enumerate(sfx))

index = f"""<!doctype html>
<html lang="he">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; }}
      #cam {{ position: absolute; inset: 0; }}
      #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
      #logo {{ position: absolute; right: 26px; top: 70px; width: 300px; z-index: 30; }}
      #overlays {{ z-index: 10; }}
      #captions {{ z-index: 20; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
      <div id="cam">
        <video id="tamir" class="clip" src="assets/tamir.mp4" data-start="0" data-duration="{SPEECH_END}" data-media-start="0" data-has-audio="true" data-volume="1.2" playsinline data-track-index="0"></video>
      </div>
      <img id="logo" class="clip" src="assets/logo-blue.png" alt="" data-start="0" data-duration="{TOTAL}" data-track-index="2" />
      <div id="overlays" data-composition-id="overlays" data-composition-src="compositions/overlays.html" data-start="0" data-duration="{TOTAL}" data-track-index="3" data-track-kind="graphics" data-width="1080" data-height="1920"></div>
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{TOTAL}" data-track-index="4" data-track-kind="captions" data-width="1080" data-height="1920"></div>
      <audio id="music" class="clip" src="assets/music.mp3" data-start="0" data-duration="{TOTAL}" data-media-start="0" data-volume="{E.get('music_volume', 0.08)}" data-fade-in="1.0" data-fade-out="2.0" data-track-index="5"></audio>
{sfx_html}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.set("#cam", {{ scale: 1 }}, 0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
os.makedirs(os.path.join(P, "compositions"), exist_ok=True)
open(os.path.join(P, "index.html"), "w").write(index)
open(os.path.join(P, "compositions/captions.html"), "w").write(captions)
open(os.path.join(P, "compositions/overlays.html"), "w").write(overlays)
print("ok", len(CAPS))
