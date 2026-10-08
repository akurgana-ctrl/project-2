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

AVAIL = {
    "high": ("זמינות גבוהה", RGBColor(0x2E, 0x9E, 0x6A)),
    "medium": ("זמינות בינונית", RGBColor(0xE8, 0x89, 0x2B)),
    "low": ("זמינות נמוכה", RGBColor(0xD6, 0x45, 0x45)),
    None: ("טרם הוזן", RGBColor(0xB4, 0xBC, 0xCC)),
}

W, H = Inches(13.333), Inches(7.5)


def text(slide, x, y, w, h, s, size, color=INK, bold=False, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.04)
    tf.margin_top = tf.margin_bottom = 0
    style_para(tf.paragraphs[0], s, size, color, bold, align)
    return box


def style_para(p, s, size, color, bold, align):
    p.alignment = align
    p._p.get_or_add_pPr().set("rtl", "1")
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


def card(slide, x, y, w, h, name, role, avail, colored, size=12):
    """A person card. colored=False -> brand look; True -> availability color."""
    empty = not name
    if colored:
        fill = AVAIL[avail][1]
        rect(slide, x, y, w, h, fill)
        fg, sub = WHITE, WHITE
    elif empty:
        rect(slide, x, y, w, h, BG, line=MUTED, dashed=True)
        fg, sub = MUTED, MUTED
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
        text(slide, x, y, w, h, label, size, fg, bold=True)


def connector(slide, x1, y1, x2, y2):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = LINE
    c.line.width = Pt(1.5)


def header(slide, title, subtitle):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = BG
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Inches(0.95))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    bar.shadow.inherit = False
    gold = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(0.95), W, Inches(0.06))
    gold.fill.solid()
    gold.fill.fore_color.rgb = GOLD
    gold.line.fill.background()
    gold.shadow.inherit = False
    text(slide, Inches(1.4), Inches(0.12), Inches(11.5), Inches(0.5), title, 26, WHITE, bold=True,
         align=PP_ALIGN.RIGHT)
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


def legend(slide):
    items = ["high", "medium", "low", None]
    x = Inches(12.9)
    y = Inches(7.02)
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
        text(slide, x, y, w - Inches(0.28), Inches(0.32), label, 10, INK, align=PP_ALIGN.RIGHT)


def org_slide(prs, data, colored):
    """Whole organisation on one slide: board on top, every team as a column below."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    if colored:
        header(s, "זמינות במבנה הארגוני הקיים", "כל אדם צבוע לפי רמת הזמינות שלו")
    else:
        header(s, "מבנה ארגוני קיים", "כח התערבות · כנסת 26")

    margin = Inches(0.45)
    usable = W - 2 * margin

    # Board row
    board = data["board"]["members"]
    text(s, margin, Inches(1.12), usable, Inches(0.28), data["board"]["title"], 13, NAVY, bold=True,
         align=PP_ALIGN.RIGHT)
    gap = Inches(0.12)
    n = len(board)
    cw = int((usable - gap * (n - 1)) / n)
    ch = Inches(0.66)
    by = Inches(1.42)
    for i, m in enumerate(board):  # RTL: first item on the right
        x = W - margin - (i + 1) * cw - i * gap
        card(s, x, by, cw, ch, m["name"], m["role"], m["availability"], colored)

    # Teams: one column each, width proportional to how many card columns it needs
    teams = data["teams"]
    head_y, head_h = Inches(2.62), Inches(0.62)
    top = head_y + head_h + Inches(0.32)
    bottom = Inches(6.85)
    mh, mgap = Inches(0.36), Inches(0.08)
    max_rows = max(1, int((bottom - top + mgap) / (mh + mgap)))
    subcols = [max(1, -(-len(t["members"]) // max_rows)) for t in teams]
    tgap = Inches(0.3)
    unit = min(int((usable - tgap * (len(teams) - 1)) / sum(subcols)), Inches(1.9))
    total = unit * sum(subcols) + tgap * (len(teams) - 1)

    bus_y = Inches(2.36)
    centers = []
    x_right = (W + total) // 2
    for t, sc in zip(teams, subcols):
        tw = sc * unit
        tx = x_right - tw
        cx = tx + tw // 2
        centers.append(cx)
        # team frame
        rows = max(1, -(-len(t["members"]) // sc))
        frame_top = head_y + head_h / 2
        frame_h = top + rows * mh + (rows - 1) * mgap + Inches(0.14) - frame_top
        rect(s, tx, frame_top, tw, frame_h, None, line=LINE, radius=0.04)
        # head
        hw = min(tw - Inches(0.2), Inches(2.6))
        head = t.get("head") or {}
        card(s, cx - hw // 2, head_y, hw, head_h, head.get("name", ""),
             f'{head.get("role", "ראש צוות")} · {t["title"]}', head.get("availability"), colored)
        # members, RTL inside the team
        iw = tw - Inches(0.2)
        mw = int((iw - mgap * (sc - 1)) / sc)
        for i, m in enumerate(t["members"]):
            r, c = divmod(i, sc)
            x = tx + Inches(0.1) + iw - (c + 1) * mw - c * mgap
            y = top + r * (mh + mgap)
            card(s, x, y, mw, mh, m["name"], None, m["availability"], colored, size=11)
        x_right = tx - tgap

    # connectors: board -> bus -> each team head
    connector(s, W // 2, by + ch, W // 2, bus_y)
    if len(centers) > 1:
        connector(s, min(centers), bus_y, max(centers), bus_y)
    for cx in centers:
        connector(s, cx, bus_y, cx, head_y)

    if colored:
        legend(s)
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
    out.parent.mkdir(exist_ok=True)
    prs.save(out)
    print(out)


if __name__ == "__main__":
    main()
