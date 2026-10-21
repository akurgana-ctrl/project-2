"""Builds preview and web versions of a newsletter issue.

Usage: python3 build.py issue-01.html
  preview-<issue>.html  local preview, images from disk
  web-<issue>.html      standalone browser version, images embedded as data URIs
"""
import base64
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
IMAGES = {
    "IMG_LOGO": "logo.png",
    "IMG_CONF": "images/conference.jpg",
    "IMG_TRAINING": "images/training.jpg",
    "IMG_HACKATHON": "images/hackathon.jpg",
}
DEMO = "https://claude.ai/artifact/BitaazYA1yUxEs9iazZaUa"
LINKS = {
    "VOTE_A_URL": DEMO + "#vote-a",
    "VOTE_B_URL": DEMO + "#vote-b",
    "VOTE_C_URL": DEMO + "#vote-c",
    "WEB_VERSION_URL": DEMO + "#web",
    "UNSUBSCRIBE_URL": DEMO + "#unsub",
    "UPDATES_GROUP_URL": "#",
    "X_URL": "#",
    "ORG_ADDRESS": "[כתובת הארגון]",
}


def fill(html, values):
    for key, value in values.items():
        html = html.replace("{{%s}}" % key, value)
    return html


def data_uri(path):
    mime = "image/png" if path.endswith(".png") else "image/jpeg"
    return "data:%s;base64,%s" % (mime, base64.b64encode((HERE / path).read_bytes()).decode())


def main(name):
    src = (HERE / name).read_text()
    stem = Path(name).stem

    preview = fill(fill(src, IMAGES), LINKS)
    (HERE / ("preview-%s.html" % stem)).write_text(preview)

    web = fill(fill(src, {k: data_uri(v) for k, v in IMAGES.items()}), LINKS)
    web = re.sub(r"<!--.*?-->", "", web, flags=re.S)
    # drop the "open in browser" row: the reader is already in the browser
    web = re.sub(r'<table role="presentation" class="container" width="600"[^>]*style="width:600px;">.*?</table>', "", web, count=1, flags=re.S)
    web = re.sub(r"<!DOCTYPE html>|<html[^>]*>|</html>|<head>|</head>|<meta[^>]*>", "", web)
    web = re.sub(r"<body[^>]*>", '<div dir="rtl" style="background:#E9ECF3;min-height:100%;">', web).replace("</body>", "</div>")
    (HERE / ("web-%s.html" % stem)).write_text(web.strip())

    left = re.findall(r"\{\{\w+\}\}", preview)
    print("built", stem, "unfilled:", left)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "issue-01.html")
