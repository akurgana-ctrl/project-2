"""Build the כח התערבות deck (PPTX, Canva-importable) from people.json.

Every element is a native shape/text box so it stays editable after import.
Run: python3 presentation/build.py
"""
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = HERE / "out" / "koach-hitarvut.pptx"

FONT = "Heebo"
NAVY = RGBColor(0x1C, 0x3C, 0x7A)
NAVY_DARK = RGBColor(0x12, 0x27, 0x55)
GOLD = RGBColor(0xF0, 0xC0, 0x00)
BG = RGBColor(0xF4, 0xF6, 0xFB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x1A, 0x22, 0x33)
MUTED = RGBColor(0x8A, 0x94, 0xA8)
LINE = RGBColor(0xC5, 0xCD, 0xDD)
# muted "before" look for the existing-structure slides
SLATE = RGBColor(0x4A, 0x55, 0x68)
SLATE_LINE = RGBColor(0xA0, 0xAE, 0xC0)
MUTED_CARD = RGBColor(0xE6, 0xE9, 0xEF)
MUTED_TEXT = RGBColor(0x5B, 0x64, 0x75)
STYLE = {"muted": False}

AVAIL = {
    "high": ("זמינות גבוהה", RGBColor(0x2E, 0x9E, 0x6A)),
    "medium": ("זמינות בינונית", RGBColor(0xE8, 0x89, 0x2B)),
    "low": ("זמינות נמוכה", RGBColor(0xD6, 0x45, 0x45)),
    None: ("טרם הוזן", RGBColor(0xB4, 0xBC, 0xCC)),
}

W, H = Inches(13.333), Inches(7.5)


def text(slide, x, y, w, h, s, size, color=INK, bold=False, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, rtl=True):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.04)
    tf.margin_top = tf.margin_bottom = 0
    style_para(tf.paragraphs[0], s, size, color, bold, align, rtl)
    return box


def style_para(p, s, size, color, bold, align, rtl=True):
    p.alignment = align
    p._p.get_or_add_pPr().set("rtl", "1" if rtl else "0")
    r = p.add_run()
    r.text = s
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.name = FONT
    rpr = r._r.get_or_add_rPr()
    cs = rpr.makeelement(qn("a:cs"), {"typeface": FONT})
    rpr.append(cs)


def rect(slide, x, y, w, h, fill, line=None, radius=0.18, dashed=False):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shp.adjustments[0] = radius
    shp.shadow.inherit = False
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1.25)
        if dashed:
            shp.line.dash_style = 4  # dash
    return shp


def card(slide, x, y, w, h, name, role, avail, colored, size=12, note=None):
    """A person card. colored=False -> brand look; True -> availability color."""
    empty = not name
    if colored:
        fill = AVAIL[avail][1]
        rect(slide, x, y, w, h, fill)
        fg, sub = WHITE, WHITE
    elif empty:
        rect(slide, x, y, w, h, BG, line=MUTED, dashed=True)
        fg, sub = MUTED, MUTED
    elif STYLE["muted"]:
        rect(slide, x, y, w, h, MUTED_CARD)
        fg, sub = MUTED_TEXT, MUTED
    else:
        rect(slide, x, y, w, h, WHITE, line=LINE)
        # gold accent strip on the right (RTL start)
        strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x + w - Inches(0.07), y + Inches(0.08),
                                       Inches(0.05), h - Inches(0.16))
        strip.fill.solid()
        strip.fill.fore_color.rgb = GOLD
        strip.line.fill.background()
        strip.shadow.inherit = False
        fg, sub = INK, MUTED
    label = name or "שם יעודכן"
    if role:
        text(slide, x, y + Inches(0.06), w, h * 0.52, label, size, fg, bold=True, anchor=MSO_ANCHOR.BOTTOM)
        text(slide, x, y + h * 0.55, w, h * 0.4, role, 9, sub, anchor=MSO_ANCHOR.TOP)
    else:
        if note:  # short responsibility on a small second line
            text(slide, x, y, w, h * 0.6, label, size - 1, fg, bold=True, anchor=MSO_ANCHOR.BOTTOM)
            text(slide, x, y + h * 0.58, w, h * 0.4, f"({note})", 8, sub, anchor=MSO_ANCHOR.TOP)
        else:
            text(slide, x, y, w, h, label, size, fg, bold=True)


def connector(slide, x1, y1, x2, y2):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = LINE
    c.line.width = Pt(1.5)


def header(slide, title, subtitle, bar_color=NAVY, accent=GOLD):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = BG
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Inches(0.95))
    bar.fill.solid()
    bar.fill.fore_color.rgb = bar_color
    bar.line.fill.background()
    bar.shadow.inherit = False
    gold = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(0.95), W, Inches(0.06))
    gold.fill.solid()
    gold.fill.fore_color.rgb = accent
    gold.line.fill.background()
    gold.shadow.inherit = False
    text(slide, Inches(1.4), Inches(0.12), Inches(11.5), Inches(0.5), title, 26, WHITE, bold=True,
         align=PP_ALIGN.RIGHT)
    if subtitle:
        text(slide, Inches(1.4), Inches(0.58), Inches(11.5), Inches(0.3), subtitle, 12, GOLD,
             align=PP_ALIGN.RIGHT)
    slide.shapes.add_picture(str(ROOT / "assets" / "logo.png"), Inches(0.35), Inches(0.08),
                             height=Inches(0.8))
    # white plate behind logo so it reads on navy
    plate = slide.shapes[-1]
    pl = rect(slide, plate.left - Inches(0.06), plate.top - Inches(0.02),
              plate.width + Inches(0.12), plate.height + Inches(0.04), WHITE, radius=0.12)
    slide.shapes._spTree.remove(pl._element)
    slide.shapes._spTree.insert(slide.shapes._spTree.index(plate._element), pl._element)


