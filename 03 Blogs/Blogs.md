---
type: yt2b-app-page
title: Blogs
created: 2026-09-03
updated: 2026-09-03
cssclasses:
  - yt2b-dashboard
  - yt2b-app-page
tags:
  - yt2b
  - dashboard
  - workflow/blog
---

# Blogs

Drafts and delivered articles created from approved video strategies.

> [!yt2b-nav] Workspace
> - [[00 Home/Home|Home]]
> - [[01 Queue/Queue|Queue]]
> - [[01 Queue/Discovery/Sources|Sources]]
> - [[02 Videos/Videos|Videos]]
> - [[04 Approvals/Approvals|Approvals]]
> - [[05 Evaluations/Evaluations|Evaluations]]

> [!agent-command] Article actions
> Build approved work, then use Writing Studio in the sidebar for the human edit and publish step.
>
> ```agent
> type: button
> text: "Write approved articles"
> prompt: "Use the youtube-to-blog skill. Continue every approved strategy through outline approval, research, writing, SEO, rendering, review, repair, delivery and evaluation. Respect every approval gate. Never publish, commit or push. End with links to the article, evaluation and publish kit."
> viewType: right-pane
> autoSend: true
> ```

## All articles

![[00 Home/Pipeline.base#Blogs]]

Only articles inside `03 Blogs` appear here. Test fixtures and templates are excluded from this view.
