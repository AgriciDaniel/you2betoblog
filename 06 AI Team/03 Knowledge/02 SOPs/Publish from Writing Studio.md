---
type: yt2b-knowledge
title: Publish from Writing Studio
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - sop
---
# Publish from Writing Studio

Publishing is always a human action; the pipeline stops at a reviewed draft.

1. Check the Blogs view in [[Home]]: the post shows `reviewed` with a score of 90 or more, and `hero.jpg` exists in the folder.
2. Export, if a file is the goal: Writing Studio export command; Manuscript HTML needs nothing, PDF, DOCX, RTF, HTML and EPUB need Pandoc reachable by Obsidian. For the web, prefer the pipeline's own `<slug>.html` and `<slug>.pdf`.
3. WordPress: upload `hero.jpg` and `images/*.jpg` to the media library first, then open `publish-kit/<slug>.publish.md`, replace each `images/<file>` with its media URL, and start the WordPress modal (site, title, status draft, categories, tags, excerpt, schedule; wikilinks Convert or Strip).
4. Add `publish-kit/video-object.jsonld` through the SEO plugin's custom schema field and `publish-kit/layouts.css` to the theme once; place `publish-kit/embed.html` where the video figure sits if the theme accepts raw HTML.
5. After checking the live post, set `yt2b_status: published` and `binder-status: published` on the post. Own videos: add `publish-kit/youtube-chapters.txt` to the YouTube description.
6. Other CMS: same steps from `publish-kit/README.txt`.

Details: `skills/youtube-to-blog/references/writing-studio.md`.
