---
type: yt2b-knowledge
title: Attribution and rights policy
kind: guideline
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - guideline
---
# Attribution and rights policy

Rights are set per run (`own` or `third-party`) in the queue note and copied
to `run.md` and the post's `yt2b_rights`. `ask` means the pipeline asks once
before fetching. The publisher owns the fair-use judgment; the pipeline makes
the conservative choice by default.

| Rule | own | third-party |
|---|---|---|
| Frames | up to `max_frames_own` (default 8) | up to `max_frames_third_party` (default 4), reduced size |
| Frame captions | label and timestamp | label, video title, creator and timestamp |
| Hero | thumbnail or a key frame | never the creator's thumbnail; generated (Banana Claude or `generate_hero.py`) |
| Quotes | timestamped | at most 3 of 25 words, timestamped |
| Creator's experience | first person allowed with substantiation | reported in the third person |
| Disclosure | AI-assistance note naming the reviewer | the disclosure template (independent companion, quotations are the creator's words, not affiliated, drafted with AI assistance and reviewed by a named person) |
| Chapters file | written to the publish kit | not written |
| Credits | `images/CREDITS.txt` with title, channel, watch URL, license field, retrieval date and one line per frame | same, plus the commentary notice |

Always: creator named and video linked in the first 200 words; deep links in
the `www.youtube.com/watch?v=ID&t=NNs` form; the VideoObject uses the
`thumbnail` URL from the metadata, never an assembled one; no remote assets in
the post; the `.avt` analysis files stay untouched (video-analyzer's license).

Full patterns: `skills/youtube-to-blog/references/companion-rules.md` sections 3 to 10.
