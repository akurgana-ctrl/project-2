"""Builds one page with a copy button per issue, for pasting issues into the website.

Usage: python3 site_copy.py issue-02.html issue-03.html   (writes out/site-copy.html)
"""
import html
import json
import re
import sys

import publish


def main(names):
    items = []
    for name in names:
        publish.main(name)
        out = publish.HERE / "out" / publish.Path(name).stem
        src = (publish.HERE / name).read_text()
        title = re.search(r"<title>(.*?)</title>", src).group(1)
        head = re.search(r"<!--\s*כותרת:\s*(.*?)\s*-->", src)
        date = re.search(r"\d{1,2}\.\d{1,2}\.\d{4}", src)
        items.append({"title": title, "headline": head.group(1) if head else "",
                      "date": date.group(0) if date else "", "html": (out / "site.html").read_text()})
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    page = (publish.HERE / "site-copy-template.html").read_text().replace("{{DATA}}", data)
    (publish.HERE / "out" / "site-copy.html").write_text(page)
    print("built out/site-copy.html:", ", ".join(html.unescape(i["title"]) for i in items))


if __name__ == "__main__":
    main(sys.argv[1:])
