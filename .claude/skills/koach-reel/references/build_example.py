#!/usr/bin/env python3
"""Generate the static HyperFrames HTML for the Andrey X reel (final approved version, v10, Nov 2026).

Reference for the koach-reel skill: copy, then replace CAPS, the segment times and the overlay copy.
Usage: python3 -I build.py <hyperframes-project-dir>

Assets this expects in <project>/assets/:
  tamir.mp4, natali.mp4          footage, re-encoded with -g 30 (natali.mp4 already trimmed + delogo'd)
  logo-blue.png                  = repo assets/logo.png        (top-right, blue/yellow, no glow)
  logo.png                       = repo assets/logo-light.png  (white, end card only)
  andrey.jpg, letter-top.png     target photo, document crop (ID number pixelated)
  music.mp3                      46 s cut of "Five Armies" (Kevin MacLeod, CC BY 4.0 - credit in caption)
  whoosh impact glitch swipe pop like share ding sparkle applause alarm shutter riser .mp3
                                 -> scripts/make_sfx.sh
  fonts/heebo-hebrew.woff2, fonts/heebo-latin.woff2

Timeline: Tamir A1 (src 13.85, 3.75 s) -> Natalie (src 1.05 in the trimmed clip, 6.45 s)
          -> Tamir A2 (src 20.64, 11.04 s) -> Tamir B (src 38.42, 13.98 s) -> end card.
Times written below 6.79 are final; old-timeline literals >= 6.79 inside <script> are shifted by D
(see shift_scripts); literals already on the new timeline are listed in KEEP.
"""
import sys, os, html

P = sys.argv[1]
D = 3.41  # Natalie insert (6.45 s) minus removed Tamir background (3.04 s)
END_SPEECH = 31.81 + D
TOTAL = END_SPEECH + 3.8


# (text, start, end, emphasis_words: {word: class})
CAPS = [
    ("אנדריי, זוכרים אותו?", 0.10, 0.62, {"אנדריי,": "gold"}),
    ("זוכרים את הקמפיין שלנו", 0.63, 1.75, {}),
    ("בהובלת נטלי דדון", 1.75, 2.77, {"נטלי": "gold", "דדון": "gold"}),
    ("לגירושו מהארץ?", 2.77, 3.75, {}),
    ("ישראל העניקה לו", 3.80, 5.10, {"ישראל": "blue"}, "N"),
    ("אזרחות מכוח", 5.10, 6.40, {"אזרחות": "gold"}, "N"),
    ("חוק השבות", 6.40, 7.30, {"השבות": "gold"}, "N"),
    ("ומקלט מהמלחמה", 7.30, 9.00, {}, "N"),
    ("ומה הוא עושה", 9.10, 9.80, {}, "N"),
    ("עם זה?", 9.80, 10.15, {"זה?": "red"}, "N"),
    ("ומאז רודף", 6.79, 7.62, {}),
    ("את החיילים שלנו", 7.62, 8.71, {"החיילים": "gold"}),
    ("וקורא להם רוצחים", 8.75, 9.75, {"רוצחים": "red"}),
    ("אז הלחץ שלנו", 9.75, 11.05, {"הלחץ": "gold"}),
    ("עובד!", 11.05, 11.89, {"עובד!": "gold big"}),
    ("השר שיקלי הגיש", 11.89, 12.73, {"שיקלי": "gold"}),
    ("מכתב רשמי", 12.73, 13.29, {}),
    ("ודרש לשלול את האזרחות", 13.29, 14.71, {"לשלול": "red"}),
    ("כל הכבוד לשר שיקלי", 14.75, 16.75, {"שיקלי": "gold"}),
    ("ככה עושים את זה", 16.75, 17.80, {}),
    ("אבל רק זה לא מספיק", 17.96, 19.38, {"לא": "red", "מספיק": "red"}),
    ("צריך להמשיך ללחוץ", 19.39, 20.52, {"ללחוץ": "gold"}),
    ("ולפעול עד שזה יקרה", 20.53, 21.60, {}),
    ("גדעון סער", 21.61, 22.66, {"גדעון": "gold big", "סער": "gold big"}),
    ("זה עליך", 22.66, 23.70, {"עליך": "red"}),
    ("המכתב על השולחן שלך", 23.70, 24.44, {}),
    ("הגיע הזמן לשלול", 24.44, 24.99, {"לשלול": "red"}),
    ("את האזרחות", 24.99, 25.61, {}),
    ("ואנחנו לא נרפה", 25.61, 26.78, {"נרפה": "gold"}),
    ("עד שזה יקרה", 26.79, 27.61, {}),
    ("תשתפו, תגיבו", 27.61, 28.49, {"תשתפו,": "gold"}),
    ("תתייגו את גדעון סער", 28.49, 29.92, {"גדעון": "gold", "סער": "gold"}),
    ("שזה יגיע לכל בית בישראל", 29.92, 31.61, {"בישראל": "blue"}),
]

