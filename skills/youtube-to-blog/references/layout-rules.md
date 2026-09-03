# Layout rules

A small, deterministic layout vocabulary for posts written from video frames.
The writer picks from this list per section; `layout_convert.py` turns the
Image Layouts blocks into HTML figure groups for the renderer and the publish
kit, and `finalize_html.py` injects the matching CSS.

## Vocabulary

| Name | Use it when | Markdown form | Images | Aspect rule |
|---|---|---|---|---|
| `single` | default for any frame | plain image line plus an italic caption line, no block | 1 | any |
| `pair` | two frames that compare (before and after) or follow each other | ```` ```image-layout-a ```` | 2 | same aspect |
| `feature+2` | one key moment plus two supporting details | ```` ```image-layout-d ```` | 3 | same aspect |
| `triptych` | three sequential steps of one action | ```` ```image-layout-h ```` | 3 | same aspect |
| `grid` | four to six screens of one flow (rare) | ```` ```image-layout-masonry-3 ```` | 4 to 6 | mixed allowed |
| `video` | the one embed figure (see `companion-rules.md` section 8) | raw HTML figure | 0 | 16:9 |
| `chart` | data points from the brief (blog-chart rules) | `<figure>` with inline SVG and a figcaption | 0 | 560x380 viewBox |
| `callout` | a warning, a tip or the creator's caveat | Obsidian callout `> [!tip]` or a blockquote | 0 | |
| `steps` | numbered procedure | ordered list, one action per item | 0 | |
| `table` | comparisons and the verification table | markdown table with a header row | 0 | |
| `quote` | a timestamped verbatim quote | blockquote with the citation pattern | 0 | |

## Verbatim block examples

Image Layouts syntax (plugin version 0.18.0, verified from its source): the
info string is the layout name, optional YAML options sit between `---` lines
inside the block, then one image per line. The wikilink alias is the
per-image caption.

`single` (no block):

```markdown
![The settings file shows a PreToolUse matcher pointing at the hook script](images/03-settings-after-0212.jpg)
*The matcher names the tool, not the file ([02:12](https://www.youtube.com/watch?v=abc123DEF45&t=132s))*
```

`pair`:

````markdown
```image-layout-a
---
caption: Before and after adding the hook
---
![[02-settings-before-0130.jpg|Before: settings.json without a hooks block (01:30)]]
![[03-settings-after-0212.jpg|After: the PreToolUse hook in place (02:12)]]
```
````

`feature+2`:

````markdown
```image-layout-d
---
caption: The failing run and the two details that explain it
---
![[05-failing-run-0340.jpg|The hook fails with exit 126 (03:40)]]
![[06-permissions-0350.jpg|File permissions without the executable bit (03:50)]]
![[07-matcher-0420.jpg|A matcher that never matches (04:20)]]
```
````

`triptych`:

````markdown
```image-layout-h
---
caption: Creating, registering and testing the hook
---
![[08-create-0500.jpg|Step 1: create the script (05:00)]]
![[09-register-0530.jpg|Step 2: register it in settings.json (05:30)]]
![[10-test-0600.jpg|Step 3: run a no-op test (06:00)]]
```
````

`grid`:

````markdown
```image-layout-masonry-3
---
caption: The six screens of the setup flow
---
![[11-a-0700.jpg|Screen 1 (07:00)]]
![[12-b-0710.jpg|Screen 2 (07:10)]]
![[13-c-0720.jpg|Screen 3 (07:20)]]
![[14-d-0730.jpg|Screen 4 (07:30)]]
```
````

`chart` (from blog-chart, dark-mode safe, inline SVG):

```html
<figure class="yt2b-chart">
  <svg viewBox="0 0 560 380" role="img" aria-label="Build time before and after the hook: 48 seconds to 31 seconds">...</svg>
  <figcaption>Source: the creator's measurement at <a href="https://www.youtube.com/watch?v=abc123DEF45&t=610s">10:10</a>, one machine, not repeated</figcaption>
</figure>
```

## Options

