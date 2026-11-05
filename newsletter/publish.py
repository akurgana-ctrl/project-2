"""Builds every output of a newsletter issue from one source file.

Usage: python3 publish.py issue-02.html

Writes to out/<issue>/:
  preview.html     local preview, images from disk
  web.html         browser version, images embedded (for the claude.ai page)
  email.html       the email itself, images served from the repo (Brevo or any sender)
  copy-page.html   page with "העתקה ל-Gmail": paste into a new Gmail message on a computer
  mailchimp.html   for Mailchimp (Code your own): direct links, Mailchimp's own unsubscribe and
                   browser-version tags; Mailchimp counts opens and clicks itself
  mailchimp-copy.html  page with one button that copies mailchimp.html, and one for the subject
  site.html        the issue as a block for a page on the website (site_copy.py makes a copy page)

Placeholders in the source:
  {{IMG:images/x.jpg}}   an image, path relative to this folder (commit it before sending)
  {{T:id}}               a tracked link, id from tracking/links.py
  {{UNSUBSCRIBE_URL}}    unsubscribe link
  {{OPEN_PIXEL}}         open-tracking image, required in every issue (only the email gets it)
  {{WEB_VERSION_URL}}    the "open in browser" row (removed from every output for now)
Images and docs are served from the repo branch, so push before sending.
"""
import base64
import html as htmllib
import json
import re
import sys
from pathlib import Path

from tracking import links as tracked

HERE = Path(__file__).parent
RAW = "https://raw.githubusercontent.com/akurgana-ctrl/project-2/newsletter-template/newsletter/"
UNSUB = "mailto:akurgana@gmail.com?subject=%D7%94%D7%A1%D7%A8%D7%94%20%D7%9E%D7%94%D7%AA%D7%A4%D7%95%D7%A6%D7%94"
BROWSER_ROW = r'<table role="presentation" class="container" width="600"[^>]*style="width:600px;">.*?</table>\s*'
IMG = re.compile(r"\{\{IMG:([^}]+)\}\}")


def data_uri(path):
    mime = "image/png" if path.endswith(".png") else "image/jpeg"
    return "data:%s;base64,%s" % (mime, base64.b64encode((HERE / path).read_bytes()).decode())


def issue_number(name):
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else 0


def render(name, images, unsubscribe=UNSUB, opens=False, direct=False, web_url=None):
    src = re.sub(r"<!--(?!\[if).*?-->", "", (HERE / name).read_text(), flags=re.S)
    if "{{OPEN_PIXEL}}" not in src:
        sys.exit("missing {{OPEN_PIXEL}}: put it right before the closing </div></div></body>")
    src = src.replace("{{OPEN_PIXEL}}", tracked.pixel(issue_number(name)) if opens else "")
    for path in IMG.findall(src):
        if not (HERE / path).exists():
            sys.exit("missing image: %s" % path)
    out = IMG.sub(lambda m: images(m.group(1)), src)
    out = tracked.fill(out, issue_number(name), direct)
    # the browser row is a fixed-width table in the source; it is rebuilt as a fluid div or dropped
    row = ('<div dir="rtl" style="max-width:600px;margin:0 auto;padding:12px 18px 0;text-align:center;'
           'font-family:\'Heebo\',Arial,sans-serif;font-size:12px;color:#6A7190;">לא מוצג טוב? '
           '<a href="%s" style="color:#1D2E67;text-decoration:underline;">פתחו בדפדפן</a></div>\n' % web_url) if web_url else ""
    out = re.sub(BROWSER_ROW, lambda m: row, out, count=1, flags=re.S)
    out = out.replace("{{UNSUBSCRIBE_URL}}", unsubscribe)
    left = re.findall(r"\{\{[^}]+\}\}", out)
    if left and left != ["{{ unsubscribe }}"]:
        sys.exit("unfilled placeholders: %s" % left)
    return out


def site_fragment(name):
    """The issue as a block to paste into a page of the website: direct links, no unsubscribe row."""
    doc = render(name, lambda p: RAW + p, "", direct=True)
    doc = re.sub(r'\s*<div [^>]*>\s*<div [^>]*><a href="" [^>]*>הסרה מהתפוצה</a></div>\s*</div>', "", doc)
    doc = re.sub(r'<div style="display:none;max-height:0;[^"]*">.*?</div>\s*', "", doc, count=1, flags=re.S)
    fonts = re.search(r'<link href="https://fonts.googleapis.com[^>]*>', doc).group(0)
    return fonts + "\n" + body_of(doc) + "\n"


def body_of(doc):
    return re.search(r"<body[^>]*>(.*)</body>", doc, re.S).group(1).strip()


def main(name):
    src = (HERE / name).read_text()
    title = re.search(r"<title>(.*?)</title>", src).group(1)
    subject = re.search(r"<!--\s*נושא:\s*(.*?)\s*-->", src)
    subject = subject.group(1) if subject else title
    out = HERE / "out" / Path(name).stem
    out.mkdir(parents=True, exist_ok=True)

    (out / "preview.html").write_text(render(name, lambda p: "../../" + p))
    email = render(name, lambda p: RAW + p, opens=True)
    (out / "email.html").write_text(email)
    mailchimp = render(name, lambda p: RAW + p, "*|UNSUB|*", direct=True, web_url="*|ARCHIVE|*")
    (out / "mailchimp.html").write_text(mailchimp)
    data = json.dumps({"html": mailchimp, "subject": subject}, ensure_ascii=False).replace("</", "<\\/")
    (out / "site.html").write_text(site_fragment(name))
    copy_mc = (HERE / "mailchimp-copy-template.html").read_text()
    (out / "mailchimp-copy.html").write_text(copy_mc.replace("{{TITLE}}", title).replace("{{DATA}}", data))

    web = render(name, data_uri)
    web = re.sub(r"<!DOCTYPE html>|<html[^>]*>|</html>|<head>|</head>|<meta[^>]*>", "", web)
    web = re.sub(r"<body[^>]*>", '<div dir="rtl" style="background:#E9ECF3;min-height:100%;">', web).replace("</body>", "</div>")
    (out / "web.html").write_text(web.strip())

    page = (HERE / "copy-page-template.html").read_text()
    style = re.search(r"<style>.*?</style>", email, re.S).group(0)
    rich = body_of(email)
    mail = rich
    for path in set(re.findall(re.escape(RAW) + r'([^"\s]+\.(?:png|jpe?g))', rich)):
        mail = mail.replace(RAW + path, data_uri(path))
    for key, value in {"TITLE": title, "SUBJECT": htmllib.escape(subject), "EMAIL_STYLE": style,
                       "MAIL": mail, "RICH": rich, "CODE": htmllib.escape(email, quote=False)}.items():
        page = page.replace("{{%s}}" % key, value)
    (out / "copy-page.html").write_text(page)

    print("built", out, "| clicks and opens tracking:", "on" if tracked.tracker_url() else "off (tracker not deployed)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "issue-01.html")