FONT = """
@font-face { font-family: 'Heebo'; font-weight: 100 900; font-display: block;
  src: url('assets/fonts/heebo-hebrew.woff2') format('woff2');
  unicode-range: U+0307-0308, U+0590-05FF, U+200C-2010, U+20AA, U+25CC, U+FB1D-FB4F; }
@font-face { font-family: 'Heebo'; font-weight: 100 900; font-display: block;
  src: url('assets/fonts/heebo-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }
"""


def esc(s):
    return html.escape(s, quote=False)


# ---------------- captions ----------------
groups, js = [], []
for i, (text, s, e, emph, *nat) in enumerate(CAPS):
    if not nat and s >= 6.78: s, e = s + D, e + D
    words = []
    for w in text.split(" "):
        cls = emph.get(w, "")
        words.append(f'<span class="w {cls}">{esc(w)}</span>')
    low = " low" if nat else (" split" if (15.26 <= s < 18.46) else "")
    groups.append(f'    <div id="cap-{i}" class="cap{low}"><div class="cap-in">{" ".join(words)}</div></div>')
    js.append(f'  pop("#cap-{i}", {s:.2f}, {e:.2f});')

captions = f"""<template>
  <style>
    {FONT}
    #root {{ position: absolute; inset: 0; pointer-events: none; }}
    .cap {{ position: absolute; left: 0; right: 0; top: 1060px; text-align: center;
      direction: rtl; opacity: 0; visibility: hidden; overflow: visible; }}
    .cap-in {{ display: inline-block; padding: 6px 28px 14px; font-family: 'Heebo', sans-serif;
      font-weight: 900; font-size: 92px; line-height: 1.05; color: #fff; max-width: 960px;
      -webkit-text-stroke: 3px #000; paint-order: stroke fill;
      text-shadow: 0 6px 0 rgba(0,0,0,.85), 0 0 28px rgba(0,0,0,.55); }}
    .cap.low {{ top: 1290px; }}
    .cap.split {{ top: 1430px; }}
    .w {{ display: inline-block; }}
    .w.gold {{ color: #FFC20E; }}
    .w.red {{ color: #FF3B3B; }}
    .w.blue {{ color: #5EA8FF; }}
    .w.big {{ font-size: 1.25em; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(groups)}
  </div>
  <script>
  const tl = gsap.timeline({{ paused: true }});
  function pop(sel, s, e) {{
    tl.set(sel, {{ visibility: "visible" }}, s);
    tl.fromTo(sel, {{ opacity: 0, scale: 0.82, y: 18 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.14, ease: "back.out(2.4)" }}, s);
    tl.to(sel, {{ opacity: 0, duration: 0.08, ease: "power2.in" }}, e - 0.08);
    tl.set(sel, {{ opacity: 0, visibility: "hidden" }}, e);
  }}
{chr(10).join(js)}
  window.__timelines["captions"] = tl;
  </script>
</template>
"""

