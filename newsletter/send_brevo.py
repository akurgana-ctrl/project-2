"""Sends a newsletter issue through the Brevo API.

Usage: BREVO_API_KEY=... python3 send_brevo.py issue-02.html recipient@example.com [sender@example.com]
The sender address must be verified in Brevo (Senders & IP). The email is built by publish.py
with images served from the repo, so push before sending.
"""
import json
import os
import re
import sys
import urllib.request

import publish


def main(name, to, sender=None):
    key = os.environ.get("BREVO_API_KEY")
    if not key:
        sys.exit("BREVO_API_KEY is not set")
    src = (publish.HERE / name).read_text()
    subject = re.search(r"<!--\s*נושא:\s*(.*?)\s*-->", src) or re.search(r"<title>(.*?)</title>", src)
    body = {
        "sender": {"name": "כח התערבות", "email": sender or to},
        "to": [{"email": to}],
        "subject": subject.group(1),
        "htmlContent": publish.render(name, lambda p: publish.RAW + p, "{{ unsubscribe }}", opens=True),
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
