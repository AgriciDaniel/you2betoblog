# Public-readiness review

Date: 2026-09-05. Scope: the current working copy, including pre-existing uncommitted pipeline and release work. No commit, push, publication, paid provider request, or account change was performed. After user approval, the corrected Home plugin was synced into this vault with a timestamped backup; its data.json was preserved.

## Verdict

The identified code defects are fixed in the working repository. Public-release acceptance still needs native Obsidian checks and a current end-to-end example. The public blog dependency is now pinned to an anonymously accessible release; the earlier private-mirror link has been corrected.

The user approved the protected-file fixes and they have been applied. The local dashboard bundle matches the updated lock. Obsidian was launched after the update, but native commands were refused because its CLI is disabled; no native interaction pass is claimed. Native/live acceptance and the analyzer commercial-use decision remain outstanding.

## Changes made in the working repository

- Rebuilt the README around the four supplied screenshots and the actual workflow; retained accurate preview limitations.
- Standardized the README/setup product name to the dashboard's `you2toblog`.
- Labeled the historical article and scorecard accurately. The screenshot's old gate clearance is not current acceptance evidence.
- Corrected the System Manual paths and the setup action name.
- Documented the unavailable required blog dependency and the analyzer's non-commercial license.
- Included upstream license texts for both bundled themes and their embedded fonts.
- Added ignore rules for saved RSS sources, RSS state, attachments, all session export formats, private learning notes, and lint cache.
- Updated the manual's adapter version, editorial approval kind, and complete-rubric requirement.

## Findings and resolution

| ID | Priority | Evidence in reviewed baseline | Reproduction and consequence | Applied change or remaining action |
|---|---|---|---|---|
| R1 | High | `skills/youtube-to-blog/scripts/pipeline.py`, `completion_violations` | A report with only a passing Gate 6 and a matching passing evaluation is accepted. Earlier gates can be absent. | Require exactly one passing gate for each number 1 through 6. |
| R2 | High | Same function | Revoking strategy approval after gating leaves completion accepted because approval state is not rechecked. | Recompute the local contract at completion, including approval, selected angle, site, and run identity. |
| R3 | High | `contract.py`, `contract_gate` | A Critical finding is cleared by an editorial `accept-high` approval. | Critical findings always block; only High findings can use that waiver. |
| R4 | High | `pipeline.py`, `cleanup_video_cache` | A synthetic run with video ID `*` removed an unrelated cached test video. Reproduction used a temporary fixture only. | Require an 11-character YouTube ID before completion and cache cleanup. |
| R5 | High | `deliver.py`, `cmd_gates` | A failed external preflight can leave an old unblocked report available downstream. | Mark any external failure, absent gate, or failed gate as blocked. |
| R6 | Medium | `plugins/youtubetoblog-home/main.js`, `HomeView.process` | Submitting an existing queue note starts a fresh agent prompt using current chips, which can disagree with stored rights/mode. Rapid submissions lack a guard. | Open existing items for explicit resume, preserve stored choices, and guard simultaneous submissions. |
| R7 | Medium | Home defaults, sidebar counts, event handling | Plugin defaults are separate from the Settings note; a blocked run counts as Active; refresh is tied to vault events before metadata can update. | Read Settings defaults, count active lifecycle states explicitly, and refresh after metadata changes. |
| R8 | Medium | `install_plugins.py`, `install_one` | The already-current path verifies the RSS bundle but returns before validating its saved-note template. | Validate existing RSS data before treating it as current. |
| R9 | Medium | `contract.py`, `valid_site_url` | Private IPs, IPv6 loopback, and subdomains of example.com pass as real publication URLs. | Reject local/reserved targets and malformed or credential-bearing URLs. |
| R10 | Medium | `release_check.py` | README assets are hard-coded; skipped tests are marked passed; dashboard behavior and local bundle hashes are outside the release verdict; broken internal symlinks pass. | Inspect actual README image references, report skipped tests as unverified, add dashboard tests and local integrity checks, and require symlink targets to exist. |
| R11 | Medium | Supplied article and evaluation images | Heading anchor syntax is visible in the article, and historical score clearance conflicts with current gates. | Captions now state the limits. A fresh native article and scorecard still need acceptance and new captures. |
| R12 | Resolved | Documented claude-blog repository | The old private-mirror URL returned 404. A follow-up found the official public release repository. | Pinned AgriciDaniel/claude-blog v2.1.1 at aec971ac511370c6216cd93776c9cf2fec97b32a, recorded nine required file hashes, and corrected the installation guide. |
| R13 | Release scope decision | Pinned video-analyzer LICENSE | Commercial use requires prior written permission from its author. | Disclosed in README/setup/notices. Decide whether to release with that scope, obtain permission, or replace the dependency. |

The applied dashboard changes also add an input label, pressed state for the rights/mode controls, keyboard access to recent runs, visible focus styles, narrow-pane layout handling, a Setup and help entry, and a provider-cost explanation. These have code and mocked behavior evidence, not native visual acceptance.

## Verification evidence