| Option | Values | Survives conversion |
|---|---|---|
| `caption` | text | yes, as the group `<figcaption>` |
| `descriptions` | list, one per image | yes, as per-image captions when the wikilink has no alias |
| `fit` | `cover`, `contain`, `natural` | yes, as class `yt2b-fit-<value>` |
| `align` | `left`, `center`, `right` | yes, as class `yt2b-align-<value>` |
| `width` | CSS length | yes, as class `yt2b-width-<value>` |
| `overlay`, `fromFolder`, `sortBy`, `limit`, `layout: custom`, carousel | Obsidian-only | dropped with a warning; do not use them in posts |

## Deterministic rules

1. `single` by default. A group needs a reason from the decision table.
2. At most one multi-image group per about 600 words of body text.
3. Never two groups adjacent; at least one paragraph of prose or one other element between them.
4. Groups only for frames of the same aspect ratio; a frame with a different aspect stays single. This covers cropped frames: a frame cropped by `hires_frames.py` (the brief's `crop` field) to a different aspect than its neighbours stays `single` unless its crop used `keep_aspect` to match them.
5. Captions always: every image line carries an alias (the caption), every group carries a `caption` option.
6. No group in the introduction; the introduction holds at most the embed figure.
7. Charts never inside groups; a chart is its own figure with a figcaption naming the source.
8. Total images per post are capped by rights (`max_frames_own`, `max_frames_third_party`); the manifest already respects the cap.
9. Images sit in the section that covers their timestamp; a frame never illustrates another section's claim.
10. Alternate element types: image, chart, callout, table; no two consecutive elements of the same type without prose between them.

## Decision table (apply per H2 section)

| Frames in the section | Relation between them | Same aspect | Section length | Position | Charts present | Layout |
|---|---|---|---|---|---|---|
| 0 | | | | | any | none, or `callout`, `steps`, `table` as the content needs |
| 1 | | | any | any | any | `single` |
| 2 | compare or sequence | yes | at least 300 words | not the intro | no chart adjacent | `pair` |
| 2 | unrelated | any | any | any | any | two `single`, separated by prose |
| 3 | one key moment plus two details | yes | at least 400 words | not the intro | no | `feature+2` |
| 3 | three steps in order | yes | at least 400 words | not the intro | no | `triptych` |
| 3 | mixed aspects or unrelated | no | any | any | any | `single` for the key frame, drop or move the rest |
| 4 to 6 | one flow, many screens | any | at least 600 words | not the intro | no | `grid` (rare) |
| any | a chart is the better proof | | | | yes | `chart` and at most one `single` |

Ties resolve toward `single`. When the 600-word budget is used, the next
candidate group becomes singles.

## Conversion notes

- The draft `<slug>.md` keeps the fenced blocks so Obsidian and Writing Studio
  render the layout. `layout_convert.py --md "<blog>/<slug>.md" --out "<blog>/.render/<slug>.md"`
  writes the renderer input; the reverse `--to obsidian` rebuilds the blocks.
- Wikilinks resolve to `images/<file>` when the file exists under the blog's
  `images/` folder. Frame names from `hires_frames.py`
  (`<nn>-<label>-<mmss>.jpg`) are distinctive; if two blogs in the vault share
  a file name, use the vault path in the wikilink (`![[03 Blogs/<folder>/images/<file>|caption]]`).
- The HTML form is one element per line: a `<figure class="yt2b-layout image-layout-<name>">` with one `<img>` per image (wrapped in a nested `<figure>` with a `<figcaption>` when it has a caption) and the group `<figcaption>` last. The renderer keeps `class`, `src`, `alt` and drops everything else, so no inline styles.
- CSS (`finalize_html.py` injects it and writes `publish-kit/layouts.css`): `image-layout-a` two equal columns, `image-layout-d` one large left plus two stacked right, `image-layout-h` three columns, `image-layout-masonry-3` three CSS columns, any other name `repeat(auto-fit, minmax(240px, 1fr))`, images `width:100%; height:auto`, single column under 640px.