# ---------------- overlays ----------------
overlays = f"""<template>
  <style>
    {FONT}
    #root {{ position: absolute; inset: 0; pointer-events: none; font-family: 'Heebo', sans-serif; direction: rtl; }}
    .abs {{ position: absolute; }}
    /* Andrey hero card */
    #ov-andrey {{ left: 28px; top: 300px; width: 250px; }}
    #ov-andrey .card {{ background: #fff; padding: 12px 12px 54px; border-radius: 8px;
      box-shadow: 0 24px 60px rgba(0,0,0,.55); transform: rotate(-5deg); position: relative; }}
    #ov-andrey img {{ display: block; width: 100%; height: 280px; object-fit: cover; object-position: 50% 30%; border-radius: 4px; }}
    #ov-andrey .name {{ position: absolute; left: 0; right: 0; bottom: 10px; text-align: center;
      font-weight: 900; font-size: 36px; color: #111; }}
    #ov-andrey .x {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
      font-family: 'Heebo', sans-serif; font-weight: 900; font-size: 250px; line-height: 1; color: #E11; opacity: .9;
      text-shadow: 0 6px 18px rgba(0,0,0,.4); }}
    /* Natalie chip */
    #ov-natalie {{ right: 130px; top: 880px; }}
    .chip {{ display: inline-flex; align-items: center; gap: 16px; padding: 14px 30px; border-radius: 999px;
      background: #FFC20E; color: #111; font-weight: 900; font-size: 46px; box-shadow: 0 12px 30px rgba(0,0,0,.45); }}
    .chip.dark {{ background: rgba(12,18,40,.88); color: #fff; border: 3px solid #FFC20E; }}
    .chip.red {{ background: #E11; color: #fff; }}
    .chip small {{ font-size: 32px; font-weight: 700; opacity: .85; }}
    /* Andrey thumb */
    #ov-thumb {{ left: 50px; top: 220px; display: flex; align-items: center; gap: 16px; flex-direction: row-reverse; }}
    #ov-thumb .ph {{ width: 190px; height: 190px; border-radius: 50%; overflow: hidden; border: 6px solid #E11;
      box-shadow: 0 12px 30px rgba(0,0,0,.5); }}
    #ov-thumb .ph img {{ width: 100%; height: 100%; object-fit: cover; object-position: 50% 25%; }}
    /* Lower thirds */
    .lt {{ right: 70px; top: 1225px; padding: 12px 30px 14px; border-right: 10px solid #FFC20E; border-radius: 8px;
      background: rgba(10,22,60,.9); box-shadow: 0 12px 30px rgba(0,0,0,.5); text-align: right; }}
    .lt-name {{ color: #fff; font-weight: 900; font-size: 50px; line-height: 1.05; }}
    .lt-sub {{ color: #FFC20E; font-weight: 700; font-size: 34px; }}
    #ov-nname {{ top: 1440px; }}
    #ov-flash {{ inset: 0; background: #fff; opacity: 0; }}
    /* Stamp */
    #ov-stamp {{ left: 0; right: 0; top: 1230px; text-align: center; }}
    #ov-stamp .s {{ display: inline-block; padding: 18px 46px; border: 12px solid #FFC20E; border-radius: 22px;
      color: #FFC20E; font-weight: 900; font-size: 150px; line-height: 1; transform: rotate(-7deg);
      background: rgba(0,0,0,.35); text-shadow: 0 6px 20px rgba(0,0,0,.6); }}
    /* Letter */
    #ov-letter {{ left: 160px; top: 360px; width: 760px; height: 527px; direction: ltr; }}
    #ov-letter .paper {{ position: relative; width: 940px; height: 652px; transform: scale(0.8085); transform-origin: 0 0; overflow: hidden; border-radius: 14px;
      background: #fff; box-shadow: 0 30px 80px rgba(0,0,0,.6); border: 6px solid #FFC20E; }}
    #ov-letter .zoom {{ position: absolute; left: 0; top: 0; width: 940px; height: 652px; transform-origin: 47% 69%; }}
    #ov-letter img {{ position: absolute; left: 0; top: 0; width: 940px; height: 652px; }}
    #ov-letter .hl {{ position: absolute; left: 300px; top: 440px; width: 292px; height: 28px; background: rgba(255,194,14,.45);
      transform-origin: 100% 50%; mix-blend-mode: multiply; }}
    #ov-letter .tag {{ position: absolute; right: 24px; top: 24px; }}
    /* Chikli chip */
    #ov-chikli {{ left: 60px; right: 60px; top: 1255px; text-align: center; }}
    /* Gideon */
    #ov-gideon {{ left: 0; right: 0; top: 1215px; text-align: center; }}
    #ov-gideon .box {{ position: relative; display: inline-block; padding: 26px 30px 26px; border-radius: 14px;
      background: linear-gradient(180deg, #E0001B, #A30012);
      box-shadow: 0 0 0 5px #FFC20E, 0 0 40px rgba(255,0,0,.7), 0 16px 40px rgba(0,0,0,.55); }}
    #ov-gideon .gline {{ color: #fff; font-weight: 900; font-size: 48px; line-height: 1.05; text-shadow: 0 4px 0 rgba(0,0,0,.35); }}
    #ov-gideon .hz {{ position: absolute; left: 0; right: 0; height: 12px;
      background: repeating-linear-gradient(-45deg, #FFC20E 0 22px, #111 22px 44px); }}
    #ov-gideon .hz.t {{ top: 0; border-radius: 18px 18px 0 0; }}
    #ov-gideon .hz.b {{ bottom: 0; border-radius: 0 0 18px 18px; }}
    #ov-gideon .t0 {{ color: #FFC20E; font-weight: 900; font-size: 44px; letter-spacing: .04em; }}
    #ov-gideon .t3 {{ color: #fff; font-weight: 800; font-size: 40px; margin-top: 8px; opacity: 0; }}
    #ov-gideon .unused {{
      border: 5px solid #E11; box-shadow: 0 20px 50px rgba(0,0,0,.55); }}
    #ov-gideon .t1 {{ color: #fff; font-weight: 900; font-size: 128px; line-height: 1; text-shadow: 0 6px 0 rgba(0,0,0,.35); }}
    #ov-gideon .t2 {{ color: #FFC20E; font-weight: 900; font-size: 84px; line-height: 1.05; margin-top: 4px; text-shadow: 0 5px 0 rgba(0,0,0,.4); }}
    #ov-clock {{ left: 60px; right: 140px; top: 880px; text-align: center; }}
    /* CTA */
    #ov-cta {{ left: 40px; right: 40px; top: 1235px; display: flex; flex-wrap: wrap; justify-content: center; gap: 16px 18px; }}
    #ov-cta .chip {{ font-size: 46px; padding: 10px 26px; }}
    /* End card */
    #ov-end {{ inset: 0; background: radial-gradient(ellipse at 50% 40%, rgba(16,30,80,.92), rgba(4,8,22,.97));
      display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 34px; }}
    #ov-end img {{ width: 420px; }}
    #ov-end .l1 {{ color: #fff; font-weight: 900; font-size: 96px; line-height: 1.05; text-align: center; }}
    #ov-end .l1 span {{ color: #FFC20E; }}
    #ov-end .l2 {{ font-size: 60px; }}
    #ov-end .l3 {{ color: #fff; font-weight: 800; font-size: 50px; margin-top: -10px; }}
  </style>
  <div id="root" data-composition-id="overlays" data-width="1080" data-height="1920" data-layout-allow-overlap>
    <div id="ov-andrey" class="abs"><div class="card"><img src="assets/andrey.jpg" alt="" /><div class="x">✕</div><div class="name">אנדריי X</div></div></div>
    <div id="ov-nname" class="abs lt"><div class="lt-name">נטלי דדון</div></div>
    <div id="ov-tamir" class="abs lt"><div class="lt-name">תמיר דורטל</div><div class="lt-sub">מייסד כח התערבות</div></div>
    <div id="ov-flash" class="abs"></div>
    <div id="ov-stamp" class="abs"><div class="s">הלחץ עובד!</div></div>
    <div id="ov-letter" class="abs"><div class="paper"><div class="zoom"><img src="assets/letter-top.png" alt="" /><div class="hl"></div></div></div><div class="tag"><div class="chip red">מכתב רשמי לשר הפנים</div></div></div>
    <div id="ov-chikli" class="abs"><div class="chip">👏 כל הכבוד לשר עמיחי שיקלי</div></div>
    <div id="ov-gideon" class="abs"><div class="box"><div class="hz t"></div><div class="gline">⚠️ גדעון סער, הכדור אצלך!</div><div class="hz b"></div></div></div>
    <div id="ov-cta" class="abs">
      <div id="cta-0" class="chip">👍 לייק</div>
      <div id="cta-1" class="chip">🔁 תשתפו</div>
      <div id="cta-2" class="chip">💬 תגיבו</div>
      <div id="cta-3" class="chip red">תתייגו @גדעון סער</div>
    </div>
    <div id="ov-end" class="abs">
      <img src="assets/logo.png" alt="" />
      <div class="l1">הלחץ <span>עובד.</span><br />ממשיכים.</div>
      <div class="chip l2">💛 תמכו בפעילות שלנו</div>
      <div class="l3">כדי שנמשיך ללחוץ 👇</div>
    </div>
  </div>
  <script>
  const tl = gsap.timeline({{ paused: true }});
  const ALL = ["#ov-andrey","#ov-nname","#ov-tamir","#ov-stamp","#ov-letter","#ov-chikli","#ov-gideon","#ov-cta","#ov-end"];
  tl.set(ALL, {{ opacity: 0 }}, 0);
  function show(sel, s, e, from) {{
    tl.fromTo(sel, Object.assign({{ opacity: 0 }}, from), {{ opacity: 1, x: 0, y: 0, scale: 1, rotation: 0, duration: 0.32, ease: "back.out(1.8)" }}, s);
    tl.to(sel, {{ opacity: 0, scale: 0.9, duration: 0.2, ease: "power2.in" }}, e - 0.2);
  }}
  // Andrey hero: slam in with X stamp
  show("#ov-andrey", 0.10, 3.70, {{ scale: 1.6, rotation: -14 }});
  tl.fromTo("#ov-andrey .x", {{ opacity: 0, scale: 2.4 }}, {{ opacity: 0.9, scale: 1, duration: 0.18, ease: "power4.in" }}, 0.55);
  // Natalie
  // Andrey thumb keeps face on screen during background
  // Natalie name + Tamir title
  show("#ov-nname", 3.95, 10.10, {{ x: 260 }});
  show("#ov-tamir", 0.30, 3.70, {{ x: 300 }});
  show("#ov-tamir", 10.30, 13.10, {{ x: 300 }});
  tl.set("#ov-flash", {{ opacity: 0 }}, 0);
  tl.fromTo("#ov-flash", {{ opacity: 0.85 }}, {{ opacity: 0, duration: 0.25, ease: "power2.out", immediateRender: false }}, 3.75);
  tl.fromTo("#ov-flash", {{ opacity: 0.85 }}, {{ opacity: 0, duration: 0.25, ease: "power2.out", immediateRender: false }}, 10.20);
  // Stamp
  show("#ov-stamp", 10.95, 12.05, {{ scale: 2.8, rotation: 12 }});
  // Letter: in, zoom to subject line, highlight sweep
  show("#ov-letter", 11.90, 15.10, {{ y: 900 }});
  tl.fromTo("#ov-letter .zoom", {{ scale: 1 }}, {{ scale: 1.65, duration: 1.6, ease: "power2.inOut" }}, 12.6);
  tl.fromTo("#ov-letter .hl", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.5, ease: "power2.out" }}, 13.4);
  tl.fromTo("#ov-letter .tag", {{ opacity: 0, y: -30 }}, {{ opacity: 1, y: 0, duration: 0.25, ease: "back.out(2)" }}, 12.2);
  // Chikli
  show("#ov-chikli", 14.75, 17.75, {{ y: 120 }});
  // Gideon
  show("#ov-gideon", 21.55, 25.60, {{ scale: 0.3, rotation: -6 }});
  tl.to("#ov-gideon .box", {{ x: 10, duration: 0.05, yoyo: true, repeat: 5, ease: "none" }}, 22.7);
  tl.fromTo("#ov-gideon .box", {{ scale: 1 }}, {{ scale: 1.06, duration: 0.3, yoyo: true, repeat: 5, ease: "sine.inOut" }}, 23.0);
  // CTA
  tl.set("#ov-cta", {{ opacity: 1 }}, 27.55);
  ["#cta-0","#cta-1","#cta-2","#cta-3"].forEach((c, i) => {{
    const t = [27.60, 27.89, 28.20, 28.50][i];
    tl.fromTo(c, {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.28, ease: "back.out(2.2)" }}, t);
  }});
  tl.to("#ov-cta", {{ opacity: 0, duration: 0.25 }}, 31.40);
  // End card
  tl.fromTo("#ov-end", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: "power2.out" }}, {END_SPEECH:.2f});
  tl.fromTo("#ov-end img", {{ scale: 0.6 }}, {{ scale: 1, duration: 0.5, ease: "back.out(1.7)" }}, {END_SPEECH:.2f});
  tl.fromTo("#ov-end .l1", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.35 }}, {END_SPEECH + 0.3:.2f});
  tl.fromTo("#ov-end .l2", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2.4)" }}, {END_SPEECH + 0.7:.2f});
  tl.fromTo("#ov-end .l3", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "power2.out" }}, {END_SPEECH + 1.1:.2f});
  tl.to("#ov-end .l2", {{ scale: 1.06, duration: 0.35, yoyo: true, repeat: 3, ease: "sine.inOut" }}, {END_SPEECH + 1.4:.2f});
  window.__timelines["overlays"] = tl;
  </script>
</template>
"""