def legend(slide, counts=None):
    counts = counts or {}
    items = ["high", "medium", "low"] + ([None] if counts.get(None) else [])
    # sits in the navy header bar, between the logo and the title
    x = Inches(7.4)
    y = Inches(0.33)
    for k in items:
        label, color = AVAIL[k]
        w = Inches(1.45)
        x -= w
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, x + w - Inches(0.22), y + Inches(0.08),
                                     Inches(0.16), Inches(0.16))
        dot.fill.solid()
        dot.fill.fore_color.rgb = color
        dot.line.fill.background()
        dot.shadow.inherit = False
        if k in counts:
            label = f"{counts[k]} · {label.replace('זמינות ', '')}"
        text(slide, x, y, w - Inches(0.28), Inches(0.32), label, 11 if counts else 10, WHITE, bold=bool(counts),
             align=PP_ALIGN.RIGHT)


def arrow(slide, x1, y1, x2, y2, color=NAVY):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = color
    c.line.width = Pt(2)
    ln = c.line._get_or_add_ln()
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))


def badge(slide, x, y, label="חדש"):
    b = rect(slide, x, y, Inches(0.55), Inches(0.24), GOLD, radius=0.5)
    text(slide, x, y, Inches(0.55), Inches(0.24), label, 9, NAVY_DARK, bold=True)


def info_box(slide, x, y, w, h, block, accent=NAVY):
    """Side unit: title bar, lead name, short bullet lines."""
    rect(slide, x, y, w, h, WHITE, line=LINE, radius=0.06)
    bar = rect(slide, x, y, w, Inches(0.42), accent, radius=0.2)
    text(slide, x, y, w, Inches(0.42), block["title"], 14, WHITE, bold=True)
    text(slide, x, y + Inches(0.5), w, Inches(0.3), block["lead"], 11, INK, bold=True)
    ty = y + Inches(0.85)
    for line in block["lines"]:
        text(slide, x + Inches(0.15), ty, w - Inches(0.3), Inches(0.3), "• " + line, 11, INK,
             align=PP_ALIGN.RIGHT)
        ty += Inches(0.3)


def num_dot(slide, x, y, d, label, fill=NAVY, color=WHITE):
    dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, d, d)
    dot.fill.solid()
    dot.fill.fore_color.rgb = fill
    dot.line.fill.background()
    dot.shadow.inherit = False
    text(slide, x - Inches(0.1), y, d + Inches(0.2), d, label, 12 if len(label) < 3 else 10, color, bold=True,
         rtl=False)


