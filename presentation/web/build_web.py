"""Render the scroll-story web version of the deck from the same data files.

Run: python3 presentation/web/build_web.py  ->  presentation/web/index.html
"""
import base64
import json
from html import escape as e
from pathlib import Path

HERE = Path(__file__).parent
PRES = HERE.parent
ROOT = PRES.parent

people = json.loads((PRES / "people.json").read_text(encoding="utf-8"))
plans = json.loads((PRES / "plans.json").read_text(encoding="utf-8"))
AV_LABEL = {"high": "גבוהה", "medium": "בינונית", "low": "נמוכה"}
AV_VAR = {"high": "--hi", "medium": "--mid", "low": "--low"}


def chip(name, avail, i, big=False, extra=""):
    cls = "p big" if big else "p"
    a = avail or "none"
    return f'<span class="{cls}" data-a="{a}" style="--i:{i}">{e(name)}{extra}</span>'


# ---- act 1: today -------------------------------------------------------
seen = {}
for m in people["board"]["members"]:
    seen[m["name"]] = m["availability"]
seen[people["ceo"]["name"]] = people["ceo"]["availability"]
n_groups = 0
idx = 0


def group_html(g, title_prefix=""):
    global n_groups, idx
    n_groups += 1
    head = g["head"]
    seen[head["name"]] = head["availability"]
    out = [f'<h3>{e(g["title"])}</h3>',
           f'<div class="lead">{e(head.get("role", "ראש צוות"))}: </div>']
    out[1] = f'<div class="chips">{chip(head["name"] + " · " + head.get("role", "ראש צוות"), head["availability"], idx, True)}</div>'
    idx += 1
    chips = []
    for m in g["members"]:
        seen[m["name"]] = m["availability"]
        note = f' <small>({e(m["note"])})</small>' if m.get("note") else ""
        chips.append(chip(m["name"], m["availability"], idx, extra=note))
        idx += 1
    out.append('<div class="chips" style="margin-top:8px">' + "".join(chips) + "</div>")
    if g.get("sub"):
        out.append('<div class="sub">' + group_html(g["sub"]) + "</div>")
    return "".join(out)


board = "".join(chip(m["name"], m["availability"], i, True) for i, m in enumerate(people["board"]["members"]))
ceo = people["ceo"]
teams = "".join(f'<div class="team">{group_html(t)}</div>' for t in people["teams"])
org = (f'<div class="org"><div class="tierlabel">דירקטוריון</div><div class="tier">{board}</div>'
       f'<div class="tierlabel">מנכ״ל</div><div class="tier">{chip(ceo["name"], ceo["availability"], 8, True)}</div>'
       f'<div class="teams">{teams}</div></div>')
counts = {}
for v in seen.values():
    counts[v] = counts.get(v, 0) + 1
legend = "".join(f'<span><i style="background:var({AV_VAR[k]})"></i>{counts.get(k, 0)} · {AV_LABEL[k]}</span>'
                 for k in ("high", "medium", "low"))

# ---- act 2: rings -------------------------------------------------------
pr = people["proposal"]
rg = pr["rings"]
C = 300


def pill(cx, cy, w, title, lead, dark):
    fill = "var(--navy)" if dark else "var(--surface)"
    stroke = "none" if dark else "var(--navy)"
    t1 = "var(--navy-ink)" if dark else "var(--navy)"
    t2 = "var(--gold)" if dark else "var(--muted)"
    return (f'<g><rect x="{cx - w / 2}" y="{cy - 27}" width="{w}" height="54" rx="27" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
            f'<text x="{cx}" y="{cy - 3}" text-anchor="middle" direction="rtl" font-size="17" font-weight="800" fill="{t1}">{e(title)}</text>'
            f'<text x="{cx}" y="{cy + 17}" text-anchor="middle" direction="rtl" font-size="12.5" fill="{t2}">{e(lead)}</text></g>')


mid_pos = {"top": (0, -150), "right": (112, 122), "left": (-112, 122)}
out_pos = {"top": (0, -238), "right": (176, 196), "left": (-176, 196)}
core = rg["core"]
core_lines = "".join(
    f'<text x="{C}" y="{C - 10 + i * 24}" text-anchor="middle" direction="rtl" font-size="{15 if i < len(core["lines"]) - 1 else 15}" '
    f'font-weight="{800 if i == len(core["lines"]) - 1 else 500}" fill="var(--gold-ink)">{e(l)}</text>'
    for i, l in enumerate(core["lines"]))
