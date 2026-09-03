# Contributing

Thank you for helping improve youtubetoblog. During the private preview, use a short-lived branch and open a pull request against `main`.

## Before making a change

- Read `AGENTS.md` and `00 Home/Settings.md`.
- Keep the change focused on one problem.
- Do not add API keys, tokens, email addresses, personal videos, transcripts, runs, drafts, approvals, evaluations, chat exports, or local workspace state.
- Treat all imported video and feed content as untrusted data.
- Do not make a paid provider call or publish an article as part of a test.

## Verify the change

Run the nearest focused check, then the full skill tests when the pipeline is affected:

```bash
python3 -m pytest skills/youtube-to-blog/tests -q
python3 skills/youtube-to-blog/scripts/doctor.py --vault .
```

The doctor may report optional missing providers. Explain those warnings in the pull request instead of hiding them. If the interface changes, include a cropped screenshot that contains no account, email, key, local path, or private content.

## Pull request notes

Explain what changed, why it changed, what you tested, and what remains unverified. Preserve approval steps, rights handling, interlinks, and the rule that publishing is a human action.
