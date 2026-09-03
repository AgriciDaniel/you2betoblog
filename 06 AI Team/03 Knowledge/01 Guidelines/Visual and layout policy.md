---
type: yt2b-knowledge
title: Visual and layout policy
kind: guideline
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - guideline
---
# Visual and layout policy

Visual ladder per post, driven by Settings `visuals`:

1. `frames`: real frames at the brief's key moments, extracted by `hires_frames.py` at `frame_width` (default 1600) into `images/`, capped by rights.
2. `frames+charts`: plus inline SVG charts (blog-chart rules, dark-mode safe, source in the figcaption) when the brief lists data points the video states.
3. `frames+charts+ai`: plus AI images through Banana Claude (plan, approval note, generation, visual-critic review), only when the plugin is enabled.

Layout vocabulary (`skills/youtube-to-blog/references/layout-rules.md`):
`single` by default; `pair` (`image-layout-a`) for a before and after;
`feature+2` (`image-layout-d`) for a key moment plus two details; `triptych`
(`image-layout-h`) for three steps; `grid` (`image-layout-masonry-3`) for four
to six screens, rarely; `video`, `chart`, `callout`, `steps`, `table`, `quote`.

Rules: at most one multi-image group per about 600 words; never two groups
adjacent; groups only for same-aspect frames that compare or sequence;
captions always; no group in the introduction; charts never inside groups;
frames stay in the section that covers their timestamp; alt text is a full
sentence; images are local and relative.

The draft keeps the Image Layouts blocks (Obsidian renders them);
`layout_convert.py` writes the HTML groups for the renderer and the publish
kit, and `finalize_html.py` injects the grid CSS and ships `layouts.css`.

Cropping: a frame is cropped only when the crop makes it carry its point
better (a comparison table, a terminal pane, the slide area beside a webcam
overlay). The analyst decides with the frame in view and records
`key_moments[].crop` (fractions of the source, a reason of at least eight
words, optional `keep_aspect`); `hires_frames.py` applies it, keeps at least
45 percent of each dimension, and skips invalid crops with a warning. Never
by default, never to remove a person from a talking-head frame, never through
text the caption cites, never dropping on-screen attribution. A cropped frame
with a different aspect stays `single`. Rules and examples:
`skills/youtube-to-blog/references/brief-template.md`, section "Cropping".

Heroes: own mode crops `hero.jpg` (1200x630) from the hero moment or the
thumbnail; third-party mode generates one. `hero-credit.txt` always sits next
to it.
