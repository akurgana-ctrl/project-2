"""Build the journal web page (reports/journal.html) from reports/journal.md.

Usage: python3 reports/tools/build_journal.py
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "journal.md"
OUT = ROOT / "journal.html"
TEMPLATE = ROOT / "templates" / "journal-page.html"

TASK_RE = re.compile(r"^\d+\.\s+\*\*(.+?)\*\*\s*(?:·\s*(.+))?$")
SUB_RE = re.compile(r"^\s+-\s+(.+)$")
ITEM_RE = re.compile(r"^-\s+(.+)$")


def inline(text):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(text))


def parse(md):
    updated, sections, current = "", [], None
    for line in md.splitlines():
        if line.startswith("עודכן:"):
            updated = line.split(":", 1)[1].strip()
        elif line.startswith("## "):
            current = {"title": line[3:].strip(), "items": []}
            sections.append(current)
        elif current is None or not line.strip():
            continue
        elif m := TASK_RE.match(line):
            current["items"].append({"title": m[1], "meta": m[2] or "", "subs": []})
        elif (m := SUB_RE.match(line)) and current["items"]:
            current["items"][-1]["subs"].append(m[1])
        elif m := ITEM_RE.match(line):
            text, _, meta = m[1].rpartition(" · ") if " · " in m[1] else (m[1], "", "")
            current["items"].append({"title": text, "meta": meta, "subs": []})
    return updated, sections


def render_sub(sub):
    done = sub.startswith("בוצע")
    cls = ' class="done"' if done else ""
    return f"<li{cls}>{inline(sub)}</li>"


def render_section(section):
    kind = {"משימות פתוחות": "open", "בוצע": "done"}.get(section["title"], "note")
    rows = []
    for i, item in enumerate(section["items"], 1):
        num = f'<span class="num">{i}</span>' if kind == "open" else ""
        meta = f'<span class="meta">{inline(item["meta"])}</span>' if item["meta"] else ""
        subs = "".join(render_sub(s) for s in item["subs"])
        subs = f'<ul class="subs">{subs}</ul>' if subs else ""
        rows.append(
            f'<li class="item">{num}<div class="body"><div class="head">'
            f'<span class="title">{inline(item["title"])}</span>{meta}</div>{subs}</div></li>'
        )
    count = f'<span class="count">{len(section["items"])}</span>'
    return (
        f'<section class="sec sec-{kind}"><h2>{html.escape(section["title"])}{count}</h2>'
        f'<ol class="list">{"".join(rows)}</ol></section>'
    )


def main():
    updated, sections = parse(SRC.read_text(encoding="utf-8"))
    page = TEMPLATE.read_text(encoding="utf-8")
    page = page.replace("{{UPDATED}}", html.escape(updated))
    page = page.replace("{{SECTIONS}}", "\n".join(render_section(s) for s in sections))
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
