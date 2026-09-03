---
type: yt2b-app-page
title: Queue
created: 2026-09-03
updated: 2026-09-03
cssclasses:
  - yt2b-dashboard
  - yt2b-app-page
tags:
  - yt2b
  - dashboard
  - workflow/queue
---

# Queue

Videos waiting to be analyzed, planned or completed. Use the red play dashboard for the fastest single-video intake.

> [!yt2b-nav] Workspace
> - [[00 Home/Home|Home]]
> - [[01 Queue/Discovery/Sources|Sources]]
> - [[02 Videos/Videos|Videos]]
> - [[03 Blogs/Blogs|Blogs]]
> - [[04 Approvals/Approvals|Approvals]]
> - [[05 Evaluations/Evaluations|Evaluations]]

> [!agent-command] Queue actions
> Start the queued work or get a simple status report.
>
> ```agent
> type: button
> text: "Analyze the queue"
> prompt: "Use the youtube-to-blog skill. Run doctor once, then process queued videos through fetch, analyze, segments and brief in the required order. Stop after each brief and report the run folder. Ask only when rights are unset and Settings says ask. Never publish, commit or push."
> viewType: right-pane
> autoSend: true
> ```
>
> ```agent
> type: button
> text: "Show queue status"
> prompt: "Use the youtube-to-blog skill. Run python3 skills/youtube-to-blog/scripts/queue.py --vault . list and summarize the queue in a short plain-language table. Change nothing."
> viewType: right-pane
> autoSend: true
> ```

## All queued videos

![[00 Home/Pipeline.base#Queue]]

Rights and writing mode come from the item or [[00 Home/Settings|Settings]]. A saved discovery item keeps its origin when promoted from [[01 Queue/Discovery/Sources|Sources]].
