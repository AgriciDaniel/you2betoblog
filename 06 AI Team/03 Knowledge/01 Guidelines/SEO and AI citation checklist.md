---
type: yt2b-knowledge
title: SEO and AI citation checklist
kind: guideline
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - guideline
---
# SEO and AI citation checklist

What every delivered post carries, and who checks it.

| Item | Rule | Checked by |
|---|---|---|
| Title and description | accurate, page-specific, consistent with the visible content | blog-seo, blog-reviewer |
| Headings | one H1 (the title), H2 per reader task, H3 only below H2, `{#id}` on link targets | blog-seo, Gate 5 (anchors) |
| Canonical | `canonical: <site_url>/<slug>/` in the front matter | Gate 5 |
| Key Takeaways box | after the introduction, 3 to 5 self-contained bullets | blog-reviewer |
| What we verified | table with claim, verdict, source | evaluate.py |
| Sources | Tier 1 to 3, stable URLs that answer 200 without redirect | Gate 5, evaluate.py |
| Internal links | 3 to 10 descriptive anchors, hub and spokes link both ways | blog-seo |
| Images | local, relative, alt sentence, width and height where known, hero 1200x630 | Gate 3, Gate 5 |
| Schema | one JSON-LD script: BlogPosting (renderer node with `wordCount`, `@id`, author reference) plus Person; the VideoObject ships in `publish-kit/video-object.jsonld` for the page that renders the player | Gate 3, Gate 5, finalize_html.py |
| VideoObject fields | name, description, `thumbnailUrl` from the metadata, `uploadDate` ISO 8601, duration PT form, `embedUrl` youtube-nocookie, `url` watch link, `isPartOf`, creator; no Clip or SeekToAction for YouTube-hosted video; key moments come from the YouTube chapters instead | finalize_html.py |
| Video links | `www.youtube.com/watch?v=ID&t=NNs`, `@handle`, never `youtu.be` | evaluate.py |
| Attribution and disclosure | creator up front; third-party disclosure line; own-mode method and AI notes | evaluate.py, blog-reviewer |
| Style | no em dashes, no filler phrases from the VOICE taboo list, readability matched to the audience | blog-writer, evaluate.py |
| Reviewer | score at least 90, zero P0, `Nonce:` line, final `BLOCKING:` line | Gate 4 |

References: `~/.claude/skills/blog/references/quality-scoring.md`, `schema-stack.md`, `eeat-signals.md`, `video-embeds.md`.
