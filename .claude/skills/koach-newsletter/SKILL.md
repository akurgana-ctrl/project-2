---
name: koach-newsletter
description: Build the weekly Hebrew newsletter of כח התערבות (Koach Hitarvut) and get it ready to send in Mailchimp. Use when asked to write, edit, design or send an issue of the newsletter (ניוזלטר, גיליון), to gather this week's topics for it, to make its images, or to put an issue on the website.
---

# The כח התערבות weekly newsletter

Everything lives in `newsletter/`. The human guide is `newsletter/מדריך-מלא.md` (point the user to it when they ask how to do something themselves). Read `newsletter/STYLE.md` first: it holds every rule the editor has set, and they are not optional. Talk to the user in Hebrew only.

## The weekly flow

1. **Gather topics.** From the user's week: the daily reports they sent (Gmail, subject "דו״ח יומי"), the calendar, and anything they paste. Propose a short list of items for "מה היה לנו" and "מה יהיה לנו", and leave out internal matters (fundraising meetings, consultants, team calls) unless asked. Confirm the list with the user (AskUserQuestion) before writing.
2. **Start the issue.** Copy the latest `newsletter/issue-NN.html` (or `issue-template.html`, which is the current layout) to the next number. Set the `<!-- כותרת: -->`, `<!-- נושא: -->`, the issue number and date in the blue bar, and the hidden preview line.
3. **Write.** Short, direct Hebrew. Credit the lobby for what it did. Never invent facts, quotes, numbers or bill texts: what you don't have yet goes in as a yellow placeholder `<span style="background:#FFE27A;color:#1D2E67;padding:0 4px;">[מה חסר]</span>` and you list it for the user.
4. **Build.** `cd newsletter && python3 publish.py issue-NN.html`. It stops on a missing image, an unknown link id or an unfilled `{{...}}`. Outputs go to `newsletter/out/issue-NN/`.
5. **Check at phone width** before showing it: `node tools/preview_mobile.js out/issue-NN/preview.html shot.png` and look at the screenshot.
6. **Push** the branch: the email loads images and PDFs from the repository (see "Assets" below). Then publish and give the user BOTH links in every reply about the issue, every time: `out/issue-NN/pulseem-copy.html` (the newsletter is sent with Pulseem; one button copies the whole HTML, one copies the subject line) and `out/issue-NN/web.html` to view it. Republish both after every change.
7. **Send (the user does this):** Mailchimp → Create → Email → Code your own → Paste in code; paste the subject in "Subject line".

## Files

| File | What it is |
|---|---|
| `STYLE.md` | All the rules: structure, wording, colours, Gmail and Mailchimp constraints |
| `issue-NN.html` | One file per issue, the source |
| `issue-template.html` | The current layout to start from |
| `publish.py` | Builds every output of an issue |
| `tracking/links.py` | Every link in an issue, by id: `href="{{T:id}}"` |
| `images/`, `docs/` | Pictures and downloadable PDFs; referenced as `{{IMG:images/x.jpg}}` |
| `tools/frame_photo.py` | Puts a photo in the brand frame: `python3 tools/frame_photo.py in.jpg images/out.jpg "כותרת" "שורה משנית"` |
| `site_copy.py` | One page with a copy button per issue, for the website: `python3 site_copy.py issue-01.html issue-02.html ...` |

Outputs of `publish.py` (in `out/issue-NN/`): `pulseem.html` (what goes to Pulseem: direct links, no unsubscribe row, Pulseem adds its own; check its preview shows one), `pulseem-copy.html` (copy buttons), `mailchimp.html` (older Mailchimp version), `mailchimp-copy.html` (copy buttons), `web.html` (to view), `site.html` (block for the website), `email.html` and `copy-page.html` (sending from Gmail, a fallback).

## Things that went wrong before, and the fix

- **Layout breaks when pasted:** only simple `div` blocks with inline styles; no nested tables, no classes. Images get `width="100%"` and `style="width:100%;max-width:100%;height:auto"`.
- **Video in an email:** no email client plays video. Use a still with a play button that links to the video.
- **Hebrew text in AI-generated images comes out broken:** ask for the image without text and add the text yourself (or in Canva).
- **Real-world claims about people** (an MK, an official): no names unless the user asks, no accusations beyond what is published, and say so to the user before sending.
- **Brand frame for photos:** navy `#1D2E67`, gold `#F0C000`, logo bottom-left; `tools/frame_photo.py` does it.

## Assets

Images and PDFs are served from `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/newsletter/`. If the folder moves, put the new base URL (ending in `/`) in `newsletter/assets-url.txt`. Push before the user sends, or the images will be missing.
