"""Sends a newsletter issue through the Brevo API.

Usage: BREVO_API_KEY=... python3 send_brevo.py issue-01.html recipient@example.com [sender@example.com]
The sender address must be verified in Brevo (Senders & IP). Images are served from the repo,
so the email shows them like any normal newsletter.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

from tracking import links as tracked

HERE = Path(__file__).parent
RAW = "https://raw.githubusercontent.com/akurgana-ctrl/project-2/newsletter-template/newsletter/"
IMAGES = {
    "IMG_LOGO": "logo.png",
    "IMG_LOGO_WHITE": "logo-white.png",
    "IMG_CONF": "images/conference.jpg",
    "IMG_TRAINING": "images/training.jpg",
    "IMG_HACKATHON": "images/hackathon.jpg",
    "IMG_PRESSURE": "images/pressure-group.jpg",
    "IMG_PODCAST": "images/podcast.jpg",
}
VOTE_EMAIL = "akurgana@gmail.com"


def render(name):
    html = tracked.fill((HERE / name).read_text())
    html = re.sub(r"<!--(?!\[if).*?-->", "", html, flags=re.S)
    for key, path in IMAGES.items():
        html = html.replace("{{%s}}" % key, RAW + path)
    html = html.replace("{{CONF_DOC_URL}}", RAW + "docs/knesset-26-booklet.pdf")
    # no public web version yet: drop the "open in browser" row
    html = re.sub(r'<table role="presentation" class="container" width="600"[^>]*style="width:600px;">.*?</table>', "", html, count=1, flags=re.S)
    html = html.replace("{{VOTE_EMAIL}}", VOTE_EMAIL)
    html = html.replace("{{UNSUBSCRIBE_URL}}", "{{ unsubscribe }}")
    left = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if left:
        sys.exit("unfilled placeholders: %s" % left)
    return html


def main(name, to, sender=None):
    import os
    key = os.environ.get("BREVO_API_KEY")
    if not key:
        sys.exit("BREVO_API_KEY is not set")
    title = re.search(r"<title>(.*?)</title>", (HERE / name).read_text()).group(1)
    body = {
        "sender": {"name": "כח התערבות", "email": sender or to},
        "to": [{"email": to}],
        "subject": title,
        "htmlContent": render(name),
    }
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(body).encode(),
        headers={"api-key": key, "content-type": "application/json", "accept": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        print(res.status, res.read().decode())


if __name__ == "__main__":
    main(*sys.argv[1:])
