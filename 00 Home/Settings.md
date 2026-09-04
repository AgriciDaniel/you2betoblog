---
type: yt2b-settings
author: Daniel Agrici
site_url: ""
language: en
default_rights: ask
default_mode: companion
max_blogs_per_video: 3
frame_width: 1600
max_frames_own: 8
max_frames_third_party: 4
keep_video: false
pause_for_outline: true
max_video_minutes: 90
visuals: frames+charts
word_count_tolerance_percent: 30
updated: 2026-09-04
---

# Settings

Edit the properties above. Every script reads them through `yt2b_common.load_settings`; an empty value falls back to the default shown here.

- `author`: the byline written into every blog post and the Person node in the structured data (empty until setup fills it).
- `site_url`: your site root, used for canonical URLs and the author link (empty until setup fills it).
- `language`: caption language and the `lang` field of every post (default `en`).
- `default_rights`: `own`, `third-party` or `ask`; `ask` makes the agent ask once per video whose rights are unset (default `ask`).
- `default_mode`: `companion` for an article that stands beside the video, `expand` for a full article that uses the video as one source (default `companion`).
- `max_blogs_per_video`: how many angles the strategist may propose per video (default `3`).
- `frame_width`: pixel width of the frames extracted for articles (default `1600`).
- `max_frames_own`: frame cap per article for your own videos (default `8`).
- `max_frames_third_party`: frame cap per article for third-party videos (default `4`).
- `keep_video`: keep the downloaded video in `.cache/video` after the run instead of deleting it (default `false`).
- `pause_for_outline`: open an outline approval before drafting each article (default `true`).
- `max_video_minutes`: videos longer than this are refused unless `--force-long` is passed (default `90`).
- `visuals`: `frames`, `frames+charts` or `frames+charts+ai`; charts need data points in the brief, AI images need Banana Claude (default `frames+charts`).
- `word_count_tolerance_percent`: delivery blocks when the article differs from its word-count goal by more than this percentage, and warns at half this value (default `30`).
