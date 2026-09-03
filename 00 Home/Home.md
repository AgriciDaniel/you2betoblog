---
type: yt2b-dashboard
title: Home
created: 2026-09-03
updated: 2026-09-03
cssclasses:
  - yt2b-dashboard
  - aimh-dashboard
tags:
  - yt2b
  - dashboard
---

# youtubetoblog

Paste a YouTube link, shape the article, approve the important decisions, then finish it in Writing Studio.

> [!yt2b-nav] Workspace
> - [[00 Home/Home|Home]]
> - [[01 Queue/Queue|Queue]]
> - [[01 Queue/Discovery/Sources|Sources]]
> - [[02 Videos/Videos|Videos]]
> - [[03 Blogs/Blogs|Blogs]]
> - [[04 Approvals/Approvals|Approvals]]
> - [[05 Evaluations/Evaluations|Evaluations]]
> - [[00 Home/Settings|Settings]]

## Start with a video

Paste a YouTube link below. If rights are not already set in [[00 Home/Settings|Settings]], say whether the video is **own** or **third-party**.

```agent
type: chat
id: yt2b-home
persist: true
height: 320px
```

> [!agent-command] Quick actions
> Use these when you want the next step without writing a prompt.
>
> ```agent
> type: button
> text: "Check setup"
> prompt: "Use the youtube-to-blog skill. Run python3 skills/youtube-to-blog/scripts/doctor.py --vault . and report a short plain-language table of what is ready, what is optional and what needs attention. Change nothing, install nothing and never print secret values."
> viewType: right-pane
> autoSend: true
> ```
>
> ```agent
> type: button
> text: "Set up my voice"
> prompt: "Use the youtube-to-blog skill and run setup. Run doctor first if it has not run in this session, then interview me one question at a time using skills/youtube-to-blog/references/setup-interview.md. Write BRAND.md, VOICE.md and 06 AI Team/03 Knowledge/04 Voice/Author Profile.md, then run python3 skills/youtube-to-blog/scripts/alembic_sync.py --vault . and report what changed."
> viewType: right-pane
> autoSend: true
> ```
>
> ```agent
> type: button
> text: "Analyze queued videos"
> prompt: "Use the youtube-to-blog skill. Run doctor once, import the Home Inbox if present, then process each queued video through fetch, analyze, segments and brief in the required order. Stop after each brief and report the run folder. Ask only when rights are unset and Settings says ask. Never publish, commit or push."
> viewType: right-pane
> autoSend: true
> ```
>
> ```agent
> type: button
> text: "Plan articles"
> prompt: "Use the youtube-to-blog skill. For every briefed run, dispatch the yt2b-strategist using skills/youtube-to-blog/references/strategy-template.md, write strategy.md, create the strategy approval note, then stop and show me the decision that needs approval."
> viewType: right-pane
> autoSend: true
> ```
>
> ```agent
> type: button
> text: "Write approved articles"
> prompt: "Use the youtube-to-blog skill. Continue every approved strategy through the required outline approval, research, writing, SEO, rendering, review, repair, delivery and evaluation stages. Respect every approval gate and Settings default. Never publish, commit or push. End with links to the article, evaluation and publish kit."
> viewType: right-pane
> autoSend: true
> ```
>
> ```agent
> type: button
> text: "Run until approval"
> prompt: "Use the youtube-to-blog skill. Run doctor once, run setup if BRAND.md or VOICE.md is missing, import the Inbox, then process queued videos through fetch, analyze, segments, brief and strategy in order. Create the strategy approval note and stop there. Continue already-approved strategies through delivery and evaluation. Never publish, commit or push."
> viewType: right-pane
> autoSend: true
> ```

## What needs you

### Queue

![[00 Home/Pipeline.base#Home queue]]

### Approvals

![[00 Home/Reviews.base#Home approvals]]

## Recent work

### Articles

![[00 Home/Pipeline.base#Home blogs]]

### Quality checks

![[00 Home/Reviews.base#Home evaluations]]

## Discover

Follow feeds and YouTube channels with **Feeds** and **Discover** in the app navigation. Saved items keep their source trail and can be promoted to the queue when you are ready.

![[01 Queue/Discovery/Sources.base#Home sources]]

## Help

> [!info]- How it works
> 1. **Check** confirms the local tools and reports keys by name only.
> 2. **Queue** records the video, rights and writing mode.
> 3. **Analyze** builds the transcript, scenes, frames and content brief.
> 4. **Plan** proposes article angles and pauses for your strategy approval.
> 5. **Write** researches, outlines, drafts, reviews, repairs and evaluates the approved article.
> 6. **Finish** happens in Writing Studio. Publishing always stays a human action.
>
> See the [[06 AI Team/03 Knowledge/System Manual|System Manual]] for the complete workflow.

> [!info]- Rights and attribution
> Set each video to **own** or **third-party**. Own videos can use first person and more frames. Third-party videos use visible creator attribution, timestamped frames, tighter quote and frame limits, and a generated hero. The publisher keeps responsibility for the final fair-use decision. Change the default in [[00 Home/Settings|Settings]].

> [!info]- Cost and keys
> Claude uses the signed-in CLI. Gemini video analysis needs `GOOGLE_API_KEY` in the video analyzer configuration. Whisper fallback can use `GROQ_API_KEY` or `OPENAI_API_KEY`. Optional paid images use Banana Claude and its own approval. Keys stay outside this vault and are never displayed here. Check current provider pricing and quota before a live paid run.

> [!info]- Where things are saved
> Queue items live in [[01 Queue/Queue|Queue]], source runs in [[02 Videos/Videos|Videos]], finished drafts in [[03 Blogs/Blogs|Blogs]], decisions in [[04 Approvals/Approvals|Approvals]], and scorecards in [[05 Evaluations/Evaluations|Evaluations]]. Team knowledge, session notes and SOPs live in `06 AI Team`.
