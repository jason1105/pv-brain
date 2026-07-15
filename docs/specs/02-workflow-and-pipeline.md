# Workflow Model and Pipeline

## Workflow model

Per ADR-0002, the workflow — not the agent, model, or script — is the core
abstraction. The engine therefore treats a workflow as **data, not implicit
call order**:

- A workflow is a declared, ordered sequence of **steps**.
- Each step declares **typed, named inputs and outputs** (artifact
  contracts).
- The engine validates the contract graph when the workflow is assembled:
  every input must be produced by an earlier step or supplied at start.
  A wiring mistake fails at assembly, not at step 7 of 9.
- The engine hosts **N workflows**; `produce-video` is workflow #1. The
  business-level definition lives in
  [`../workflow/produce-video.md`](../workflow/produce-video.md) and the
  code references it by name — the repo's Workflow layer and the runtime
  stay one system.

## Run lifecycle

- Every run has a stable `run_id` and a `channel_id`.
- **Step boundaries are checkpoint boundaries.** After each step, the run
  state and manifest are persisted. A crashed or failed run resumes
  idempotently: completed steps are skipped, the failed step re-executes.
- Step status is an enum: `pending | running | done | failed |
  awaiting_approval`. `awaiting_approval` exists from day one so a human
  review gate before publish is a status value, not a redesign.
- The engine is a **library with a pure-function entry point**
  (profile + topic + config → video package). No step may require a TTY or
  interactive input. The CLI is a thin shell over this function (ADR-0004).

## Pipeline steps (`produce-video`)

| # | Step | Consumes | Produces | Providers used |
|---|------|----------|----------|----------------|
| 1 | `ideate` | profile, topic | `brief` | LLM |
| 2 | `write_script` | brief | `script` (segmented) | LLM |
| 3 | `synthesize_voice` | script | `voice_track` (per-segment audio + measured timings) | TTS |
| 4 | `plan_visuals` | script, voice_track | `timeline` (EDL) | Visuals |
| 5 | `render_video` | timeline, voice_track | `video` | Renderer |
| 6 | `make_captions` | script, voice_track | `captions` (.srt) | — (derived) |
| 7 | `make_thumbnail` | brief, script | `thumbnail` | LLM (concept) + Visuals (raster) |
| 8 | `package_metadata` | brief, script, voice_track | `metadata` | LLM |
| 9 | `publish` | video, thumbnail, captions, metadata | `publish_result` | Publisher |

Steps map to the prompt templates in `docs/prompts/youtube/`:
`ideate`/`write_script` → production templates; `make_thumbnail`,
`package_metadata` → packaging templates.

### Step rules

- **Validation at every boundary.** Degenerate artifacts are hard errors
  before the next step runs: empty script, zero segments, zero-duration
  audio, empty rendered file. The pipeline must never "succeed" into a
  broken package.
- **Publish is an ordinary step** producing a `publish_result` artifact
  (platform, video URL/ID, timestamps — the join key for a future analytics
  loop), not a terminal side effect.

## Data model

### Script (canonical: `script.json`)

The script is **structured segments**, not prose. `script.md` is derived for
humans.

```json
{
  "schema_version": 1,
  "topic": "...",
  "title_working": "...",
  "segments": [
    {
      "id": "seg-001",
      "role": "hook | body | re_engage | cta",
      "heading": "...",
      "narration": "...",
      "visual_intent": "short description of what should be on screen"
    }
  ]
}
```

### Voice track

The TTS contract returns **one audio clip per segment with measured
duration**. Assembly timing comes from these measurements only —
words-per-minute estimation never leaves the inside of the offline TTS
provider (adversarial-review binding conclusion: anything else fossilizes
wrong timing assumptions in the renderer).

### Timeline (EDL)

The renderer consumes a **timeline**: an ordered list of entries pairing one
visual asset with one audio span.

```json
{
  "schema_version": 1,
  "entries": [
    {
      "segment_id": "seg-001",
      "visual": {"kind": "slide", "asset": "artifact://slides/seg-001.png"},
      "audio": {"asset": "artifact://voice/seg-001.wav", "duration_s": 12.84}
    }
  ]
}
```

`kind` admits future values (`clip`, `image`, `generated`) so stock footage
and generative visuals extend the timeline without changing the renderer
interface.

### Artifact store

Artifacts are addressed by **URI-like references** (`artifact://…`), never
raw filesystem paths, through an `ArtifactStore` interface. The MVP
implementation is a local run directory; nothing outside it may know that.
This is the seam that lets the cloud runtime swap in object storage
(ADR-0001, ADR-0004).

### Manifest (`manifest.json`)

The manifest is a **versioned provenance record**, not a file listing:

```json
{
  "schema_version": 1,
  "run_id": "...", "channel_id": "...",
  "workflow": "produce-video",
  "draft": false,
  "steps": [
    {
      "name": "write_script",
      "status": "done",
      "provider": "anthropic", "model": "...",
      "prompt_ref": "prompts/youtube/production.md#high-retention-script",
      "prompt_hash": "sha256:...", "seed": 42,
      "started_at": "...", "duration_s": 3.1,
      "outputs": {"script": "artifact://script.json"}
    }
  ],
  "artifacts": {"video": {"ref": "artifact://video.mp4", "sha256": "..."}}
}
```

Provider identity, model, prompt hash, seed, timing, and per-artifact
checksums make every run reproducible and every bad artifact traceable to
the step that produced it — the precondition for the analytics loop the
company ultimately optimizes with.

## Channel state

A `ChannelStore` interface (topic history, published videos) exists as a
stub from day one — the scheduler milestone makes "don't repeat the last 30
topics" mandatory, and a stateless design has nowhere to put it. MVP ships a
local JSON implementation with topic history only.