# ---------------- index ----------------
A1_START, A1_DUR = 13.85, 3.75
N_START, N_DUR = 1.05, 6.45
A2_START, A2_DUR = 20.64, 11.04
B_START, B_DUR = 38.42, 13.98
sfx = [  # (file, start, dur, vol)
    ("whoosh", 0.05, 0.9, 0.5), ("impact", 0.55, 1.2, 0.55), ("whoosh", 1.65, 0.9, 0.35),
    ("whoosh", 3.75, 0.9, 0.35), ("impact", 10.95, 1.5, 0.8), ("whoosh", 11.85, 0.9, 0.45),
    ("whoosh", 14.70, 0.9, 0.3), ("impact", 21.55, 1.2, 0.6), ("whoosh", 27.55, 0.9, 0.4),
    ("impact", END_SPEECH, 1.5, 0.6),
]
sfx = [(f, st + D if 6.79 <= st < 32 else st, d, v) for (f, st, d, v) in sfx if not (f == "whoosh" and st == 3.75)]
sfx = [x for x in sfx if not (x[0] == "whoosh" and abs(x[1] - 1.65) < 0.01)]
sfx += [("pop", 0.30, 0.2, 0.55), ("pop", 3.95, 0.2, 0.55), ("pop", 10.30, 0.2, 0.55),
        ("pop", 15.61, 0.2, 0.5), ("sparkle", 16.81, 1.3, 0.35),
        ("pop", 18.16, 0.2, 0.55), ("applause", 18.20, 3.0, 0.45),
        ("alarm", 24.98, 0.9, 0.5), ("pop", 24.96, 0.2, 0.6), ("glitch", 26.11, 0.5, 0.4), ("alarm", 27.0, 0.9, 0.3),
        ("shutter", 15.40, 0.65, 0.6), ("riser", 12.45, 1.9, 0.3), ("impact", 12.16, 1.0, 0.35),
        ("like", 31.01, 0.5, 0.7), ("share", 31.28, 0.6, 0.65), ("pop", 31.61, 0.2, 0.6), ("ding", 31.91, 1.2, 0.45),
        ("pop", END_SPEECH + 0.7, 0.2, 0.6)]
