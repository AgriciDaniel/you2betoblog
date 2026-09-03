---
type: yt2b-knowledge
title: layout_convert.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---
# layout_convert.py

Converts Image Layouts fenced blocks to HTML figure groups for the renderer and back. Source: `skills/youtube-to-blog/scripts/layout_convert.py`. Standard library only.

## Usage

- `layout_convert.py --md "<blog>/<slug>.md" --out "<blog>/.render/<slug>.md"` (default `--to html`)
- `layout_convert.py --md PATH --out PATH --to obsidian` (reverse)

## Behaviour

- A fenced block with info string `image-layout` or `image-layout-<name>` becomes `<figure class="yt2b-layout image-layout-<name>">` with one `<img>` per image line (nested `<figure>` plus `<figcaption>` when the image has a caption) and the group `<figcaption>` from the `caption` option.
- Wikilinks `![[file|caption]]` resolve to `images/<file>` when the file exists under `images/`; markdown images pass through; `descriptions` become per-image captions; `fit`, `align`, `width` become `yt2b-*` classes; Obsidian-only options are dropped with a warning.
- Every other fenced block (code, nested examples with four backticks) is left untouched. Running `--to html` twice is a no-op.
- Prints `{blocks, out, to, warnings}`.

## Exit codes

0 ok, 2 markdown not found.

Rules: [[06 AI Team/03 Knowledge/01 Guidelines/Visual and layout policy|Visual and layout policy]] and `references/layout-rules.md`.
