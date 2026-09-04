# Acceptance and release evidence

This project separates local proof from live and human proof. A green local check is necessary, but it does not prove that every provider, computer, video type, or editorial decision will work.

## Review on 2026-09-05

**Verdict: code fixes applied; native/live acceptance remains open.** See [the public-readiness review](PUBLIC-READINESS-REVIEW.md) for resolved defects, evidence, and remaining acceptance work.

- Working-copy baseline: 111 Python tests passed; Python lint and Home JavaScript syntax passed.
- Isolated installation: all six pinned Obsidian plugins installed and verified successfully, including both patched builds and their installer-required checks. This does not install the external Claude analysis/writing tools or prove native UI behavior.
- Git content review: one reachable commit and 185 unique blobs scanned with the release checker's credential/email patterns; no matches. This is a bounded pattern scan, not a guarantee that every sensitive string is detectable.
- Applied fixes: 134 Python tests and 10 mocked dashboard behavior tests pass in the working repository. The approved patch is applied; the local Home plugin is updated with a backup. Obsidian was launched after the update, but native test commands are blocked until its CLI is enabled.
- Public dependency resolved: claude-blog v2.1.1 was cloned anonymously at commit aec971ac511370c6216cd93776c9cf2fec97b32a. The required five scripts and four agents match the integrated plugin payload. Setup now points to the public release; a fixture rendered successfully with its HTML renderer.
- The required video analyzer's pinned license restricts commercial use. Its terms must remain prominent in the README and setup guide.
- The local write-ready doctor fails because Settings `site_url` is empty. This is a personalization requirement, not a reason to invent or ship a site URL for every user.
- Native Obsidian interaction, a fresh end-to-end provider run, editorial acceptance, and publication were not performed.

## Reproducible local checks

Run from the vault root:

```bash
python3 skills/youtube-to-blog/scripts/release_check.py --vault .
```

This checks the repository projection, secret-shaped content and email addresses, JSON files, Python syntax, internal symlinks, README images, the pinned plugin plan, and the complete Python test suite. It ignores personal files already excluded by Git.

To reproduce the Obsidian plugin set in an isolated vault, run the installer from `docs/SETUP.md`. It verifies exact upstream commits, applies the Writing Studio and RSS Dashboard patches, runs the RSS tests and build checks, and verifies the resulting files against `_system/plugin-lock.json`.

## Pipeline acceptance matrix

| Scenario | Current evidence | Public-release requirement |
|---|---|---|
| Owned video with captions, companion mode | One completed local run exists, but the historical article now fails the stricter Gate 6 because it predates the new controls | Run a new video from queue to reviewed article with a real site URL and all six gates green |
| Owned video without captions | Offline paths are tested, live transcription is not accepted | Run with an approved Whisper provider and verify transcript quality |
| Third-party video | Rights, disclosure, attribution, frame caps and quotation rules exist | Run one licensed third-party example and complete a rights review |
| Expand mode | Code paths and thresholds exist | Complete one live expanded article and compare it with the source video for added value |
| Long video override | Length policy exists | Test one intentionally approved video over the normal limit |
| RSS discovery and save | Patched source tests and isolated install pass | Native Obsidian save test with hostile title and same-name collision |
| Writing Studio handoff | Startup and return-navigation patch is reproducible | Native Obsidian test on a clean user profile, including restart and back navigation |
| Patched plugin dependency audit | Production dependency audits report zero findings. On 2026-09-04, the upstream build-only dependency trees still reported four High findings for Writing Studio, and one Low, one Moderate and one High for RSS Dashboard | Review or update the upstream development toolchains before treating the build process as hardened for public contributors |
| Optional AI images | Approval policy exists | Separate approved paid test, visual review, rights review and cost confirmation |
| Publishing | Intentionally human-only | Human preview, canonical check and explicit publish action on a staging site |

## Release decision

Do not call the project public-ready only because `release_check.py` passes. Before public release, complete the native and live rows above, remove or replace private-preview wording, confirm third-party notices and licenses, perform a final staged-diff review, and make the publication decision explicitly.

## Push verification on 2026-09-05

The configured GitHub target is `AgriciDaniel/you2betoblog`, branch `main`. It was confirmed private before pushing; pushing these changes does not authorize a visibility change or a public release.

Obsidian 1.13.7 is installed and was launched for native testing. Its CLI returned: "Command line interface is not enabled. Please turn it on in Settings > General > Advanced." The user was asked to enable it. Native results remain unverified until that capability is available.

The read-only audit of personal historical runs reports one unfinished run, and one older completed run missing authorization evidence with a retained cached video. Those personal files are excluded from Git. The audit did not manufacture approvals or remove the retained video.

The optional browser harness (`python3 plugins/youtubetoblog-home/tests/browser_smoke.py`) passed at 1440x1000, 900x700, and 640x700. It verified no horizontal overflow, a usable input height, no page errors, invalid-URL feedback, rights-chip accessibility state, setup/help, nine sidebar routes, and keyboard opening of a recent run. A short-window input compression defect was fixed during this pass. These results use synthetic Obsidian APIs and are not native acceptance.
