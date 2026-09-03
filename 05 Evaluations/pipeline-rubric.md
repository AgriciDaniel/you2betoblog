---
type: yt2b-knowledge
title: Pipeline rubric
kind: guideline
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - evaluations
---
# Pipeline rubric

`evaluate.py` writes one note per delivered blog in this folder and mirrors
these thresholds as constants. The score and the blocking decision set the
post's `yt2b_status`; the other rows are findings for the editor and the
`rubric_pass` property.

| Metric | Threshold | What it means | How it is computed |
|---|---|---|---|
| `score` | at least 90 | the blog-reviewer's Exceptional band, the same bar Gate 4 enforces | `### Overall Score: N/100` parsed from `review.md` |
| `p0` | 0 | no load-bearing defect (fabricated number, broken structure, plagiarism risk) | bullets under the Critical heading of `review.md`, or 0 when it states "no P0" or "zero P0" |
| `blocking` | false | the reviewer cleared the post | the last `BLOCKING:` line of `review.md` |
| `gates_passed` | true | the five delivery gates passed in one run | `preflight-report.json`: `blocked` false and gates 1 to 5 all passed |
| `overlap_ratio` | at most 0.12 (companion), at most 0.06 (expanded) | the post is written, not transcribed | share of the article's 8-grams (lowercase, punctuation stripped, code and links removed) that appear in the transcript from `analysis/segments.json` |
| `frames_in_place` | true | every frame sits in the section that covers its timestamp | for each manifest image with `t_s`: the H2 block containing it must hold a deep link inside the brief section's time range (the image's own caption excluded) or a heading matching the brief section |
| `attribution_ok` | true | the creator is credited up front | channel name and `youtube.com/watch?v=<id>` within the first 200 words; third-party mode also needs the disclosure line |
| `links_ok` | true | no link will fail the gate or leak to a redirect | no `youtu.be`; every YouTube link is `www.youtube.com/watch?v=ID(&t=NNs)`, a `@handle`, a channel, a playlist or the `youtube-nocookie.com/embed/ID` player; with network on, every external link answers HEAD 200 without redirect (5 s timeout, at most 40 links) |
| `thumbnail_ok` | true when checked | the VideoObject thumbnail is reachable | HEAD 200 for `thumbnail` from `video.info.json` (network only, empty otherwise) |
| `verification_section` | true | the added-value element exists | a `## What we verified` or `### What we verified` heading |
| `voice_flags` | 0 | the post respects the voice profile | occurrences of the phrases listed under a "Taboo phrases" (or "avoid", "never use") heading in the root `VOICE.md`, or in its `taboo_phrases` property |

Status rule: `reviewed` when `score` is at least 90 and `blocking` is false,
else `blocked`. A blocked post stays in the vault with its evaluation and
`review.md` so the editor can repair it in Writing Studio and rerun delivery.

Everything here runs without network by default in tests; the pipeline runs
`evaluate.py` with network on so the link and thumbnail rows are real.
