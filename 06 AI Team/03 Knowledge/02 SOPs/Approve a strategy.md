---
type: yt2b-knowledge
title: Approve a strategy
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - sop
---
# Approve a strategy

When the strategist has proposed the angles for a video, the pipeline stops
and waits for you. This takes two minutes.

1. Open `04 Approvals/queue/<date>-<videoId>-strategy.md` (Home lists it under Approvals with status `requested`).
2. Read `## Request`: the recommendation, the angles with their reader task, keyword, template, the sections and moments they use, and the overlap verdicts against your existing posts. The full reasoning is in the run's `strategy.md`.
3. Tick the angles you want under `## Options`. `blog-1` is the companion hub; `blog-2` and `blog-3` are spokes that add their own value. Untick a spoke that reads like a variant.
4. Answer the seven questions per blog under `## Questions` on the `answer:` lines: audience, angle, voice, expertise to foreground, CTA, length, visuals. Leave a line blank to use the brief and the brand defaults.
5. Set the `status` property to `approved`.
6. Go back to Home and press "Write approved blogs", or tell the chat to continue.

The pipeline then creates one blog folder per ticked angle, extracts the
frames, researches, writes, renders and reviews each post, and records an
evaluation. You will see an outline approval next when Settings
`pause_for_outline` is true.

Decline with `status: declined` to stop this video. The queue note is set to
`failed` with the reason and nothing else changes.

Related: [[04 Approvals/policy|Approval policy]], [[06 AI Team/03 Knowledge/03 Scripts/approval|approval.py]].
