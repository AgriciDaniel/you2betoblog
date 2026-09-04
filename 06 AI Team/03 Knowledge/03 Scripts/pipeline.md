---
type: yt2b-knowledge
title: pipeline.py
kind: script
created: 2026-09-04
updated: 2026-09-04
tags:
  - yt2b
  - knowledge
  - script
---
# pipeline.py

Deterministic controller for pipeline checkpoints and the final local state transition. It never calls a model, downloads, publishes or spends money.

## Commands

- `pipeline.py --vault PATH inspect --run RUN` reports current artifacts and the next action.
- `pipeline.py --vault PATH authorize --run RUN --current-request analyze|full` records provider authorization from the current request. Use only when that request actually exists.
- `pipeline.py --vault PATH check-write --run RUN --blog BLOG` enforces setup, provider authorization, strategy approval and outline approval before writing.
- `pipeline.py --vault PATH complete --run RUN --blog BLOG [--keep-video]` requires all delivery gates and a passing matching evaluation for every registered blog. It also requires at least as many registered blogs as the approved strategy selected. It then updates the run and queue and performs the configured cache cleanup.
- `pipeline.py --vault PATH audit [--run RUN]` reports stale approvals, missing authorization, queue disagreement, incomplete runs and leftover completed-run cache files.

`complete` deletes only regular files matching `.cache/video/<videoId>.*` under the selected vault. It never deletes a blog, source note, transcript, approval or evaluation.

Related: [[06 AI Team/03 Knowledge/02 SOPs/Confirm release readiness|Confirm release readiness]], [[skills/youtube-to-blog/SKILL|YouTube to Blog skill]].