| Check | Result | Limits |
|---|---|---|
| `python3 -m pytest skills/youtube-to-blog/tests -q` on working baseline | 111 passed | Offline fixtures, not provider acceptance |
| `ruff check skills/youtube-to-blog/scripts skills/youtube-to-blog/tests` | Passed | Python lint only |
| `node --check plugins/youtubetoblog-home/main.js` | Passed | Syntax only |
| Strengthened `release_check.py --vault .` | Passed across 212 files in the final push check | Offline verification; native/live acceptance is separate |
| Anonymous pinned Obsidian installer in an isolated vault | Six plugins installed, all expected bundle hashes verified | Existing host tools were available; not a fresh operating system or native Obsidian launch |
| Patched plugin build checks invoked by installer | Passed, including production dependency audit commands, RSS unit tests/lint/type check/build, and Writing Studio build | Installer suppresses successful subcommand output, so individual test counts are not recorded here; full development dependency audit was not rerun |
| Git history pattern scan | One reachable commit, 185 unique blobs, no matching secret/email patterns | Reachable content only; no remote visibility change or history rewrite |
| Tracked files also ignored by Git | None at baseline | New data still needs review before staging |
| Added privacy ignore patterns | Verified for saved RSS notes, RSS data, attachments, session JSON, and the private fix patch | They do not protect files already committed in another clone |
| README/setup/notices relative links | All resolved | External dependency links evaluated separately |
| Applied Python suite | 134 passed | Includes 21 patch regression cases and two optional-RSS doctor tests; offline fixtures |
| Applied `node --test plugins/youtubetoblog-home/tests/home.test.cjs` | 10 passed | Obsidian API stubs, no native app |
| Applied lint and JavaScript syntax | Passed | No native guarantee |
| Approved patch | Applied after applicability check and backup | Pre-existing changes preserved; patch must not be applied again |
| Normal setup doctor | Passed with no required failures | Optional Whisper and AI-image keys absent |
| Write-ready doctor | Failed only on empty `site_url` | Waiting for the real URL; no keys printed |

The candidate release scan initially flagged a synthetic URL fixture as email-shaped. The fixture now constructs that test URL without embedding an address-shaped literal. No real credential or personal address was involved.

## Application acceptance coverage

| Surface | Reviewed now | Still needed |
|---|---|---|
| Home capture and modes | Source, supplied screenshot, offline behavioral tests | Native click/keyboard test and invalid/missing-provider feedback |
| Sidebar and counts | Source, screenshot, offline count regression | Live refresh after metadata changes, narrow/short windows, restart |
| Feeds / Discover | Pinned build and patch installer checks | Native discovery, hostile-title save, same-name collision, restart persistence |
| Sources / Queue | Navigation targets and source-to-queue code | Native two-way links, repeated source promotion, explicit resume |
| Videos / Blogs | Notes and supplied screenshots | Current article rendering, frames and timestamp navigation, empty/populated states |
| Approvals / Evaluations | Policy, code, offline tests and reproduced bypasses | Current native approval cycle and fresh evaluation |
| Settings / Help | Paths, documentation, Settings default handling | New-user setup and missing-setting recovery |
| Writing Studio | Patched reproducible install and project startup code | Clean-profile startup, return navigation, editing, export and restart |

Native computer control is unavailable in this session. No simulated browser or API-stub result is presented as a native Obsidian pass.

## Fastest path to a release decision

1. Completed: apply the approved patch, update the local Home plugin with backup, and run working-copy checks.
2. Distribution resolved: public claude-blog v2.1.1 cloned without authentication and pinned. Its five required scripts and four agents exactly match the integrated 2.1.0 plugin payload. The public renderer produced the fixture HTML successfully. Full fresh-machine setup remains unverified.
3. Decide the intended commercial/non-commercial scope in light of the analyzer license.
4. Supply the real publishing site URL for the local acceptance run. Do not invent it or make it a default for all users.
5. Complete native Home, Queue, approval, Writing Studio, and RSS acceptance. Mark optional features experimental if deliberately deferred.
6. Run one explicitly authorized owned-video example through the current full workflow and review the result. Paid calls need separate authorization.
7. Capture the corrected article and evaluation, inspect the final public file selection and diff, and make the publication decision explicitly.

## Sources

- [Pinned video-analyzer license](https://github.com/docusphere/video-analyzer/blob/151e8782c564093c3aa7339e2adc744aab25001b/LICENSE), fetched 2026-09-05.
- [Public claude-blog v2.1.1](https://github.com/AgriciDaniel/claude-blog/releases/tag/v2.1.1), fetched anonymously and verified at commit aec971ac511370c6216cd93776c9cf2fec97b32a on 2026-09-05. The original private-mirror link was the source of the earlier 404.
- Plugin and theme upstream license endpoints were checked on 2026-09-05; the five installed third-party plugin license identifiers match the existing notices. Bundled license copies are under `docs/licenses`.

## Follow-up verification and deployment boundary

The doctor now treats disabled RSS as optional while still requiring safe RSS data when it is enabled. Two focused regression tests cover that distinction.

The public blog release is byte-identical to the integrated plugin for the nine required files. Eight also match the current user-profile runtime; the user-profile analyze_blog.py contains separate local additions and was left untouched. This is why public dependency compatibility was checked against the pinned plugin and with a public-renderer smoke test, not inferred from the customized user installation.

The local Home plugin update preserves data.json and keeps a timestamped backup under the ignored plugin directory. Other installed plugins and global Claude tools were not replaced. Native Obsidian reload/interaction is still required.

## Browser and push follow-up

The browser harness found and resolved short-window input compression. It now passes at three widths (1440, 900, 640), with no horizontal overflow or page errors, and exercises eleven navigation targets plus invalid URL and chip-state checks. Source is retained under `plugins/youtubetoblog-home/tests/browser_smoke.py`; all browser network requests are blocked and Obsidian APIs are synthetic.

A subsequent historical-run audit reported one incomplete run and one completed legacy run missing provider authorization evidence with a retained cached video. Those private files remain excluded from the push and were not retroactively approved or cleaned up.

The user authorized committing and pushing the reviewed repository work to the configured GitHub remote. The target was verified as the private repository AgriciDaniel/you2betoblog, main branch. Native/live gaps remain documented; this push does not change repository visibility or constitute public-release acceptance.
