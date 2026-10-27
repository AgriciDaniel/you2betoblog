
# you2betoblog

<p align="center">
  <strong>Turn YouTube videos into reviewable blog articles — right inside Obsidian.</strong>
</p>

<p align="center">
  Collect the source. Inspect the evidence. Approve the direction.
  Refine the draft. Publish on your terms.
</p>

<p align="center">
  <a href="https://www.youtube.com/watch?v=L1Ub6s8XEcw">
    <strong>▶ Watch the Demo</strong>
  </a>
  ·
  <a href="docs/SETUP.md">Setup Guide</a>
  ·
  <a href="CHANGELOG.md">Release Notes</a>
  ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

<p align="center">
  <img src="docs/images/home-dashboard.png"
       alt="you2betoblog home dashboard showing video input, rights and writing mode selectors, navigation, and recent runs"
       width="100%">
</p>

> [!IMPORTANT]
> **Release status: acceptance is still in progress.**
> This project is not yet a fully accepted public release. Review the
> [acceptance and release evidence](docs/ACCEPTANCE.md) and
> [setup prerequisites](docs/SETUP.md) before installing or relying on it.
> The required video analyzer has non-commercial licensing restrictions.
> See [Licensing](#licensing) before using this project.

---

## The idea

A YouTube video can be the starting point for a much better article—but
getting from video to a publishable draft takes more than a transcript and
a prompt.

**you2betoblog** brings source analysis, article strategy, human approvals,
draft review, and quality evaluation into one connected workflow in your
Obsidian vault.

Instead of treating the generated article as an isolated output, the
workflow keeps the video, extracted evidence, approved direction, draft,
and evaluation connected so you can inspect the work before publishing.

### What you can do

- **Analyze videos:** collect metadata, captions, timestamped frames, and
  a structured content brief.
- **Explore article directions:** generate up to three article ideas and
  choose which ones to develop.
- **Control the workflow:** review strategy and, by default, approve the
  outline before continuing.
- **Inspect source evidence:** keep extracted frames and analysis in the
  corresponding video run.
- **Review the article:** check attribution, links, images, and available
  quality-evaluation results.
- **Finish in Obsidian:** refine the draft in Writing Studio, then export
  or publish it yourself.

The goal is a **reviewable writing process**, not unattended publishing.

---

## From video to article

<p align="center">
  <strong>01 · Capture → 02 · Analyze → 03 · Approve → 04 · Review → 05 · Finish</strong>
</p>

### 01 — Add a video

Paste a YouTube URL and record whether the video is your own or third-party
material. Rights information informs the applicable quotation, frame, and
attribution rules.

### 02 — Analyze the source

Collect available video metadata and captions, extract timestamped frames,
and prepare a structured content brief. Keep the analysis associated with
its video run for later inspection.

### 03 — Choose an article direction

Review up to three proposed article ideas and select the direction to
develop. Strategy approval is required; outline approval is enabled by
default.

### 04 — Review the draft

Inspect the generated article, source attribution, links, selected frames,
and available evaluation results before treating the draft as ready.

### 05 — Finish in Writing Studio

Make your final edits in your vault. Export or publish the article yourself
when you decide it is ready.

---

## Choose your workflow

| Action | What it does |
| --- | --- |
| **Process** | Takes a new video through analysis and strategy, then pauses for approval. |
| **Analyze only** | Stops after producing the content brief. |
| **Companion** | Creates an article designed to accompany the video. |
| **Expand** | Uses the video as one source in a broader article. |

**Important:** Process and Analyze only may use paid provider services.
Neither action publishes an article.

Approval pauses are part of the workflow, not a guarantee of factual
accuracy. Review the source and the generated content before use.

---

## Inspect the source, not just the output

Every article should be reviewable against the material that informed it.

Run notes keep analysis and extracted frames together, helping you trace
claims and article decisions back to the original video.

<p align="center">
  <img src="docs/images/video-analysis-frames.png"
       alt="Video analysis run showing extracted timestamped frames"
       width="100%">
</p>

Use the available source material to check context, attribution, and
whether a proposed article direction accurately represents the video.

## Review the article

Drafts can include:

- Timestamped links back to the video.
- Creator attribution.
- Selected video frames.
- Charts supported by source data.
- Links and other supporting material.

<p align="center">
  <img src="docs/images/example-created-blog.png"
       alt="Example generated blog article with source attribution and a timestamped frame"
       width="100%">
</p>

> [!NOTE]
> This is a historical example, not an accepted release fixture. The
> screenshot contains a visible heading-anchor marker, and native Markdown
> rendering remains an acceptance item.

---

## Quality evaluation

Each delivered article receives an evaluation covering the review score,
delivery gates, source overlap, frame placement, attribution, links, and
voice checks.

<p align="center">
  <img src="docs/images/evaluation-example.png"
       alt="Historical article evaluation showing a reviewer scorecard and preflight checks"
       width="100%">
</p>

> [!WARNING]
> The displayed evaluation predates the current six-gate contract.
> Its score and clearance are historical results—not proof that an article
> passes the current checks. A fresh, accepted example is still required.

Treat evaluation as a review aid, not a substitute for human judgment or
source verification.

---

## Your Obsidian workspace

The vault combines a local Obsidian interface with the files and tools
that support the writing pipeline.

### Workspace areas

`Home` · `Feeds` · `Discover` · `Sources` · `Queue` · `Videos` ·
`Blogs` · `Approvals` · `Evaluations` · `Settings`

A local Obsidian plugin provides the landing page and sidebar. The
pipeline skill, two specialist agents, templates, and operating guides
live alongside the content.

### Rights, approvals, and privacy

- **Rights-aware processing:** rights are recorded for each video.
  Third-party material is subject to tighter quotation, frame, and
  attribution rules.
- **Human approvals:** strategy approval is required; outline approval
  is enabled by default. Only an explicitly requested `--auto` run changes
  those approval pauses.
- **Credential separation:** API keys stay outside the vault and Git.
- **Private working data:** personal runs, drafts, decisions, evaluations,
  voice files, and chat exports are ignored by default.
- **Optional capabilities:** RSS discovery and AI image generation are
  optional. Paid images require separate approval.
- **Human-controlled publishing:** no article is automatically published
  by Process or Analyze only.

**Before sharing a copy of the repository**, inspect the actual file
selection. Default ignore rules are useful safeguards, not proof that
every personal or sensitive file is excluded.

---

## Installation and setup

**Start here: [Setup Guide](docs/SETUP.md)**

The current setup is desktop-focused.

### Prerequisites

You need:

- [Obsidian Desktop](https://obsidian.md/)
- [Claude Code](https://code.claude.com/)
- [Node.js](https://nodejs.org/) and npm
- [Python 3.11 or newer](https://www.python.org/)
- `yt-dlp`
- `ffmpeg` and `ffprobe`
- The required external video-analysis and blog tools
- Appropriate provider credentials for the capabilities you use

### What the setup guide covers

- The pinned Obsidian plugin installer.
- The Claude adapter and required tools.
- Provider keys and personal settings.
- The setup doctor and prerequisite checks.
- Video analysis and optional transcription configuration.

Video analysis uses Gemini. Videos without captions require an optional
transcription provider. A YouTube Data API key is not required by this
workflow.

> [!IMPORTANT]
> Fresh-machine installation, native Obsidian behavior, and live
> end-to-end acceptance remain release requirements. Treat optional
> features without completed acceptance as experimental.

Follow the setup guide and review its prerequisites before running the
pipeline or spending money on provider services.

---

## Development and project documentation

| Resource | Purpose |
| --- | --- |
| [Acceptance and release evidence](docs/ACCEPTANCE.md) | Review release readiness and outstanding acceptance work. |
| [Setup guide](docs/SETUP.md) | Configure the desktop workflow and dependencies. |
| [Changelog](CHANGELOG.md) | Review changes, upgrades, verification, and known limitations. |
| [Contributing](CONTRIBUTING.md) | Find contribution guidance and project checks. |
| [Security](SECURITY.md) | Learn how to report security issues. |
| [System manual](06%20AI%20Team/03%20Knowledge/System%20Manual.md) | Read the full operating manual inside the vault. |
| [Third-party notices](THIRD_PARTY_NOTICES.md) | Review dependency licensing and notices. |

Exact dependency versions and source links are recorded in
`_system/plugin-lock.json` and `THIRD_PARTY_NOTICES.md`.

---

## Contributors

- Benjamin · [@avalonreset](https://github.com/avalonreset)

Contributions, bug reports, and thoughtful feedback are welcome. Please
read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes.

---

## Licensing

### Original project code

The repository's original code is licensed under the MIT License.
See [LICENSE](LICENSE).

### Required video analyzer

The required
[video-analyzer license](https://github.com/docusphere/video-analyzer/blob/151e8782c564093c3aa7339e2adc744aab25001b/LICENSE)
permits personal, educational, and non-commercial use. Commercial use
requires prior written permission from the copyright holder.

**The repository's MIT license does not override the video analyzer's
separate restrictions.** Review the analyzer's license before using this
workflow, especially for commercial projects.

Dependencies retain their respective licenses. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

### Trademark notice

YouTube is a trademark of Google LLC. This project is not affiliated with
or endorsed by YouTube.

---

<p align="center">
  <strong>Better articles start with better source review.</strong>
</p>

<p align="center">
  <a href="https://www.youtube.com/watch?v=L1Ub6s8XEcw">Watch the demo</a>
  ·
  <a href="docs/SETUP.md">Get started</a>
</p>
