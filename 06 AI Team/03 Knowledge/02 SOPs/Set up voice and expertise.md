---
type: yt2b-knowledge
title: Set up voice and expertise
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - sop
---
# Set up voice and expertise

Run once before the first blog, again whenever the voice or credentials change. About fifteen minutes.

1. In [[Home]] press "Setup voice and expertise", or type `/youtube-to-blog setup` in the chat.
2. Answer the seven rounds: audience, positioning, voice, expertise and credentials, site and call to action, visuals, publishing target. Use real names, titles and links; they become the author bio and the Person schema on every post.
3. Optional: give it the paths of 5 to 10 published posts in your voice when it asks; it measures them with `blog style learn` and records the baseline in `VOICE.md`.
4. Check what it wrote: root `BRAND.md` and `VOICE.md` (`/blog brand show` prints them), [[Author Profile]], and `author`, `site_url`, `visuals` in [[Settings]].
5. Confirm the summary lists the `_alembic/` workflows as written; Writers Alembic picks them up on the next run.
6. Refresh later by running the same command: every answer is pre-filled, the files are rewritten, and workflows you edited by hand are kept unless you ask for `--force`.

Details for the agent: `skills/youtube-to-blog/references/setup-interview.md`.
