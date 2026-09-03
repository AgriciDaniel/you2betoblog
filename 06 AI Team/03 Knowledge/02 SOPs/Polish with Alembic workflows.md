---
type: yt2b-knowledge
title: Polish with Alembic workflows
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - sop
---
# Polish with Alembic workflows

1. Once: enable Writers Alembic and keep its default provider `default-claude-cli` and folder `_alembic`. On the Flatpak Obsidian, make `claude` reachable on the app's PATH (see `skills/youtube-to-blog/references/alembic-workflows.md`).
2. Open the draft `<slug>.md` in its `03 Blogs/` folder in editing view.
3. Select the passage, run `Writers Alembic: Run workflow` (or the hotkey) and pick a YT2B workflow: Fact-check flags first, then Attribute claims, De-slop, Tighten, Rewrite in my voice where needed, Answer-first intro, Alt text.
4. For the whole-note workflows (Key Takeaways box, FAQ, Meta description) place the cursor where the output should land, select nothing, run.
5. Read every result before moving on; `Ctrl+Z` reverts it. Fill each `[mm:ss]` with the deep link from `analysis/transcript.md` and resolve each `[VERIFY: ...]` marker.
6. When the text is final, ask the agent in the Home chat to re-run delivery for the blog so `<slug>.html`, `<slug>.pdf`, the review and the evaluation match the new text.

Catalogue and rules: `skills/youtube-to-blog/references/alembic-workflows.md`. Voice source: [[Voice rules]].
