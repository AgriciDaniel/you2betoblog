---
type: yt2b-knowledge
title: evaluate.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---
# evaluate.py

Scores a delivered blog against the pipeline rubric and writes the evaluation note. Source: `skills/youtube-to-blog/scripts/evaluate.py`.

## Usage

`evaluate.py --vault PATH --run RUN_DIR --blog BLOG_DIR [--no-network]`

## Behaviour

- Reads `review.md` (Overall Score, P0 count, BLOCKING line, categories, issues), `preflight-report.json`, the post markdown, `images/manifest.json`, `analysis/segments.json` and `brief/video-brief.json`.
- Computes `overlap_ratio` (article 8-grams found in the transcript), `frames_in_place`, `attribution_ok` (creator and watch link in the first 200 words, disclosure line in third-party mode), `links_ok` (no youtu.be, allowed YouTube forms, HEAD 200 without redirect when the network is on), `thumbnail_ok` (network only), `verification_section` (a "What we verified" heading), `voice_flags` (taboo phrases from the root `VOICE.md`).
- Writes `05 Evaluations/<date>-<slug>.md` (result table, reviewer scorecard, gate table, findings, method) and updates the post's `yt2b_score` and `yt2b_status` (`reviewed` when the score is at least 90 and not blocking, else `blocked`).
- Prints the metrics plus `status`, `rubric_pass`, `evaluation_note` and `findings`.

## Exit codes

0 ok (findings are reported, not failures), 2 invalid input (missing run, blog or post markdown).

Thresholds: [[05 Evaluations/pipeline-rubric|pipeline-rubric]].
