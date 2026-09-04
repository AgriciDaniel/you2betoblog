---
type: yt2b-knowledge
title: install_plugins.py
kind: script
created: 2026-09-04
updated: 2026-09-04
tags:
  - yt2b
  - knowledge
  - script
---
# install_plugins.py

Reproduces the selected Obsidian plugins from `_system/plugin-lock.json`.

- `plan` is read-only and shows ids, versions, sources and patch state.
- `install` downloads pinned release files and builds patched plugins from exact upstream commits.
- Writing Studio is built before its compiled-bundle patch is applied.
- RSS Dashboard runs its unit tests, lint, type check and production build after its source patch is applied.
- Both patched builds run `npm audit --omit=dev`; a known production dependency vulnerability stops installation.
- Every installed file must match its locked SHA-256.
- `--replace` moves an existing differing plugin to a timestamped backup. Without it, the command stops.
- Existing plugin data is preserved. RSS data must contain the safe YAML placeholders or replacement stops.

The script writes only inside the selected vault's `.obsidian` folder. It does not install global packages or modify another vault.

Setup: [[00 Home/Help|Help]] and `docs/SETUP.md`.
