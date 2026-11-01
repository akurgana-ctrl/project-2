"""Generates tamir/index.html (HyperFrames composition) from edit.json. usage: build_html.py <scratch> <total>"""
import json, sys, html
S, TOTAL = sys.argv[1], float(sys.argv[2])
E = json.load(open(f"{S}/edit.json"))
words, cuts = E["words"], E["cuts"]

KEY = {"פוף!", "נשלל.", "2,600", "רישיונות", "נשק", "בוטלו", "ביום.", "חור", "בספינה.", "אקדח.", "הרישיון", "הרישיון.",
       "שוללים?", "בכלל.", "עתירות:", "תשובות:", "ותתמכו", "בנו", "פקיד,", "בלי", "שם", "״תיענה", "בהקדם״.",
       "חלקית", "וסירבה", "המון", "כסף", "מרוקן", "חמוש", "איך,", "למה", "וכמה."}

# ---- caption groups: max 3 words, break on punctuation / pause >= 0.15 s / segment change
groups, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    end_punct = w["text"][-1] in ".,:?!״"
    if (len(cur) >= 3 or end_punct or nxt is None or nxt["seg"] != w["seg"]
            or nxt["start"] - w["end"] >= 0.15 or (len(cur) == 2 and len(nxt["text"]) + sum(len(x["text"]) for x in cur) > 17)):
        groups.append(cur); cur = []

cap_html, cap_js = [], []
for gi, g in enumerate(groups):
    st = max(0.05, g[0]["start"] - 0.05)
    nxt_st = groups[gi + 1][0]["start"] - 0.05 if gi + 1 < len(groups) else TOTAL
    en = min(max(g[-1]["end"] + 0.25, st + 0.5), nxt_st, 55.25)
    spans = []
    for wi, w in enumerate(g):
        cls = "w key" if w["text"] in KEY else "w"
        spans.append(f'<span id="c{gi}w{wi}" class="{cls}">{html.escape(w["text"])}</span>')
        cap_js.append(f'tl.fromTo("#c{gi}w{wi}",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.14,ease:"back.out(2.4)"}},{max(st, w["start"] - 0.04):.3f});')
    cap_html.append(f'<div id="cap{gi}" class="capgrp">{" ".join(spans)}</div>')
    cap_js.append(f'tl.set("#cap{gi}",{{opacity:1,visibility:"visible"}},{st:.3f});'
                  f'tl.to("#cap{gi}",{{opacity:0,duration:0.08}},{en - 0.08:.3f});tl.set("#cap{gi}",{{opacity:0,visibility:"hidden"}},{en:.3f});')

# ---- punch-ins at every jump cut (alternate framing hides the cut)
SCALES = [1.14, 1.0, 1.1, 1.0, 1.12, 1.0, 1.08, 1.0, 1.12, 1.0, 1.06]
punch_js = [f'tl.set("#cam",{{scale:{SCALES[k % len(SCALES)]}}},{c:.3f});' for k, c in enumerate(cuts)]
# extra emphasis punches inside long takes
for at, sc in [(15.28, 1.18), (17.23, 1.24), (31.88, 1.0), (32.6, 1.16), (46.43, 1.14), (49.53, 1.0)]:
    punch_js.append(f'tl.to("#cam",{{scale:{sc},duration:0.25,ease:"power3.out"}},{at});')

caps = "\n".join(cap_html)
cap_script = "\n".join(cap_js)
punch_script = "\n".join(punch_js)

HTML = open(f"{S}/scripts/template.html", encoding="utf8").read()
HTML = (HTML.replace("{{TOTAL}}", f"{TOTAL}").replace("{{CAPTIONS}}", caps)
        .replace("{{CAPTION_JS}}", cap_script).replace("{{PUNCH_JS}}", punch_script))
open(f"{S}/tamir/index.html", "w", encoding="utf8").write(HTML)
print("groups", len(groups))
