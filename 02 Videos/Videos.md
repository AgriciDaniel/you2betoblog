---
type: yt2b-app-page
title: Videos
created: 2026-09-03
updated: 2026-09-03
cssclasses:
  - yt2b-dashboard
  - yt2b-app-page
tags:
  - yt2b
  - dashboard
  - workflow/video
---

# Videos

Every source run, from first fetch through brief and strategy.

> [!yt2b-nav] Workspace
> - [[00 Home/Home|Home]]
> - [[01 Queue/Queue|Queue]]
> - [[01 Queue/Discovery/Sources|Sources]]
> - [[03 Blogs/Blogs|Blogs]]
> - [[04 Approvals/Approvals|Approvals]]
> - [[05 Evaluations/Evaluations|Evaluations]]

> [!agent-command] Video actions
> Continue analyzed work to the next human decision.
>
> ```agent
> type: button
> text: "Plan briefed videos"
> prompt: "Use the youtube-to-blog skill. For each run in 02 Videos with status briefed, create strategy.md with the yt2b-strategist, open the strategy approval note, then stop and show me what needs a decision."
> viewType: right-pane
> autoSend: true
> ```

## All video runs

![[00 Home/Pipeline.base#Videos]]

Open a run to see its video, transcript, frames, brief, strategy, linked queue item and stage log.
