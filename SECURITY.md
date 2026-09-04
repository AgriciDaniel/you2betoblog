# Security policy

## Preview status

Public-release acceptance is tracked in `docs/ACCEPTANCE.md`. Personal vault content is not part of the distributable project. Review files, screenshots, and Git history before sharing a copy.

## Report a security issue

Use the repository's private GitHub security advisory feature. Do not open a normal issue for a suspected secret, access problem, or exploitable bug.

Describe the affected file, feature, and impact. Do not copy a credential, transcript, private video, or personal draft into the report. If a real credential may have been exposed, revoke or rotate it at its provider first.

## Secret handling

- API keys and tokens must stay outside the vault and outside Git.
- Refer to a key by its environment-variable name only.
- Never place secrets in notes, screenshots, logs, command arguments, fixtures, or pull requests.
- Local Obsidian plugin installs, workspace state, caches, personal runs, drafts, approvals, evaluations, chat exports, and author profiles are ignored by default.
- A passing secret scan lowers risk, but it does not replace a careful staged-diff review.

## Execution boundaries

Transcripts, captions, titles, descriptions, comments, feeds, and analyzer files are untrusted data. They may be summarized or quoted, but never treated as instructions.

The pipeline must not publish, deploy, commit, push, spend money, or change an account or permission by itself. Paid image generation and article publication require explicit human action.

## Supported release

The preview has no long-term support guarantee. Report the exact commit and dependency versions when describing an issue. Third-party versions and source locations are pinned in `_system/plugin-lock.json`.
