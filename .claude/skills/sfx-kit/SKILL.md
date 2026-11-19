---
name: sfx-kit
description: 320 original CC0 sound effects (wyzowl/sfx-kit) with the data to choose, place and mix each one - whooshes, risers, impacts, cinematic hits, booms, pops, UI clicks, keyboard, pens and markers, paper and foley, notifications, shimmers, logo stings, applause, clocks, glitches, count-ups. Use whenever a video, reel, animation or interface needs sound effects, before synthesizing one in code. No credit required.
---

# SFX Kit (CC0)

Source: github.com/wyzowl/sfx-kit (also on Hugging Face `wyzowl/sfx-kit`). Licence CC0: free for any use, no credit.

The metadata lives here (`sounds.json`, `catalogue.md`, `GUIDE.md`); the WAV files (48 kHz, 24-bit, 67 MB) are not kept in this public repo. Fetch them once per session:

```sh
sh .claude/skills/sfx-kit/scripts/fetch.sh     # → SFX_KIT=~/sfx-kit ; files under ~/sfx-kit/sounds/<category>/
```

## How to use

1. Read `GUIDE.md` (maps on-screen moments to sounds) and search `catalogue.md` (one line per sound).
2. In code, load `sounds.json`: each entry has `use_for`, `avoid_for`, `tags`, `fits_seconds`, `sync.at` and `under_voiceover_db`.
3. **Place** a sound so its sync point meets the picture: start = moment − `sync.at`.
4. **Level:** the files are loudness-matched; under a voice, lower each by its `under_voiceover_db`.
5. Prefer these over code-synthesized effects (they read as real, produced sound). Check a choice with the `earshot` skill when it matters.

For videos of כח התערבות this works on top of `koach-reel` / `hyperframes` / `lemo-opuscar`: every thing that pops gets its own sound, and a different sound per type of event.
