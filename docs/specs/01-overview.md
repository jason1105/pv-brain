# PV Factory — Product Overview

## Definition

PV Factory (`pvfactory`) is an automated **faceless-video production
pipeline**. Given a channel profile and a topic, it produces a complete,
upload-ready **video package**: rendered video, voiceover, captions,
thumbnail, and paste-ready publishing metadata — with no human doing the
production work between input and output.

It is the first executable workflow of the Autonomous Content Company: the
per-video **production** workflow, which runs 30+ times a month per channel
and is therefore where automation compounds fastest.

## Goals (MVP)

1. **End-to-end per-video pipeline.** One headless invocation:
   ideate → script → voiceover → visuals → assemble → thumbnail → metadata →
   publish (dry-run). Every stage produces an inspectable artifact.
2. **Real, publishable output.** The acceptance run (below) must produce an
   mp4 with audible narration, synced captions, a 1280×720 thumbnail, and
   operator-complete metadata that a human could upload without editing.
3. **Pluggable providers.** LLM, TTS, visuals, rendering, and publishing sit
   behind adapter interfaces. Offline deterministic providers make the whole
   pipeline runnable and testable with zero network and zero cost.
4. **Durable, resumable runs.** Run state persists at every step boundary;
   a failed run can be resumed without redoing completed steps.
5. **Batch operation.** A topic backlog file produces N video packages in
   one command.

## Non-goals (MVP)

- **Channel-level strategy automation** (niche research, content calendars,
  competitor analysis). The prompt templates in
  [`../prompts/youtube/`](../prompts/youtube/) already serve these
  conversationally; they run once per channel, not per video.
- **YouTube OAuth upload.** Publishing is dry-run: an upload-ready package
  with a concrete checklist. Real upload is a later milestone (quota,
  verification review, and token management are a tarpit).
- **Stock footage, generative imagery, Ken Burns effects.** The MVP renderer
  is styled text-slides; the renderer *contract* (timeline/EDL) is designed
  so richer visual providers slot in without interface changes.
- **Analytics feedback loop.** The manifest records the provenance needed to
  build it later; the loop itself is out of scope.
- **A long-running service/scheduler.** See ADR-0004: the engine is a
  library invoked by a thin CLI now, and by a service later.

## Acceptance criteria

The MVP's definition of done is **not** the CI smoke test. It is a
documented **acceptance run**:

> With a real LLM provider (API key) and a real TTS provider configured, one
> command on a real channel profile produces a video package that a human
> could upload to YouTube unedited: audible narration, readable styled
> slides, captions in sync, thumbnail legible at small size, metadata
> paste-ready.

Additionally:

- The same pipeline runs fully offline (`--offline`) with deterministic
  providers, and CI proves it on every push with a decode-verified mp4.
- Draft output is unmistakable: offline/mock content is watermarked and
  stamped in the manifest (see ADR-0005). A draft can never be mistaken for
  a deliverable.

## Users

- **Primary (now):** a channel operator running the CLI to batch-produce
  faceless videos for one or more channels.
- **Primary (later):** the always-on cloud runtime invoking the same engine
  on a schedule, with a human approving before publish.

## Glossary

| Term | Meaning |
|------|---------|
| **Channel profile** | TOML file describing one channel: niche, audience, language, tone, style, pacing. |
| **Video package** | The per-run output directory: video, voiceover, captions, thumbnail, metadata, script, brief, manifest. |
| **Workflow** | An ordered, declared set of steps with typed artifact contracts (ADR-0002). The engine can host multiple workflows; `produce-video` is the first. |
| **Step** | One unit of the workflow: consumes named artifacts, calls providers, produces named artifacts. |
| **Artifact** | A named, typed output persisted through the ArtifactStore and recorded in the manifest. |
| **Provider** | A pluggable implementation of one capability seam (LLM, TTS, visuals, renderer, publisher). |
| **Segment** | The atomic unit of narration: one script section with its text, measured audio, and timing. Visuals sync to segments. |
| **Manifest** | The versioned provenance record of a run (`manifest.json`). |
| **Draft** | Any output produced with mock/offline content providers; watermarked and stamped as such. |
