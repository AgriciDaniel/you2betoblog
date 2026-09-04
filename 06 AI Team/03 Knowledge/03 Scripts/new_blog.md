---
type: yt2b-knowledge
title: new_blog.py
kind: script
created: 2026-09-03
updated: 2026-09-04
tags:
  - yt2b
  - knowledge
  - script
---

# new_blog.py

**Purpose.** Creates the delivery folder for one approved angle: `03 Blogs/<date> <slug>/`, its `images/` folder and `<slug>.md` with the complete frontmatter, then registers the blog on the run note. The writer fills the body later; the folder contract (one `.md` besides `review.md`) starts here.

**Usage.**

```bash
python3 skills/youtube-to-blog/scripts/new_blog.py --vault "<vault>" --run "<run>" --slug "<slug>" --title "<title>" [--description TEXT] [--template ID] [--rights R] [--mode M] [--word-goal N] [--force]
```

**Inputs.** [[00 Home/Settings|Settings]] `author`, `language` and `site_url`; the run note for default rights and mode; today's existing blog folders for the binder sequence.

**Outputs.** Frontmatter: `title, description, date, author, slug` (equals the file stem), `tags, lang, canonical`, plus `type: yt2b-blog, yt2b_status: drafting, yt2b_score: 0, yt2b_video, yt2b_rights, yt2b_mode, yt2b_template`, and the Writing Studio fields `binder-order` (YYYYMMDD plus a two digit sequence) and `word-count-goal`. `canonical` is `<site_url>/<slug>`. An empty author or empty, local or placeholder site URL is refused before any blog folder is written. Body: `<!-- draft pending -->`. JSON: `blog_dir, md_path, slug, canonical, binder_order, warnings`.

**Exit codes.** 0 ok, 2 invalid input, missing run, or an existing folder without `--force` (`--force` rewrites the frontmatter and keeps the body), 3 setup policy failure.