sfx += [("glitch", 3.70, 0.5, 0.75), ("swipe", 3.68, 0.6, 0.6), ("glitch", 10.15, 0.5, 0.75), ("swipe", 10.13, 0.6, 0.6)]
sfx_html = "\n".join(
    f'      <audio id="sfx-{i}" class="clip" src="assets/{f}.mp3" data-start="{s:.2f}" data-duration="{d}" data-volume="{v}" data-track-index="{10 + (i % 4)}"></audio>'
    for i, (f, s, d, v) in enumerate(sfx)
)

index = f"""<!doctype html>
<html lang="he">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      #root {{ background: radial-gradient(ellipse at 50% 20%, #1a2a66, #050914 70%); }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; }}
      #cam {{ position: absolute; inset: 0; transform-origin: 50% 35%; }}
      #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
      #natfx {{ position: absolute; inset: 0; transform-origin: 50% 45%; }}
      #nat {{ position: absolute; inset: 0; transform: scale(1.6); transform-origin: 50% 0; }}
      #natscrim {{ position: absolute; left: 0; right: 0; top: 1420px; bottom: 0; background: linear-gradient(to bottom, rgba(0,0,0,0), rgba(0,0,0,1) 26%, #000); z-index: 1; }}
      #logo {{ position: absolute; right: 26px; top: 70px; width: 300px; z-index: 30; }}
      #overlays {{ z-index: 10; }}
      #captions {{ z-index: 20; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
      <div id="cam">
        <video id="tamir-a" class="clip" src="assets/tamir.mp4" data-start="0" data-duration="{A1_DUR}" data-media-start="{A1_START}" data-has-audio="true" data-volume="1" playsinline data-track-index="0"></video>
        <div id="natfx"><div id="nat"><video id="natali" class="clip" src="assets/natali.mp4" data-start="{A1_DUR}" data-duration="{N_DUR}" data-media-start="{N_START}" data-has-audio="true" data-volume="1.15" playsinline data-track-index="8"></video></div></div>
        <video id="tamir-a2" class="clip" src="assets/tamir.mp4" data-start="{A1_DUR + N_DUR:.2f}" data-duration="{A2_DUR}" data-media-start="{A2_START}" data-has-audio="true" data-volume="1" playsinline data-track-index="0"></video>
        <video id="tamir-b" class="clip" src="assets/tamir.mp4" data-start="{A1_DUR + N_DUR + A2_DUR:.2f}" data-duration="{B_DUR}" data-media-start="{B_START}" data-has-audio="true" data-volume="1" playsinline data-track-index="1"></video>
      </div>
      <img id="logo" class="clip" src="assets/logo-blue.png" alt="" data-start="0" data-duration="{END_SPEECH:.2f}" data-track-index="2" />
      <div id="overlays" data-composition-id="overlays" data-composition-src="compositions/overlays.html" data-start="0" data-duration="{TOTAL}" data-track-index="3" data-track-kind="graphics" data-width="1080" data-height="1920"></div>
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{END_SPEECH:.2f}" data-track-index="4" data-track-kind="captions" data-width="1080" data-height="1920"></div>
      <audio id="music-bed" class="clip" src="assets/music.mp3" data-start="0" data-duration="{END_SPEECH:.2f}" data-media-start="0" data-volume="0.16" data-fade-in="0.3" data-track-index="5"></audio>
      <audio id="music-end" class="clip" src="assets/music.mp3" data-start="{END_SPEECH:.2f}" data-duration="{TOTAL - END_SPEECH:.2f}" data-media-start="{END_SPEECH:.2f}" data-volume="0.55" data-fade-out="1.2" data-track-index="5"></audio>
{sfx_html}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      // punch-ins on emphasis (transform on the wrapper, not the videos)
      tl.set("#cam", {{ scale: 1 }}, 0);
      tl.set("#natfx", {{ scale: 1, rotation: 0 }}, 0);
      tl.fromTo("#natfx", {{ scale: 1.22, rotation: -2.5 }}, {{ scale: 1, rotation: 0, duration: 0.42, ease: "back.out(2.6)", immediateRender: false }}, 3.75);
      tl.to("#natfx", {{ scale: 1.14, rotation: 2, duration: 0.18, ease: "power2.in" }}, 10.02);
      tl.to("#cam", {{ scale: 1.12, duration: 0.12, ease: "power3.out" }}, 8.75);   // רוצחים
      tl.to("#cam", {{ scale: 1, duration: 0.25, ease: "power2.inOut" }}, 9.75);
      tl.to("#cam", {{ scale: 1.15, duration: 0.10, ease: "power4.out" }}, 11.0);   // עובד!
      tl.to("#cam", {{ scale: 1, duration: 0.25, ease: "power2.inOut" }}, 11.55);
      // split: letter
      tl.set("#cam", {{ transformOrigin: "50% 100%" }}, 11.84);
      tl.to("#cam", {{ scale: 0.6, duration: 0.35, ease: "power3.inOut" }}, 11.85);
      tl.to("#cam", {{ scale: 1, duration: 0.35, ease: "power3.inOut" }}, 15.05);
      tl.set("#cam", {{ transformOrigin: "50% 35%" }}, 15.41);
      tl.to("#cam", {{ scale: 1.08, duration: 3.9, ease: "none" }}, 27.6);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

import re
KEEP = {"10.20", "10.30", "13.10", "10.10"}  # already on the new timeline
def shift_scripts(doc):
    def fix_script(m):
        body = m.group(0)
        def num(mm):
            pre, v = mm.group(1), mm.group(2)
            if "duration" in pre or v in KEEP: return mm.group(0)
            x = float(v)
            return pre + (f"{x + D:.2f}" if x >= 6.79 and x < 32 else v)
        return re.sub(r'((?:duration:\s*)?)(?<![\w.#-])(\d+\.\d+)(?![\d.]*(?:px|%|em|s\b))', num, body)
    return re.sub(r'<script>(?:(?!</script>).)*</script>', fix_script, doc, flags=re.S)
overlays = shift_scripts(overlays)
index = shift_scripts(index)
os.makedirs(os.path.join(P, "compositions"), exist_ok=True)
open(os.path.join(P, "index.html"), "w").write(index)
open(os.path.join(P, "compositions/captions.html"), "w").write(captions)
open(os.path.join(P, "compositions/overlays.html"), "w").write(overlays)
print("ok")
