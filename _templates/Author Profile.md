---
type: yt2b-knowledge
title: Author Profile
kind: voice
name: "{{author_name}}"
url: "{{author_url}}"
job_title: "{{author_job_title}}"
same_as:
  - "{{author_same_as_1}}"
  - "{{author_same_as_2}}"
expertise:
  - "{{author_expertise_1}}"
  - "{{author_expertise_2}}"
  - "{{author_expertise_3}}"
disclosure: "{{author_disclosure}}"
bio_short: "{{author_bio_short}}"
created: "{{date}}"
updated: "{{date}}"
tags:
  - yt2b
  - voice
---
# {{author_name}}

The properties above are the machine-read part: `name`, `url`, `job_title` and `same_as` become the Person node in every post's JSON-LD graph, `expertise` and `bio_short` feed the author block, `disclosure` is printed where the article needs it. Keep `name` identical to `author` in [[00 Home/Settings]].

## Bio
{{author_bio}}

Two or three sentences in the E-E-A-T shape: name and role with years in the field, one credential or notable work relevant to the topics, one line on what the author writes about. No adjectives about passion.

## Credentials
- **Role**: {{author_job_title}}
- **Years of experience**: {{author_years}}
- **Notable work**: {{author_notable_work}}
- **Author page**: {{author_url}}

## Experience the writer may claim
{{author_experience_claims}}

Only first-hand claims the author can back with a method, a measurement, a screenshot or a record. Anything else is written as sourced analysis, not experience.

## Expertise limits
{{author_expertise_limits}}

Topics where the author writes as a well-read reporter rather than a practitioner. The writer keeps first person out of these.

## Where this is used
- `author` in [[00 Home/Settings]] copies `name`; `site_url` there is the site, `url` here is the author page.
- `finalize_html.py` builds the Person node from `name`, `url`, `job_title` and `same_as`.
- The writer packet (`references/writer-packet.md`) uses `bio_short` and the bio above for the author block at the end of every post.
- Root `BRAND.md` mirrors the same profile links under sameAs; root `VOICE.md` carries the voice, not the credentials.
