"""Brands a photo in the Koach Hitarvut frame: navy, gold border, a caption bar with the logo.

Usage: python3 tools/frame_photo.py input.jpg images/output.jpg "כותרת" ["שורה משנית"]
Needs Playwright with Chromium (the frame is drawn as HTML so the Hebrew renders correctly).
"""
import html
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
PAGE = """<!doctype html><html dir="rtl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;900&family=Karantina:wght@700&display=swap" rel="stylesheet">
<style>body{margin:0;background:#fff}
#c{width:1000px;background:#1D2E67;padding:26px;box-sizing:border-box;font-family:Heebo,sans-serif;border-top:10px solid #F0C000}
#c img.p{display:block;width:100%;border:5px solid #F0C000;box-sizing:border-box}
.bar{display:flex;align-items:center;justify-content:space-between;padding-top:20px}
.t1{font-family:Karantina,Heebo;font-size:60px;line-height:56px;color:#fff}
.t2{font-size:22px;color:#F0C000;font-weight:900;margin-top:6px}
.bar img{height:110px}</style></head><body>
<div id="c"><img class="p" src="file://{{PHOTO}}">
<div class="bar"><div><div class="t1">{{TITLE}}</div><div class="t2">{{SUB}}</div></div><img src="file://{{LOGO}}"></div></div>
</body></html>"""
SHOT = """const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(2500);await (await p.$('#c')).screenshot({path:process.argv[3]});await b.close();})();"""


def main(src, out, title, sub=""):
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        page = tmp / "frame.html"
        fill = {"{{PHOTO}}": str(Path(src).resolve()), "{{LOGO}}": str((HERE / "logo-light.png").resolve()),
                "{{TITLE}}": html.escape(title), "{{SUB}}": html.escape(sub)}
        text = PAGE
        for key, value in fill.items():
            text = text.replace(key, value)
        page.write_text(text)
        (tmp / "shot.js").write_text(SHOT)
        subprocess.run(["node", str(tmp / "shot.js"), str(page), str(tmp / "out.png")], check=True)
        Image.open(tmp / "out.png").convert("RGB").save(out, quality=82, optimize=True)
    print("saved", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
