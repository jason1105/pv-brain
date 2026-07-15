# YouTube Prompt Library

Reusable prompt templates for the YouTube content pipeline, distilled from
the [12-prompt playbook](../../research/2026-07-15-youtube-12-prompt-playbook.md)
and normalized for machine use.

## Conventions

- Variables use `{{snake_case}}` placeholders (e.g. `{{niche}}`, `{{topic}}`).
- Each template states its **purpose**, **inputs**, and **expected output**
  so a workflow step (or a person) can call it without extra context.
- Templates are inputs to the runtime's LLM steps; the source of truth for
  *when* each runs is the workflow, not this library.

## Templates by pipeline stage

| File | Stage | Templates |
|------|-------|-----------|
| [`niche-research.md`](niche-research.md) | Research | Niche discovery, competitor breakdown |
| [`channel-strategy.md`](channel-strategy.md) | Strategy | 90-day roadmap, first 10 videos, content calendar |
| [`production.md`](production.md) | Production | Video concept, high-retention script |
| [`packaging.md`](packaging.md) | Packaging | Viral titles, thumbnail concepts |
| [`distribution.md`](distribution.md) | Distribution | Algorithm checklist, Shorts engine |
| [`monetization.md`](monetization.md) | Monetization | Income blueprint |
