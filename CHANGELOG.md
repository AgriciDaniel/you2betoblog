# Changelog

## 0.1.0 (unreleased preview)

Release notes prepared on 2026-09-05. No stable release or public-launch acceptance is declared. See [acceptance evidence](docs/ACCEPTANCE.md) for remaining checks.

### Added

- Obsidian workspace with Home, source discovery, queue, linked video runs, drafts, approval notes, evaluations, templates, and operating guides.
- YouTube-to-blog pipeline with companion and expand modes, per-video rights, source frames, strategy and outline approvals, and six delivery gates.
- Home dashboard with video input, rights and mode controls, recent runs, navigation, help, and accessible keyboard controls.
- Pinned plugin installation, public claude-blog v2.1.1 setup, supplied product screenshots, security guidance, and bundled third-party license texts.

### Fixed

- Completion now requires all six gates, current approvals, the selected article contract, and matching evaluated content. Missing gates and stale results block completion.
- Critical findings cannot be waived. Invalid video identifiers are rejected before cache cleanup.
- Dashboard submission guards prevent concurrent duplicates. Existing queue items open for explicit resume; defaults come from Settings.
- Dashboard controls stay usable in short windows, active counts exclude blocked and finished runs, and metadata changes refresh the sidebar.
- RSS installation verifies safe defaults even when the plugin is already installed. Disabled RSS remains optional.

### Security and privacy

- Release checks validate the Git file selection, credential patterns, email addresses, JSON, Python syntax, symlinks, README images, and pinned plugin integrity.
- Added coverage for modern GitHub tokens, AWS access identifiers, Slack tokens, Groq keys, and URLs containing credentials. Findings report locations and types without matched values.
- Git exclusions cover personal runs, drafts, approvals, evaluations, voice profiles, discovery saves, attachments, session exports, local environment files, and common credential containers.
- Independent detect-secrets 1.5.0 scanning with network verification disabled found no candidates in 248 text blobs across the two existing commits. This is bounded evidence, not a guarantee that sensitive data is impossible to include.

### Installation and upgrade

Follow [SETUP.md](docs/SETUP.md), inspect the pinned dependencies, install plugins, configure your own Settings, and run the doctor. Do not copy a working personal vault to distribute the template; use the tracked repository files.

Existing users should back up their vault and plugin data before updating. Reinstall the Home plugin with the documented installer and reload Obsidian. Preserve existing approvals and run notes. Historical completed articles must pass the current six-gate checks before being treated as accepted output; old scores do not satisfy the new contract.

The repository plugin version remains 0.1.0. The Home component has its own version. This update does not migrate or delete personal content, publish articles, or enable provider services.

### Verification and known limitations

- 140 Python tests and 10 dashboard behavior tests pass after the final credential-pattern regression additions.
- The browser harness passed at 1440x1000, 900x700, and 640x700 using synthetic Obsidian APIs. It does not establish native acceptance.
- Six pinned Obsidian plugins previously installed successfully in an isolated vault. The public blog renderer produced fixture HTML.
- Native Obsidian checks remain blocked by its disabled CLI. Live provider runs, fresh-machine acceptance, and editorial acceptance remain open.
- A real site URL must be configured before writing. Optional transcription and paid images need their own setup and acceptance.
- The required video analyzer restricts commercial use; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Repository MIT terms do not override dependency terms.
- Upstream build-only dependency audit findings remain recorded in the [acceptance matrix](docs/ACCEPTANCE.md). Production-only audits previously reported zero findings; that does not clear the development toolchains.

No release tag, deployment, visibility change, or stable release publication accompanies these notes.
