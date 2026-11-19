---
name: openverse
description: Find openly licensed music, sound effects and images through Openverse (WordPress/openverse, api.openverse.org) - over 800 million CC0 / CC BY works from Freesound, Jamendo, Wikimedia and more, each with its licence and a ready attribution line. Use when a video, reel or page needs a music bed, a real recorded sound or a picture you may use legally, and the sfx-kit bank doesn't have it.
---

# Openverse

Source: github.com/WordPress/openverse (the search engine and API behind openverse.org). The repository is the service itself (API + frontend); what we use is its public API, no key needed (rate-limited).

```sh
python3 -I .claude/skills/openverse/scripts/search.py "tense documentary pulse" --category music --min-dur 30
python3 -I .claude/skills/openverse/scripts/search.py "rubber stamp" --category sound_effect
python3 -I .claude/skills/openverse/scripts/search.py "Knesset" --type images
```

Each line: title, creator, licence, file `url`, landing page, duration and an `attribution` line.

## Rules

- **Licences:** default filter `cc0,by`. CC0 needs nothing; **CC BY needs credit** – paste the `attribution` line into the post caption and the film's `CREDITS`. Never use NC (not commercial) or ND for the organisation's content, and ask before SA.
- Download each file into its own new folder in the scratchpad; never into the repo (it is public).
- Before using a track, check it (length, loudness, that it actually is music and not speech) with the `earshot` skill (`describe`, `realness`), and cut the music on a bar line.
- Prefer `sfx-kit` (CC0, curated) for effects; use Openverse for music beds and anything sfx-kit lacks.
