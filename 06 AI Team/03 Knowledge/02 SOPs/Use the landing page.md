---
type: yt2b-knowledge
title: Use the landing page
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - sop
---

# Use the landing page

The landing page is the `youtubetoblog Home` plugin. It replaces every empty tab (or open it with the play icon in the ribbon, or the command **Open youtubetoblog home**).

1. Open a new tab (Ctrl+T). The page shows the play glyph, the wordmark, one input and a row of shortcuts.
2. Paste a YouTube link into the input. Accepted forms: `youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/`, `youtube.com/live/`. Anything else gives the notice "Paste a youtube.com/watch?v= link".
3. Pick the chips under the input: rights `own` or `third-party`, mode `companion` or `expand`. The preselected chips come from the plugin settings (Settings > youtubetoblog Home), not from `00 Home/Settings.md`.
4. Press **Process** (or Enter). **Analyze only** does the same but stops after the brief. Esc clears the input.
5. What happens: the plugin writes `01 Queue/<YYYY-MM-DD>-<videoId>.md` with the same properties as `queue.py add` and the note `from the landing page`. If that video is already queued it says so and reuses the note. Then it opens Claude Code in the right pane through Agent Client and sends the run prompt: doctor once, setup if `BRAND.md` or `VOICE.md` is missing, fetch, analyze, segments, brief, strategy, then the strategy approval note in `04 Approvals/queue`. The agent stops there and tells you the path; approve it as in [[06 AI Team/03 Knowledge/02 SOPs/Approve a strategy|Approve a strategy]].
6. Without Agent Client the queue note opens instead and a notice explains that the plugin is needed. The video is still queued, so **Run the full pipeline** on [[00 Home/Home|Home]] picks it up.

The shortcut row opens Home, the Queue, Videos and Blogs views of `00 Home/Pipeline.base`, the Approvals and Evaluations views of `00 Home/Reviews.base`, and `00 Home/Settings.md`. The list under it shows the last five runs from `02 Videos` (title, status, updated); click a row to open its `run.md`.
