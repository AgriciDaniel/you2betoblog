---
type: yt2b-knowledge
title: Discover and queue sources
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - format/source
  - intake/discovered
---

# Discover and queue sources

Use RSS Dashboard for discovery and reading. Use youtubetoblog Home as the only pipeline intake authority. To preserve provenance, open a saved YouTube source and choose **Queue open source** in the left sidebar. The queue note receives `source_notes` and `discovered_via: rss-dashboard`; the source receives a `queue` backlink and `status: promoted`.

## Discover

1. Open **Feeds** to read subscribed sources, or **Discover** to browse new feeds.
2. Organize feeds with `source/youtube`, `source/rss`, `source/podcast` or `source/web` and an appropriate `format/*` tag.
3. Save an item only when it deserves durable research context. Saved notes go to `01 Queue/Discovery/Saved` and appear in [[01 Queue/Discovery/Sources.base|Sources]].

RSS Dashboard 2.6.0 is installed with a local safety patch. If a same-title file already exists, saving stops with a refusal notice. It never trashes the existing note. Remote titles, URLs, feed names, authors and tag lists are JSON-quoted before they enter YAML frontmatter. Do not replace the installed build with an unpatched community update.

## Promote a YouTube item

1. Open the saved `yt2b-source` note for the YouTube item.
2. Click **Queue open source** in the left sidebar.
3. Confirm the resulting root note in `01 Queue` has `type: yt2b-queue`, `status: queued`, `rights: ask` and a `source_notes` link.
4. Confirm the source note now has `status: promoted` and a `queue` backlink.
5. Decide `own` or `third-party` before fetch. Direct URL paste remains available only for intake that has no saved-source note to preserve.

Discovery state is never approval. Continue with doctor, fetch, analyze, brief and the required strategy approval in the documented stage order.

## Sync caution

RSS Dashboard stores metadata and Vault Shards v2 data in `01 Queue/RSS Dashboard Data`. On a new synced device, keep RSS Dashboard disabled until the vault has finished its first sync, then enable it. Enabling it before feed data arrives can propagate empty defaults.

Related: [[01 Queue/Discovery/README|Discovery hub]] · [[01 Queue/README|Queue guide]] · [[06 AI Team/03 Knowledge/System Manual|System Manual]]
