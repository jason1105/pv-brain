# Workflow: produce-video

The per-video production workflow — the first executable workflow of the
Autonomous Content Company. Business definition; the runtime implements it
by this name (see [`../specs/02-workflow-and-pipeline.md`](../specs/02-workflow-and-pipeline.md)).

## Intent

Turn one topic into one upload-ready video package for one channel, with no
human production work. Humans supervise at two points: choosing what goes
into the backlog, and approving the package before publish.

## Trigger

- Now: an operator runs `pvfactory produce` with a topic or backlog.
- Later: the always-on runtime pulls the next backlog item on schedule.

## Steps (business view)

| Step | Business meaning | Prompt template |
|------|------------------|-----------------|
| Ideate | Decide the angle: who is this for, why will they click, why will they stay | [`production.md`](../prompts/youtube/production.md) — Faceless Video Concept |
| Write script | Segmented, retention-engineered narration | [`production.md`](../prompts/youtube/production.md) — High-Retention Script |
| Synthesize voice | Narration audio, timed per segment | — |
| Plan visuals | One visual per segment, synced to measured narration | — |
| Render video | Assemble timeline into the final video | — |
| Make captions | Accessibility + retention (most viewers start muted) | — |
| Make thumbnail | The single highest-leverage packaging asset | [`packaging.md`](../prompts/youtube/packaging.md) — Thumbnail Concepts |
| Package metadata | Title, description with chapters, tags — paste-ready | [`packaging.md`](../prompts/youtube/packaging.md) — Viral Title Generator |
| Publish | Deliver: today a checklist, later the upload itself | — |

## Human gates

- **Before**: the backlog is human-curated (strategy stays with people;
  see non-goals in the spec).
- **After**: `publish` supports `awaiting_approval` — the workflow can hold
  the finished package for sign-off before anything goes public.

## Out of scope

Channel strategy (niche, calendar, monetization planning) is a separate
future workflow; its prompt templates already exist in
[`../prompts/youtube/`](../prompts/youtube/).