def programs_slide(prs, leader):
    """Programs only: numbered cards, no work plan (that lives in the appendices)."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    header(s, f'תוכניות כנסת 26 · {leader["name"]}', leader.get("headline", leader["domain"]))
    margin = Inches(0.45)
    items = leader["items"]
    n = len(items)
    cols = 1 if n <= 5 else 2
    rows = -(-n // cols)
    top, bottom = Inches(1.35), Inches(7.1)
    gap = Inches(0.16)
    ch = min(Inches(2.2) if n <= 2 else Inches(1.1), int((bottom - top - gap * (rows - 1)) / rows))
    cw = int((W - 2 * margin - gap * (cols - 1)) / cols)
    size = 24 if n <= 2 else 16 if n <= 5 else 12
    d = Inches(0.5) if n <= 5 else Inches(0.36)
    for i, (num, title, *rest) in enumerate(items):
        tag = rest[0] if rest else ""
        c, r = divmod(i, rows)  # fill the right column first
        x = W - margin - (c + 1) * cw - c * gap
        y = top + r * (ch + gap)
        rect(s, x, y, cw, ch, WHITE, line=LINE, radius=0.12 if n > 5 else 0.08)
        strip = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x + cw - Inches(0.08), y + Inches(0.1),
                                   Inches(0.06), ch - Inches(0.2))
        strip.fill.solid()
        strip.fill.fore_color.rgb = GOLD
        strip.line.fill.background()
        strip.shadow.inherit = False
        num_dot(s, x + cw - Inches(0.25) - d, y + (ch - d) // 2, d, num)
        tw = Inches(1.9) if cols == 1 else Inches(1.45)
        if tag:  # the field this program belongs to, as a chip at the line's end
            th = Inches(0.36) if n <= 5 else Inches(0.3)
            rect(s, x + Inches(0.2), y + (ch - th) // 2, tw, th, BG, line=GOLD, radius=0.5)
            text(s, x + Inches(0.2), y + (ch - th) // 2, tw, th, tag, 11 if n <= 5 else 9, NAVY, bold=True)
        text(s, x + Inches(0.3) + (tw if tag else 0), y, cw - d - Inches(0.7) - (tw if tag else 0), ch, title, size, INK,
             bold=True, align=PP_ALIGN.RIGHT)
    return s


def appendix_stages(prs, block):
    """One row per program, its stages flowing right-to-left as steps."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    header(s, block["title"], block["subtitle"])
    margin = Inches(0.45)
    progs = block["programs"]
    top, bottom = Inches(1.25), Inches(7.2)
    gap = Inches(0.14)
    rh = min(Inches(1.7), int((bottom - top - gap * (len(progs) - 1)) / len(progs)))
    tw = Inches(2.9)
    for i, pg in enumerate(progs):
        y = top + i * (rh + gap)
        rect(s, margin, y, W - 2 * margin, rh, WHITE, line=LINE, radius=0.06)
        tx = W - margin - tw
        num_dot(s, W - margin - Inches(0.5), y + (rh - Inches(0.38)) // 2, Inches(0.38), pg["num"])
        text(s, tx, y, tw - Inches(0.6), rh, pg["title"], 13, NAVY, bold=True, align=PP_ALIGN.RIGHT)
        st = pg["stages"]
        area_r = tx - Inches(0.1)
        area_l = margin + Inches(0.12)
        sgap = Inches(0.22)
        n = 5  # fixed grid so stage k lines up across programs
        sw = int((area_r - area_l - sgap * (n - 1)) / n)
        sh = rh - Inches(0.24)
        sy = y + Inches(0.12)
        for k, (what, who, when) in enumerate(st):
            x = area_r - (k + 1) * sw - k * sgap
            rect(s, x, sy, sw, sh, BG, line=None, radius=0.1)
            text(s, x + Inches(0.06), sy + Inches(0.04), sw - Inches(0.12), sh * 0.58, what, 11, INK,
                 bold=True, anchor=MSO_ANCHOR.MIDDLE)
            text(s, x + Inches(0.06), sy + sh * 0.6, sw - Inches(0.12), sh * 0.2, who, 9, NAVY)
            text(s, x + Inches(0.06), sy + sh * 0.78, sw - Inches(0.12), sh * 0.2, when, 9, MUTED)
            if k:
                arrow(s, x + sw + sgap - Inches(0.03), sy + sh // 2, x + sw + Inches(0.03), sy + sh // 2, GOLD)
    return s


def appendix_table(prs, block):
    """Grouped rows: # | program | track | committee | first step. Gold strip marks flagship items."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    header(s, block["title"], block["subtitle"])
    margin = Inches(0.45)
    cols = [("", 0.5), ("תוכנית", 5.0), ("מסלול פעולה", 2.2), ("ועדה", 2.0), ("צעד ראשון", 2.73)]
    xs, x = [], W - margin
    for _, wi in cols:
        x -= Inches(wi)
        xs.append(x)
    y = Inches(1.2)
    hh = Inches(0.36)
    rect(s, margin, y, W - 2 * margin, hh, NAVY, radius=0.15)
    for (label, wi), cx in zip(cols, xs):
        text(s, cx + Inches(0.08), y, Inches(wi) - Inches(0.16), hh, label, 11, WHITE, bold=True,
             align=PP_ALIGN.RIGHT)
    y += hh + Inches(0.08)
    nrows = sum(len(sec["rows"]) for sec in block["sections"])
    avail = Inches(6.95) - y - len(block["sections"]) * Inches(0.38)
    rh = min(Inches(0.6), int(avail / nrows))
    for sec in block["sections"]:
        text(s, margin, y, W - 2 * margin, Inches(0.34), sec["title"], 13, NAVY, bold=True,
             align=PP_ALIGN.RIGHT)
        y += Inches(0.38)
        for num, prog, track, com, step, flag in sec["rows"]:
            rect(s, margin, y, W - 2 * margin, rh - Inches(0.06), WHITE, line=LINE, radius=0.12)
            if flag:
                strip = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, W - margin - Inches(0.07), y + Inches(0.06),
                                           Inches(0.06), rh - Inches(0.18))
                strip.fill.solid()
                strip.fill.fore_color.rgb = GOLD
                strip.line.fill.background()
                strip.shadow.inherit = False
            cells = [num, prog, track, com, step]
            for (label, wi), cx, val, ci in zip(cols, xs, cells, range(5)):
                if ci == 0:
                    num_dot(s, cx + (Inches(wi) - Inches(0.32)) // 2, y + (rh - Inches(0.06) - Inches(0.32)) // 2,
                            Inches(0.32), val, fill=GOLD if flag else NAVY, color=NAVY_DARK if flag else WHITE)
                    continue
                text(s, cx + Inches(0.08), y, Inches(wi) - Inches(0.16), rh - Inches(0.06), val,
                     11 if ci == 1 else 10, INK if ci in (1, 4) else NAVY, bold=(ci == 1), align=PP_ALIGN.RIGHT)
            y += rh
    # legend for flagship marker
    num_dot(s, margin, Inches(7.08), Inches(0.24), "", fill=GOLD)
    text(s, margin + Inches(0.3), Inches(7.04), Inches(3), Inches(0.32), "תוכנית דגל מומלצת", 10, INK,
         align=PP_ALIGN.LEFT)
    return s


def oval(slide, cx, cy, r, fill, line=None, width=1.5):
    o = slide.shapes.add_shape(MSO_SHAPE.OVAL, int(cx - r), int(cy - r), int(2 * r), int(2 * r))
    o.shadow.inherit = False
    o.fill.solid()
    o.fill.fore_color.rgb = fill
    if line is None:
        o.line.fill.background()
    else:
        o.line.color.rgb = line
        o.line.width = Pt(width)
    return o


def pill(slide, cx, cy, w, h, title, lead, fill, fg, sub):
    x, y = int(cx - w / 2), int(cy - h / 2)
    rect(slide, x, y, int(w), int(h), fill, line=None if fill != WHITE else NAVY, radius=0.5)
    text(slide, x, y + Inches(0.04), int(w), int(h * 0.5), title, 13, fg, bold=True, anchor=MSO_ANCHOR.BOTTOM)
    text(slide, x, y + int(h * 0.52), int(w), int(h * 0.42), lead, 10, sub, anchor=MSO_ANCHOR.TOP)


def proposal_rings(prs, data):
    """Proposed structure as concentric circles: the paid Knesset team at the centre."""
    pr = data["proposal"]
    rg = pr["rings"]
    s = prs.slides.add_slide(prs.slide_layouts[6])
    header(s, pr["title"], "")
    margin = Inches(0.45)

    cx, cy = Inches(8.7), Inches(4.25)
    r_out, r_mid, r_in = Inches(3.05), Inches(2.1), Inches(1.2)
    oval(s, cx, cy, r_out, RGBColor(0xEE, 0xF1, 0xF7), LINE)
    oval(s, cx, cy, r_mid, RGBColor(0xD9, 0xE1, 0xF0), LINE)
    oval(s, cx, cy, r_in, GOLD, None)

    core = rg["core"]
    text(s, cx - r_in, cy - Inches(0.92), 2 * r_in, Inches(0.24), core["label"], 10, NAVY_DARK)
    text(s, cx - r_in, cy - Inches(0.7), 2 * r_in, Inches(0.38), core["title"], 18, NAVY_DARK, bold=True)
    ly = cy - Inches(0.28)
    for i, line in enumerate(core["lines"]):
        text(s, cx - r_in + Inches(0.1), ly, 2 * r_in - Inches(0.2), Inches(0.26), line, 11, NAVY_DARK,
             bold=(i == len(core["lines"]) - 1))
        ly += Inches(0.27)

    # positions on each band (RTL: "right" is read first)
    mid = {"top": (0, -Inches(1.63)), "right": (Inches(1.2), Inches(1.33)), "left": (-Inches(1.2), Inches(1.33))}
    out = {"top": (0, -Inches(2.6)), "right": (Inches(1.95), Inches(2.18)), "left": (-Inches(1.95), Inches(2.18))}
    for it in rg["middle"]:
        dx, dy = mid[it["pos"]]
        pill(s, cx + dx, cy + dy, Inches(1.95), Inches(0.62), it["title"], it["lead"], NAVY, WHITE, GOLD)
    for it in rg["outer"]:
        dx, dy = out[it["pos"]]
        pill(s, cx + dx, cy + dy, Inches(2.5), Inches(0.62), it["title"], it["lead"], WHITE, NAVY, INK)

    # Left column: the rhythm, then the two conditions in red
    lw = Inches(4.3)
    kpis = pr["core"]["kpis"]
    ky = Inches(1.45)
    for k in kpis:
        rect(s, margin, ky, lw, Inches(0.62), NAVY, radius=0.25)
        text(s, margin, ky, lw, Inches(0.62), k, 16, WHITE, bold=True)
        ky += Inches(0.74)
    RED = AVAIL["low"][1]
    ny = ky + Inches(0.12)
    for note in pr.get("notes", []):
        nh = Inches(1.5)
        rect(s, margin, ny, lw, nh, WHITE, line=RED, radius=0.08)
        s.shapes[-1].line.width = Pt(2)
        num_dot(s, margin + lw - Inches(0.5), ny + Inches(0.14), Inches(0.34), "!", fill=RED)
        text(s, margin + Inches(0.15), ny + Inches(0.1), lw - Inches(0.72), Inches(0.42), note["title"], 12, RED,
             bold=True, align=PP_ALIGN.RIGHT)
        text(s, margin + Inches(0.15), ny + Inches(0.56), lw - Inches(0.3), nh - Inches(0.62), note["line"], 12, INK,
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.TOP)
        ny += nh + Inches(0.15)
    return s


def proposal_slide(prs, data):
    pr = data["proposal"]
    s = prs.slides.add_slide(prs.slide_layouts[6])
    header(s, pr["title"], pr["subtitle"])
    margin = Inches(0.45)

    # Top: everyone outside the core, split by how they take part
    groups = pr["groups"]
    gx_r, gx_l = W - margin, margin
    ggap = Inches(0.35)
    total_people = sum(len(gr["people"]) for gr in groups)
    unit = (gx_r - gx_l - ggap * (len(groups) - 1)) / total_people
    gy, gh = Inches(1.15), Inches(0.92)
    by, bh = gy + Inches(0.36), Inches(0.5)
    x_right = gx_r
    for gr in groups:
        gw = int(unit * len(gr["people"]))
        gx = x_right - gw
        rect(s, gx, gy, gw, gh, None, line=LINE, radius=0.08)
        text(s, gx + Inches(0.1), gy + Inches(0.04), gw - Inches(0.2), Inches(0.3),
             gr["title"], 13, NAVY, bold=True, align=PP_ALIGN.RIGHT)
        text(s, gx + Inches(0.1), gy + Inches(0.06), gw - Inches(0.2), Inches(0.28),
             gr["note"], 10, MUTED, align=PP_ALIGN.LEFT)
        n = len(gr["people"])
        g = Inches(0.1)
        cw = int((gw - Inches(0.2) - g * (n - 1)) / n)
        for i, (nm, role) in enumerate(gr["people"]):
            x = gx + gw - Inches(0.1) - (i + 1) * cw - i * g
            if nm.startswith("?"):  # a seat still to be filled
                rect(s, x, by, cw, bh, None, line=GOLD, dashed=True)
                text(s, x, by + Inches(0.03), cw, bh * 0.52, nm[1:], 12, NAVY, bold=True, anchor=MSO_ANCHOR.BOTTOM)
                text(s, x, by + bh * 0.55, cw, bh * 0.4, role, 9, MUTED, anchor=MSO_ANCHOR.TOP)
            else:
                card(s, x, by, cw, bh, nm, role, None, False, size=12)
        x_right = gx - ggap

    # Core: the paid Knesset team
    core = pr["core"]
    cx, cwid = Inches(3.75), Inches(5.83)
    cy, chh = Inches(2.3), Inches(2.85)
    connector(s, W // 2, gy + gh, W // 2, cy)
    rect(s, cx, cy, cwid, chh, WHITE, line=GOLD, radius=0.05)
    s.shapes[-1].line.width = Pt(2.5)
    text(s, cx, cy + Inches(0.1), cwid, Inches(0.36), core["title"], 17, NAVY, bold=True)
    n = len(core["names"])
    g = Inches(0.12)
    pw = int((cwid - Inches(0.3) - g * (n - 1)) / n)
    py = cy + Inches(0.6)
    for i, nm in enumerate(core["names"]):
        x = cx + cwid - Inches(0.15) - (i + 1) * pw - i * g
        if nm:
            nm, _, alt = nm.partition("|")
            card(s, x, py, pw, Inches(0.62), nm, alt or "נציג קבוע", None, False, size=12)
        else:  # the seat still to be filled
            rect(s, x, py, pw, Inches(0.62), None, line=GOLD, dashed=True)
            f4 = core.get("fourth", {"title": "נציג רביעי", "line": ""})
            text(s, x, py + Inches(0.04), pw, Inches(0.32), f4["title"], 12, NAVY, bold=True,
                 anchor=MSO_ANCHOR.BOTTOM)
            text(s, x, py + Inches(0.36), pw, Inches(0.24), f4["line"], 9, MUTED, anchor=MSO_ANCHOR.TOP)
    # content person sits inside the core: part of the team, not an outside service
    ct = pr["content"]
    qy, qh = cy + Inches(1.35), Inches(0.62)
    qx, qw = cx + Inches(0.15), cwid - Inches(0.3)
    rect(s, qx, qy, qw, qh, WHITE, line=GOLD)
    s.shapes[-1].line.width = Pt(2)
    text(s, qx, qy + Inches(0.05), qw, Inches(0.3), ct["title"], 13, NAVY, bold=True)
    text(s, qx, qy + Inches(0.34), qw, Inches(0.24), ct["line"], 10, MUTED)
    ky = cy + Inches(2.1)
    kn = len(core["kpis"])
    kw = int((cwid - Inches(0.3) - g * (kn - 1)) / kn)
    for i, k in enumerate(core["kpis"]):
        x = cx + cwid - Inches(0.15) - (i + 1) * kw - i * g
        rect(s, x, ky, kw, Inches(0.6), NAVY, radius=0.2)
        text(s, x, ky, kw, Inches(0.6), k, 13, WHITE, bold=True)

    # Sides feed the core
    sy, sh = Inches(2.3), Inches(1.75)
    rx = cx + cwid + Inches(0.35)
    info_box(s, rx, sy, W - margin - rx, sh, pr["research"])
    arrow(s, rx, sy + sh // 2, cx + cwid, sy + sh // 2)
    lw = cx - Inches(0.35) - margin
    info_box(s, margin, sy, lw, sh, pr["field"])
    arrow(s, margin + lw, sy + sh // 2, cx, sy + sh // 2)

    # Volunteer digital team takes the content to the public
    dg = pr["digital"]
    dy, dh = cy + chh + Inches(0.35), Inches(0.8)
    dw = Inches(4.2)
    dx = cx + (cwid - dw) // 2
    arrow(s, cx + cwid // 2, cy + chh, cx + cwid // 2, dy)
    rect(s, dx, dy, dw, dh, WHITE, line=LINE, radius=0.08)
    text(s, dx, dy + Inches(0.08), dw, Inches(0.32), f'{dg["title"]} · {dg["lead"]}', 13, NAVY, bold=True)
    text(s, dx, dy + Inches(0.44), dw, Inches(0.28), dg["line"], 11, INK)

    # Red notes: the two conditions the model depends on
    notes = pr.get("notes", [])
    if notes:
        RED = AVAIL["low"][1]
        ny, nh = dy + dh + Inches(0.15), Inches(0.92)
        ng = Inches(0.2)
        nw = int((W - 2 * margin - ng * (len(notes) - 1)) / len(notes))
        for i, note in enumerate(notes):
            x = W - margin - (i + 1) * nw - i * ng
            rect(s, x, ny, nw, nh, WHITE, line=RED, radius=0.12)
            s.shapes[-1].line.width = Pt(2)
            num_dot(s, x + nw - Inches(0.5), ny + Inches(0.12), Inches(0.36), "!", fill=RED)
            text(s, x + Inches(0.15), ny + Inches(0.1), nw - Inches(0.75), Inches(0.36), note["title"], 14, RED,
                 bold=True, align=PP_ALIGN.RIGHT)
            text(s, x + Inches(0.15), ny + Inches(0.46), nw - Inches(0.3), Inches(0.42), note["line"], 11, INK,
                 align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.TOP)
    return s


def activity_slide(prs, act):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    header(s, act["title"], "")
    margin = Inches(0.45)
    full = W - 2 * margin
    g = Inches(0.2)

    # KPIs
    kn = len(act["kpis"])
    kw = int((full - g * (kn - 1)) / kn)
    ky, kh = Inches(1.25), Inches(0.95)
    for i, (big, small) in enumerate(act["kpis"]):
        x = W - margin - (i + 1) * kw - i * g
        rect(s, x, ky, kw, kh, NAVY, radius=0.14)
        text(s, x, ky + Inches(0.1), kw, Inches(0.48), big, 22, WHITE, bold=True, anchor=MSO_ANCHOR.BOTTOM)
        text(s, x, ky + Inches(0.6), kw, Inches(0.28), small, 12, GOLD, anchor=MSO_ANCHOR.TOP)

    # Week strip
    days = act["days"]
    dy, dh = Inches(2.4), Inches(1.3)
    dg = Inches(0.14)
    dw = int((full - dg * (len(days) - 1)) / len(days))
    for i, (day, what, line, knesset) in enumerate(days):
        x = W - margin - (i + 1) * dw - i * dg
        rect(s, x, dy, dw, dh, GOLD if knesset else WHITE, line=None if knesset else LINE, radius=0.1)
        text(s, x, dy + Inches(0.1), dw, Inches(0.3), day, 12, NAVY_DARK if knesset else MUTED, bold=True)
        text(s, x + Inches(0.1), dy + Inches(0.38), dw - Inches(0.2), Inches(0.45), what, 15, NAVY_DARK if knesset else NAVY,
             bold=True)
        text(s, x + Inches(0.1), dy + Inches(0.82), dw - Inches(0.2), Inches(0.45), line, 11, NAVY_DARK if knesset else INK,
             anchor=MSO_ANCHOR.TOP)

    # Planning bar under the days it happens on
    pl = act.get("planning")
    if pl:
        c0, c1 = min(pl["cols"]), max(pl["cols"])
        x_r = W - margin - c0 * (dw + dg)
        x_l = W - margin - (c1 + 1) * dw - c1 * dg
        py = dy + dh + Inches(0.1)
        rect(s, x_l, py, x_r - x_l, Inches(0.62), NAVY, radius=0.18)
        text(s, x_l + Inches(0.15), py + Inches(0.04), x_r - x_l - Inches(0.3), Inches(0.3), pl["title"], 13, WHITE,
             bold=True)
        text(s, x_l + Inches(0.15), py + Inches(0.32), x_r - x_l - Inches(0.3), Inches(0.26), pl["line"], 10, GOLD)

    # Who goes (right) + content person (left)
    by, bh = Inches(4.55), Inches(2.55)
    bw = int((full - g) / 2)
    who = act["who"]
    wx = W - margin - bw
    rect(s, wx, by, bw, bh, WHITE, line=LINE, radius=0.06)
    text(s, wx + Inches(0.2), by + Inches(0.12), bw - Inches(0.4), Inches(0.36), who["title"], 16, NAVY, bold=True,
         align=PP_ALIGN.RIGHT)
    n = len(who["reps"])
    cg = Inches(0.1)
    cw = int((bw - Inches(0.4) - cg * (n - 1)) / n)
    for i, nm in enumerate(who["reps"]):
        x = wx + bw - Inches(0.2) - (i + 1) * cw - i * cg
        if nm == "נציג רביעי":
            rect(s, x, by + Inches(0.6), cw, Inches(0.55), None, line=GOLD, dashed=True)
            text(s, x, by + Inches(0.6), cw, Inches(0.55), nm, 12, NAVY, bold=True)
        else:
            nm, _, alt = nm.partition("|")
            card(s, x, by + Inches(0.6), cw, Inches(0.55), nm, alt or None, None, False, size=12)
    text(s, wx + Inches(0.2), by + Inches(1.3), bw - Inches(0.4), Inches(0.3), who["fourth_note"], 11, MUTED,
         align=PP_ALIGN.RIGHT)
    rect(s, wx + Inches(0.2), by + Inches(1.75), bw - Inches(0.4), Inches(0.7), BG, radius=0.15)
    text(s, wx + Inches(0.3), by + Inches(1.75), bw - Inches(0.6), Inches(0.7), "+ " + who["support"], 13, INK,
         bold=True, align=PP_ALIGN.RIGHT)

    ct = act["content"]
    cx = margin
    rect(s, cx, by, bw, bh, WHITE, line=GOLD, radius=0.06)
    s.shapes[-1].line.width = Pt(2.5)
    text(s, cx + Inches(0.2), by + Inches(0.12), bw - Inches(0.4), Inches(0.36), ct["title"], 16, NAVY, bold=True,
         align=PP_ALIGN.RIGHT)
    text(s, cx + Inches(0.2), by + Inches(0.5), bw - Inches(0.4), Inches(0.3), ct["sub"], 11, MUTED,
         align=PP_ALIGN.RIGHT)
    ly = by + Inches(1.0)
    for line in ct["lines"]:
        text(s, cx + Inches(0.25), ly, bw - Inches(0.5), Inches(0.5), "• " + line, 15, INK, bold=True,
             align=PP_ALIGN.RIGHT)
        ly += Inches(0.6)
    return s


def stage_slide(prs, st):
    """One budget stage: the big number, the line items with what changed, and a box that argues for it."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    header(s, st["title"], "")
    margin = Inches(0.45)
    g = Inches(0.3)
    lw = Inches(5.2)
    rw = W - 2 * margin - lw - g
    rx = W - margin - rw
    top = Inches(1.3)

    # Right: line items
    rect(s, rx, top, rw, Inches(0.42), NAVY, radius=0.2)
    text(s, rx + Inches(0.2), top, rw - Inches(3.2), Inches(0.42), "תפקיד", 12, WHITE, bold=True, align=PP_ALIGN.RIGHT)
    text(s, rx + Inches(1.6), top, Inches(1.4), Inches(0.42), "לחודש", 12, WHITE, bold=True)
    text(s, rx + Inches(0.1), top, Inches(1.5), Inches(0.42), "שינוי", 12, WHITE, bold=True)
    ry = top + Inches(0.52)
    for label, amount, tag in st["rows"]:
        rect(s, rx, ry, rw, Inches(0.56), WHITE, line=LINE, radius=0.15)
        text(s, rx + Inches(3.1), ry, rw - Inches(3.3), Inches(0.56), label, 13, INK, bold=True, align=PP_ALIGN.RIGHT)
        text(s, rx + Inches(1.6), ry, Inches(1.4), Inches(0.56), amount, 14, NAVY, bold=True)
        up = tag.startswith("+")
        chip_fill = GOLD if up else BG
        rect(s, rx + Inches(0.15), ry + Inches(0.12), Inches(1.35), Inches(0.32), chip_fill, radius=0.5)
        text(s, rx + Inches(0.15), ry + Inches(0.12), Inches(1.35), Inches(0.32), tag, 10,
             NAVY_DARK if up else MUTED, bold=up, rtl=not up)
        ry += Inches(0.64)
    if st.get("rate"):  # daily Knesset pay belongs with the money, not with the weekly rhythm
        rect(s, rx, ry + Inches(0.06), rw, Inches(0.5), GOLD, radius=0.3)
        text(s, rx + Inches(0.2), ry + Inches(0.06), rw - Inches(0.4), Inches(0.5), st["rate"], 13, NAVY_DARK, bold=True)

    # Left: the number
    lx = margin
    rect(s, lx, top, lw, Inches(2.55), NAVY, radius=0.06)
    text(s, lx, top + Inches(0.15), lw, Inches(0.3), "עלות חודשית", 13, GOLD)
    text(s, lx, top + Inches(0.45), lw, Inches(0.8), st["monthly"], 44, WHITE, bold=True)
    text(s, lx, top + Inches(1.22), lw, Inches(0.3), st["yearly"], 13, WHITE)
    kw = (lw - Inches(0.4) - Inches(0.1) * (len(st["kpis"]) - 1)) // len(st["kpis"])
    for k, (big, small) in enumerate(st["kpis"]):
        kx = lx + lw - Inches(0.2) - (k + 1) * kw - k * Inches(0.1)
        rect(s, kx, top + Inches(1.65), kw, Inches(0.72), RGBColor(0x2A, 0x4C, 0x8C), radius=0.15)
        text(s, kx, top + Inches(1.67), kw, Inches(0.38), big, 17, WHITE, bold=True)
        text(s, kx, top + Inches(2.04), kw, Inches(0.28), small, 10, GOLD)

    # Left below: what changes / why it pays
    bx = st["box"]
    by = top + Inches(2.75)
    bh = Inches(7.25) - by
    strong = bx.get("strong")
    rect(s, lx, by, lw, bh, WHITE, line=GOLD if strong else LINE, radius=0.06)
    if strong:
        s.shapes[-1].line.width = Pt(3)
    text(s, lx + Inches(0.2), by + Inches(0.12), lw - Inches(0.4), Inches(0.62), bx["title"], 15 if strong else 14,
         NAVY, bold=True, align=PP_ALIGN.RIGHT)
    ly = by + Inches(0.8)
    for line in bx["lines"]:
        text(s, lx + Inches(0.25), ly, lw - Inches(0.5), Inches(0.6), "• " + line, 12, INK, bold=strong,
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.TOP)
        ly += Inches(0.68)
    return s


def costs_slide(prs, cs):
    """Three cost models side by side; the recommended one gets the gold frame."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    header(s, cs["title"], "")
    margin = Inches(0.45)
    g = Inches(0.25)
    ms = cs["models"]
    cw = int((W - 2 * margin - g * (len(ms) - 1)) / len(ms))
    top, ch = Inches(1.3), Inches(5.6)
    for i, m in enumerate(ms):
        x = W - margin - (i + 1) * cw - i * g
        rec = m.get("recommended")
        rect(s, x, top, cw, ch, WHITE, line=GOLD if rec else LINE, radius=0.05)
        if rec:
            s.shapes[-1].line.width = Pt(3)
        # head
        # the highlighted model is drawn in gold
        rect(s, x, top, cw, Inches(0.95), GOLD if rec else SLATE, radius=0.12)
        text(s, x, top + Inches(0.1), cw, Inches(0.42), m["name"], 20, NAVY_DARK if rec else WHITE, bold=True)
        text(s, x + Inches(0.1), top + Inches(0.52), cw - Inches(0.2), Inches(0.36), m["tag"], 10,
             NAVY_DARK if rec else GOLD)
        # the number
        text(s, x, top + Inches(1.05), cw, Inches(0.7), m["monthly"], 36, NAVY, bold=True)
        text(s, x, top + Inches(1.7), cw, Inches(0.3), "לחודש · " + m["yearly"], 12, MUTED)
        # two small KPIs
        kw = (cw - Inches(0.4) - Inches(0.1) * (len(m["kpis"]) - 1)) // len(m["kpis"])
        for k, (big, small) in enumerate(m["kpis"]):
            kx = x + cw - Inches(0.2) - (k + 1) * kw - k * Inches(0.1)
            rect(s, kx, top + Inches(2.1), kw, Inches(0.72), BG, radius=0.15)
            text(s, kx, top + Inches(2.13), kw, Inches(0.38), big, 17, NAVY, bold=True)
            text(s, kx, top + Inches(2.5), kw, Inches(0.28), small, 10, MUTED)
        # composition
        ry = top + Inches(3.0)
        for label, amount in m["rows"]:
            text(s, x + Inches(1.35), ry, cw - Inches(1.55), Inches(0.34), label, 11, INK, align=PP_ALIGN.RIGHT)
            text(s, x + Inches(0.15), ry, Inches(1.2), Inches(0.34), amount, 11,
                 MUTED if amount == "בהתנדבות" else NAVY, bold=amount != "בהתנדבות", align=PP_ALIGN.LEFT)
            ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x + Inches(0.2), ry + Inches(0.37),
                                        x + cw - Inches(0.2), ry + Inches(0.37))
            ln.line.color.rgb = LINE
            ln.line.width = Pt(0.75)
            ry += Inches(0.4)
        text(s, x + Inches(0.2), ry + Inches(0.05), cw - Inches(0.4), Inches(0.28), "תעריף: " + m["rate"], 10, MUTED,
             align=PP_ALIGN.RIGHT)
    text(s, margin, Inches(7.02), W - 2 * margin, Inches(0.3), cs["footnote"], 10, MUTED)
    return s


def org_slide(prs, data, colored):
    """Whole organisation on one slide: board on top, every team as a column below."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    STYLE["muted"] = True
    # one availability per person, even when they sit in two teams
    seen = {m["name"]: m["availability"] for m in data["board"]["members"]}
    if data.get("ceo"):
        seen[data["ceo"]["name"]] = data["ceo"]["availability"]
    n_groups = 0

    def walk(g):
        nonlocal n_groups
        n_groups += 1
        for x in [g.get("head") or {}] + g["members"]:
            if x.get("name"):
                seen[x["name"]] = x.get("availability")
        if g.get("sub"):
            walk(g["sub"])
    for t in data["teams"]:
        walk(t)
    counts = {}
    for v in seen.values():
        counts[v] = counts.get(v, 0) + 1
    if colored:
        header(s, "זמינות במבנה הארגוני הקיים", "כל אדם צבוע לפי רמת הזמינות שלו", SLATE, SLATE_LINE)
    else:
        header(s, "מבנה ארגוני קיים", "", SLATE, SLATE_LINE)
        # the problem in three numbers, between logo and title
        stats = [(str(len(seen)), "אנשים"), (str(n_groups), "צוותים")]
        x = Inches(7.6)
        for num, label in stats:
            w = Inches(2.35) if len(label) > 8 else Inches(1.45)
            x -= w
            box = text(s, x, Inches(0.22), w, Inches(0.5), num, 22, GOLD, bold=True, align=PP_ALIGN.RIGHT)
            r = box.text_frame.paragraphs[0].add_run()
            r.text = " " + label
            r.font.size = Pt(13)
            r.font.color.rgb = WHITE
            r.font.name = FONT

    margin = Inches(0.45)
    usable = W - 2 * margin

    # Board row
    board = data["board"]["members"]
    text(s, margin, Inches(1.08), usable, Inches(0.26), data["board"]["title"], 13, SLATE, bold=True,
         align=PP_ALIGN.RIGHT)
    gap = Inches(0.12)
    n = len(board)
    cw = int((usable - gap * (n - 1)) / n)
    ch = Inches(0.6)
    by = Inches(1.36)
    for i, m in enumerate(board):  # RTL: first item on the right
        x = W - margin - (i + 1) * cw - i * gap
        card(s, x, by, cw, ch, m["name"], m["role"], m["availability"], colored)

    # CEO between board and teams
    ceo = data.get("ceo")
    anchor_y = by + ch
    if ceo:
        ceo_w, ceo_h, ceo_y = Inches(2.6), Inches(0.48), Inches(2.14)
        connector(s, W // 2, anchor_y, W // 2, ceo_y)
        card(s, (W - ceo_w) // 2, ceo_y, ceo_w, ceo_h, ceo["name"], ceo["role"], ceo["availability"], colored)
        anchor_y = ceo_y + ceo_h

    # Teams: one column each, width proportional to how many card columns it needs
    teams = data["teams"]
    head_y, head_h = (Inches(2.86), Inches(0.5)) if ceo else (Inches(2.62), Inches(0.6))
    top = head_y + head_h + Inches(0.2)
    bottom = Inches(6.95)
    mh, mgap = Inches(0.36), Inches(0.08)
    max_rows = max(1, int((bottom - top + mgap) / (mh + mgap)))
    subcols = [t.get("cols") or max(1, -(-len(t["members"]) // max_rows)) for t in teams]
    tgap = Inches(0.3)
    unit = min(int((usable - tgap * (len(teams) - 1)) / sum(subcols)), Inches(1.9))
    total = unit * sum(subcols) + tgap * (len(teams) - 1)

    def group(t, tx, tw, sc, gy, gh, gtop, default_role):
        """Frame + head card + member grid. Returns the frame's bottom y."""
        cx = tx + tw // 2
        rows = max(1, -(-len(t["members"]) // sc))
        frame_top = gy + gh // 2
        frame_bottom = gtop + rows * mh + (rows - 1) * mgap + Inches(0.12)
        rect(s, tx, frame_top, tw, frame_bottom - frame_top, None, line=LINE, radius=0.04)
        hw = min(tw - Inches(0.2), Inches(2.6))
        head = t.get("head") or {}
        card(s, cx - hw // 2, gy, hw, gh, head.get("name", ""),
             f'{head.get("role", default_role)} · {t["title"]}', head.get("availability"), colored)
        iw = tw - Inches(0.2)
        mw = int((iw - mgap * (sc - 1)) / sc)
        for i, m in enumerate(t["members"]):  # RTL inside the group
            r, c = divmod(i, sc)
            x = tx + Inches(0.1) + iw - (c + 1) * mw - c * mgap
            y = gtop + r * (mh + mgap)
            card(s, x, y, mw, mh, m["name"], None, m["availability"], colored, size=11, note=m.get("note"))
        return frame_bottom

    bus_y = (anchor_y + head_y) // 2
    centers = []
    x_right = (W + total) // 2
    for t, sc in zip(teams, subcols):
        tw = sc * unit
        tx = x_right - tw
        cx = tx + tw // 2
        centers.append(cx)
        fb = group(t, tx, tw, sc, head_y, head_h, top, "ראש צוות")
        sub = t.get("sub")  # a sub-group boxed under its parent team (e.g. youth under activists)
        if sub:
            sy, sh = fb + Inches(0.22), Inches(0.42)
            connector(s, cx, fb, cx, sy)
            group(sub, tx, tw, sc, sy, sh, sy + sh + Inches(0.14), "רכז")
        x_right = tx - tgap

    # connectors: board -> bus -> each team head
    connector(s, W // 2, anchor_y, W // 2, bus_y)
    if len(centers) > 1:
        connector(s, min(centers), bus_y, max(centers), bus_y)
    for cx in centers:
        connector(s, cx, bus_y, cx, head_y)

    if colored:
        legend(s, counts)
    STYLE["muted"] = False
    return s


def main():
    import sys
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "people.json"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    data = json.loads(src.read_text(encoding="utf-8"))
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    org_slide(prs, data, colored=False)
    org_slide(prs, data, colored=True)
    if "proposal" in data:
        proposal_rings(prs, data)
    plans_path = HERE / "plans.json"
    if plans_path.exists():
        plans = json.loads(plans_path.read_text(encoding="utf-8"))
        for leader in plans.get("programs", []):
            programs_slide(prs, leader)
        # Staged work plans live on the website (site/plans.json), not in the deck.
    if "activity" in data:
        activity_slide(prs, data["activity"])
    for st in data.get("stages", []):
        stage_slide(prs, st)
    if "costs" in data:
        costs_slide(prs, data["costs"])
    out.parent.mkdir(exist_ok=True)
    prs.save(out)
    print(out)


if __name__ == "__main__":
    main()
