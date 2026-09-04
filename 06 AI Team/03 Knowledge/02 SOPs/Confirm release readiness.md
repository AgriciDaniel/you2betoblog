---
type: yt2b-knowledge
title: Confirm release readiness
kind: sop
created: 2026-09-04
updated: 2026-09-04
tags:
  - yt2b
  - knowledge
  - workflow/review
---
# Confirm release readiness

1. Run `python3 skills/youtube-to-blog/scripts/release_check.py --vault .` and keep its JSON result.
2. Run `python3 skills/youtube-to-blog/scripts/pipeline.py --vault . audit` and resolve every blocking state disagreement.
3. In an isolated clean vault, run the pinned plugin installer and its integrity check.
4. Complete the live matrix in `docs/ACCEPTANCE.md`, including an owned video, a licensed third-party video, a no-caption video, expand mode and the two native Obsidian plugin checks.
5. Ask a human editor who did not create the article to judge usefulness, accuracy, voice and rights.
6. Review the exact staged diff, third-party notices and license. Confirm that no personal run, draft, chat export, key or email address is included.
7. Decide separately whether to commit, push, make the repository public, publish an article or spend on an image. None of those actions follows automatically from a green check.

Related: [[06 AI Team/03 Knowledge/03 Scripts/release_check|release_check.py]], [[06 AI Team/03 Knowledge/03 Scripts/pipeline|pipeline.py]].
