---
type: yt2b-knowledge
title: release_check.py
kind: script
created: 2026-09-04
updated: 2026-09-04
tags:
  - yt2b
  - knowledge
  - script
---
# release_check.py

Offline check for the shareable repository projection. It scans tracked and intended untracked files, while respecting `.gitignore`, for secret-shaped content and email addresses. It reports only file, line and finding type, never the matched value.

It also validates JSON, Python syntax, existing internal symlink targets, the images actually referenced by README, local plugin and patch hashes, the pinned plugin plan, the complete Python suite, and the dashboard behavior tests. `--skip-tests` reports the tests as unverified and returns a non-passing overall result.

```bash
python3 skills/youtube-to-blog/scripts/release_check.py --vault .
```

The JSON result lists what remains unproven: provider credentials and quotas, live calls, native behavior on another computer, human editorial acceptance, publishing and deployment.
