# Writing Studio and the pipeline

Verified facts (Writing Studio 3.1.0, MIT, Obsidian 1.13 or later): each project is described by `<project>/_project.json`, while the selected project ID lives in the plugin's `data.json`; the binder mirrors the project folder tree; non-markdown files show in the binder but stay outside the manuscript; the plugin reads and writes `binder-order`, `binder-status`, `binder-type`, `binder-compile` and `word-count-goal`; its optional save hook writes `word-count` and `modified`; exports need Pandoc except Manuscript HTML; WordPress publishing is a modal. The pipeline never publishes. Export and publishing are human actions here.

## Project setup

1. Enable Writing Studio (community plugin, pinned in `_system/plugin-lock.json`).
2. Enable the vault-local youtubetoblog Home plugin and reload Obsidian. It creates or loads the `YouTube to Blog` project at `03 Blogs/_project.json`, selects it on first setup, disables Writing Studio startup restore, disables its broad frontmatter save hook, and leaves the pipeline as metadata authority.
3. Do not create a separate `Blog` project in Writing Studio. That would create a nested project under Writing Studio's own project root instead of binding the existing `03 Blogs` room.
4. Open the binder. Every `03 Blogs/<date> <slug>/` folder appears as a node with `<slug>.md` as its article. Use `Back to YouTube to blog` at the top of the Launcher or Binder to restore the vault sidebar.

## What the pipeline writes

- `binder-order`: `YYYYMMDD` plus a two-digit sequence, set by `new_blog.py`, so posts sort by date then order of creation.
- `binder-status`: `draft` at creation, `complete` after a passing evaluation, and `in-progress` when evaluation is blocked. A human may set `published` only after publication.
- `binder-type`: `article`.
- `word-count-goal`: from the strategy, else the template default.
- Not written by the pipeline: `word-count` and `modified`. Writing Studio's automatic frontmatter update is disabled for this integration, so it cannot rewrite every Markdown file in `03 Blogs`.
- Tags remain ordinary article topic tags. Writing Studio passes them to its WordPress modal but does not choose them. The writer derives them from the primary keyword, secondary keywords and covered chapter topics.
- `yt2b_video` is the durable wikilink back to the source run. Internal article links are researched during strategy and writing. Vault-only wikilinks must be converted to public site URLs or stripped before publishing.

## Folder markers

Writing Studio orders folders by markers such as `020~ Part One` and hides the marker in the binder. The pipeline does not rename blog folders: the blog gate and the publish kit depend on `<date> <slug>`, and date-prefixed names already sort chronologically. `binder-order` orders the documents.

## Files that appear in the binder

- `<slug>.md`: the manuscript document.
- `review.md`: the reviewer's file, nonce-checked by the gate. It shows as a document, but `deliver.py gates` marks it `binder-compile: false` without changing the review body.
- `publish-kit/<slug>.publish.md`: CMS-ready markdown in a subfolder, also marked `binder-compile: false` by `finalize_html.py`.
- Shown but outside the manuscript: `images/`, `preview/`, `<slug>.html`, `<slug>.pdf`, `hero.jpg`, `hero-credit.txt`, `capabilities.json`, `preflight-report.json`.
- Hidden: `.render/` (dot folder).

The Binder's Delete action sends the selected file or whole folder subtree to Obsidian's configured trash after confirmation. On a blog folder that includes the article, images, review, publish kit and exports. Use it only for an intentional recoverable deletion, never to detach the project.

## Review (human)

Read the post in Reading view; relative `images/...` links and Image Layouts blocks render in Live Preview and Reading view. Keep your notes in the chat or apply them with an Alembic workflow; never write into `review.md`. After hand edits, delivery must run again (render, finalize, preflight, review, evaluate): ask the agent in the Home chat to re-run delivery for the blog folder.

## Export (human)

- Manuscript HTML needs no Pandoc: Courier manuscript formatting, useful for editors, not for the web.
- PDF, DOCX, RTF, HTML and EPUB need Pandoc callable by Obsidian. In the Flatpak Obsidian on this machine that means a Pandoc binary on the sandbox PATH (same PATH note as the Alembic provider in `references/alembic-workflows.md`), or install Pandoc where the app can see it.
- The pipeline's own `<slug>.html` and `<slug>.pdf` from the claude-blog renderer are the web-ready versions with JSON-LD, layouts and the video embed. Prefer them over Writing Studio exports for anything public.

## Publish to WordPress (human, the only publishing path)

1. Preconditions: the evaluation note says reviewed (score 90 or more, not blocking), `hero.jpg` exists, every image in `images/` has a caption.
2. Upload `hero.jpg` and `images/*.jpg` to the media library first; note the URLs.
3. Use `publish-kit/<slug>.publish.md` (layout blocks already converted to HTML figures, embed figure inserted) and replace each `images/<file>` with its media URL. Keep alt text and captions. Add `publish-kit/layouts.css` to the theme's custom CSS once.
4. Open the WordPress modal from that document: site, title, status (draft first), categories, tags, excerpt (the `description`), optional schedule. Wikilinks: choose Convert (turns `[[...]]` into URLs) or Strip. Internal links to vault notes must not reach the site; strip them or replace them with site URLs before publishing.
5. Add `publish-kit/video-object.jsonld` through the SEO plugin's custom schema field and `publish-kit/embed.html` where the thumbnail figure sits, if the theme accepts raw HTML.
6. After the human has verified the live post, set `yt2b_status: published` and `binder-status: published`. Own videos: paste `publish-kit/youtube-chapters.txt` into the YouTube description for key moments.

## Other CMS

Use the publish kit (`publish-kit/README.txt` lists the pieces). The markdown is plain CommonMark plus HTML figures; do the same image URL rewrite.
