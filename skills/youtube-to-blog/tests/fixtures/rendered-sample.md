---
title: "Claude Code hooks: a practical guide from the video"
description: "What Claude Code hooks do, how to wire one, and the two mistakes the video demonstrates."
date: 2026-09-03
author: Daniel Agrici
slug: claude-code-hooks-guide
tags:
  - claude-code
  - hooks
lang: en
canonical: https://example.com/claude-code-hooks-guide/
type: yt2b-blog
yt2b_status: drafting
yt2b_score: 0
yt2b_video: "[[02 Videos/2026-09-03-claude-code-hooks-explained-abc123DEF45/run|run]]"
yt2b_rights: own
yt2b_mode: companion
yt2b_template: how-to-guide
binder-order: 2026090301
word-count-goal: 1800
---

Hooks let Claude Code run your own commands before or after a tool call. In the video [Claude Code Hooks Explained](https://www.youtube.com/watch?v=abc123DEF45), Daniel Agrici builds one hook from scratch and shows two mistakes that silently disable it. This guide follows the same path in reading order, with a link to the exact moment for each step.

> **Key Takeaways**
> - A hook is a shell command bound to a tool event; the settings file decides when it runs.
> - Test a hook with a no-op command first ([02:14](https://www.youtube.com/watch?v=abc123DEF45&t=134s)).
> - Two common mistakes: a missing executable bit and a matcher that never matches.

<figure class="video-embed">
  <iframe src="https://www.youtube-nocookie.com/embed/abc123DEF45" title="Claude Code Hooks Explained" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
  <noscript><a href="https://www.youtube.com/watch?v=abc123DEF45"><img src="images/video-thumb.jpg" alt="Watch: Claude Code Hooks Explained" loading="lazy"></a></noscript>
  <figcaption>Video: <a href="https://www.youtube.com/watch?v=abc123DEF45">Claude Code Hooks Explained</a> by <a href="https://www.youtube.com/@danielagrici">Daniel Agrici</a> (YouTube, published 2026-08-30).</figcaption>
</figure>

## What is a Claude Code hook? {#what-is-a-hook}

A hook is a shell command that Claude Code runs when a named event fires, such as a tool call about to start. The video defines it at [00:42](https://www.youtube.com/watch?v=abc123DEF45&t=42s): the command receives the tool input as JSON on stdin and can allow, block, or annotate the call with its exit code.

## Wiring the first hook {#wiring-the-first-hook}

Watch this moment: [01:30](https://www.youtube.com/watch?v=abc123DEF45&t=90s). The hook lives under `.claude/hooks/` and the settings file names it under a `PreToolUse` matcher.

<figure class="yt2b-layout image-layout-a">
<figure><img src="images/02-settings-before-0130.jpg" alt="Before: settings.json without a hooks block (01:30)"><figcaption>Before: settings.json without a hooks block (01:30)</figcaption></figure>
<figure><img src="images/03-settings-after-0212.jpg" alt="After: the PreToolUse hook in place (02:12)"><figcaption>After: the PreToolUse hook in place (02:12)</figcaption></figure>
<figcaption>Before and after adding the hook</figcaption>
</figure>

| Step | Command | Moment |
| --- | --- | --- |
| 1 | `chmod +x .claude/hooks/format.sh` | [02:40](https://www.youtube.com/watch?v=abc123DEF45&t=160s) |
| 2 | Add the matcher to `settings.json` | [02:12](https://www.youtube.com/watch?v=abc123DEF45&t=132s) |

```bash
chmod +x .claude/hooks/format.sh
```

## Common mistakes {#common-mistakes}

![The terminal shows the hook exiting with status 126](images/04-exit-126-0355.jpg)
*Exit status 126 means the hook file is not executable ([03:55](https://www.youtube.com/watch?v=abc123DEF45&t=235s))*

The second mistake is a matcher that never matches. The video shows the fix at [04:20](https://www.youtube.com/watch?v=abc123DEF45&t=260s): match the tool name exactly, not the file pattern.

## Frequently asked questions

### Does a hook run on every tool call?

No. A hook runs only for the events and matchers named in the settings file, so a `PreToolUse` hook with a `Bash` matcher ignores file edits.
