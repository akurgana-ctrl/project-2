"""Newsletter links and click tracking.

In issue HTML a tracked link is written href="{{T:<id>}}". fill() points it at the
Apps Script tracker (tracking/deploy-url.txt) when that file exists, otherwise
straight at the destination, so an issue always builds with working links.
The ids and destinations must match the "links" tab of the tracking sheet.
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
DOCS = "https://raw.githubusercontent.com/akurgana-ctrl/project-2/newsletter-template/newsletter/docs/"
LINKS = {
    "letter": DOCS + "tzalashim-letter-2026-09-07.pdf",
    "conf_video": "https://youtu.be/KvCN84yzbXA",
    "conf_booklet": DOCS + "knesset-26-booklet.pdf",
    "bill_selfdef": DOCS + "bill-self-defense.pdf",
    "bill_med": DOCS + "bill-medicine.pdf",
    "bill_net": DOCS + "bill-online-responsibility.pdf",
    "join_group": "https://chat.whatsapp.com/Cxw30pP21S34YVVI3dAeJi",
    "podcast_img": "https://youtu.be/ZpHFRbkM4fM",
    "podcast_btn": "https://youtu.be/ZpHFRbkM4fM",
    "updates_group": "https://chat.whatsapp.com/BYfqjCBe5pzHtWZ1tzIb83",
    "instagram": "https://www.instagram.com/koachhitarvut/",
    "x": "https://x.com/koach_hitarvut",
}


def tracker_url():
    f = HERE / "deploy-url.txt"
    return f.read_text().strip() if f.exists() else ""


def fill(html, issue=0):
    base = tracker_url()

    def sub(m):
        key = m.group(1)
        if key not in LINKS:
            raise SystemExit("unknown link id: %s (add it to tracking/links.py and the sheet)" % key)
        if not base:
            return LINKS[key]
        return base + "?l=" + key + ("&i=%d" % issue if issue else "")

    return re.sub(r"\{\{T:([a-z_]+)\}\}", sub, html)