rings = (
    '<svg viewBox="0 0 600 600" role="img" aria-label="המבנה המוצע: צוות הכנסת במרכז, צוותי תמיכה סביבו, ומעגל ההשפעה בחוץ">'
    f'<circle class="r r3" cx="{C}" cy="{C}" r="285" fill="var(--ring-1)" stroke="var(--line)" stroke-width="2"/>'
    f'<circle class="r r2" cx="{C}" cy="{C}" r="195" fill="var(--ring-2)" stroke="var(--line)" stroke-width="2"/>'
    f'<circle class="r r1" cx="{C}" cy="{C}" r="110" fill="var(--gold)"/>'
    f'<text x="{C}" y="{C - 72}" text-anchor="middle" direction="rtl" font-size="13" fill="var(--gold-ink)">{e(core["label"])}</text>'
    f'<text x="{C}" y="{C - 40}" text-anchor="middle" direction="rtl" font-size="26" fill="var(--gold-ink)" style="font-family:var(--display)">{e(core["title"])}</text>'
    + core_lines
    + "".join(pill(C + mid_pos[it["pos"]][0], C + mid_pos[it["pos"]][1], 190, it["title"], it["lead"], True) for it in rg["middle"])
    + "".join(pill(C + out_pos[it["pos"]][0], C + out_pos[it["pos"]][1], 230, it["title"], it["lead"], False) for it in rg["outer"])
    + "</svg>")
side = "".join(f'<div class="kpi">{e(k)}</div>' for k in pr["core"]["kpis"])
side += "".join(f'<div class="note"><h3>{e(n["title"])}</h3><p>{e(n["line"])}</p></div>' for n in pr["notes"])

# ---- act 4: week --------------------------------------------------------
act = people["activity"]
kpis = "".join(f'<div><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in act["kpis"])
week = "".join(f'<div class="day{" k" if k else ""}" style="--i:{i}"><small>{e(d)}</small><b>{e(w)}</b><p>{e(l)}</p></div>'
               for i, (d, w, l, k) in enumerate(act["days"]))
pl = act["planning"]
week += f'<div class="plan"><b>{e(pl["title"])}</b><span>{e(pl["line"])}</span></div>'
who = act["who"]
who_chips = "".join(
    f'<span class="p big{" dash" if r == "נציג רביעי" else ""}">{e(r)}</span>' for r in who["reps"])
ct = act["content"]
who_html = (f'<div class="box"><h3>{e(who["title"])}</h3><div class="chips">{who_chips}</div>'
            f'<p class="muted">{e(who["fourth_note"])}</p><p style="margin:0;font-weight:700">+ {e(who["support"])}</p></div>'
            f'<div class="box gold"><h3>{e(ct["title"])}</h3><p class="muted">{e(ct["sub"])}</p>'
            '<ul>' + "".join(f"<li><b>{e(x)}</b></li>" for x in ct["lines"]) + "</ul></div>")

# ---- act 5: budget ------------------------------------------------------
sa, sb = people["stages"]


def stage_html(s, cls, label):
    rows = "".join(
        f'<tr><td>{e(r[0])}</td><td class="num">{e(r[1])}</td>'
        f'<td><span class="chg{"" if r[2].startswith("+") else " n"}">{e(r[2])}</span></td></tr>' for r in s["rows"])
    disc = s["kpis"][0][0]
    return (f'<div class="stage {cls}"><div class="lbl">{e(label)}</div><div class="big num">{e(s["monthly"])}</div>'
            f'<div class="muted">לחודש · {e(s["yearly"])} · {e(disc)} דיונים בחודש</div><table>{rows}</table></div>')


def money(s):
    return int(s.replace(",", "").replace("₪", "").strip())


diff = money(sb["monthly"]) - money(sa["monthly"])
stages = (stage_html(sa, "a", sa["title"]) +
          f'<div class="arrow" aria-hidden="true">←<small>+{diff:,} ₪</small></div>' +
          stage_html(sb, "b", sb["title"]))
why = (f'<h3>{e(sb["box"]["title"])}</h3><ul>' + "".join(f"<li>{e(x)}</li>" for x in sb["box"]["lines"]) + "</ul>")
ms = people["costs"]["models"]
top = max(money(m["monthly"]) for m in ms)
models = "".join(
    f'<div class="model{" hl" if m.get("recommended") else ""}"><div class="n">{e(m["name"])}<small>{e(m["tag"])}</small></div>'
    f'<div class="bar"><i style="--w:{money(m["monthly"]) / top * 100:.1f}%" data-w="{money(m["monthly"]) / top * 100:.1f}%"></i></div>'
    f'<div class="v num">{e(m["monthly"])}</div></div>' for m in ms)

logo = "data:image/png;base64," + base64.b64encode((ROOT / "assets" / "logo.png").read_bytes()).decode()
programs = [{"name": x["name"], "headline": x.get("headline", x["domain"]), "items": x["items"]} for x in plans["programs"]]

html = (HERE / "template.html").read_text(encoding="utf-8")
for k, v in {
    "__LOGO__": logo, "__PEOPLE__": str(len(seen)), "__GROUPS__": str(n_groups), "__HIGH__": str(counts.get("high", 0)),
    "__LEGEND__": legend, "__ORG__": org, "__RINGS__": rings, "__SIDE__": side, "__KPIS__": kpis, "__WEEK__": week,
    "__WHO__": who_html, "__STAGES__": stages, "__WHY__": why, "__MODELS__": models,
    "__PROGRAMS__": json.dumps(programs, ensure_ascii=False),
}.items():
    html = html.replace(k, v)
(HERE / "index.html").write_text(html, encoding="utf-8")
print(HERE / "index.html", len(html))
