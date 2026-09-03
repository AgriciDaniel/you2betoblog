---
type: yt2b-knowledge
title: finalize_html.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---
# finalize_html.py

Rewrites the rendered `<slug>.html` and writes the publish kit. Source: `skills/youtube-to-blog/scripts/finalize_html.py`. Runs after `blog_render.py`, before the reviewer. Idempotent.

## Usage

`finalize_html.py --vault PATH --run RUN_DIR --blog BLOG_DIR`

## Behaviour

- Replaces the renderer's JSON-LD with exactly one script: `{"@context": "https://schema.org", "@graph": [BlogPosting, Person]}`. BlogPosting is the renderer's node kept verbatim (`wordCount` included) plus `@id` (`<canonical>#article`) and `author: {"@id": ...}` when a Person exists. Person comes from `06 AI Team/03 Knowledge/04 Voice/Author Profile.md` (name, url, job_title, same_as) and Settings `author`; nothing is invented.
- Injects `<style id="yt2b-styles">` with the layout grid and video figure CSS when the page uses them.
- Publish kit in `<blog>/publish-kit/`: `video-object.jsonld` (VideoObject with `thumbnailUrl` from the metadata, `uploadDate` from `timestamp`, duration, `embedUrl` youtube-nocookie, watch `url`, `isPartOf`, creator), `embed.html`, `layouts.css`, `<slug>.publish.md` (layout blocks converted), `youtube-chapters.txt` (own mode, at least three valid chapters, `MM:SS Title`), `README.txt`.
- The VideoObject is not placed in the preview HTML because the preview has no player; the README says where it goes.
- Prints `{html, schema_nodes, person, embed_present, layout_css_injected, publish_kit, warnings}`.

## Exit codes

0 ok, 2 invalid input (missing html, metadata or BlogPosting node).

Checklist: [[06 AI Team/03 Knowledge/01 Guidelines/SEO and AI citation checklist|SEO and AI citation checklist]].
