# Providers, Routing, and Configuration

## Provider seams

Five interfaces, each cutting along a real vendor/capability boundary:

| Interface | Capability | MVP implementations |
|-----------|-----------|---------------------|
| `LLMProvider` | Structured text generation | `mock` (deterministic, seeded), `anthropic`, `ark` (Volcengine/Doubao), `gemini` |
| `TTSProvider` | Narration synthesis | `silence` (CI), `tone` (CI, audible sync check), `edge` (real speech, network, no key) |
| `VisualProvider` | Visual assets for segments | `slides` (styled PIL text-slides) |
| `Renderer` | Timeline → video file | `ffmpeg` (bundled static binary) |
| `Publisher` | Deliver the package | `dryrun` (upload checklist) |

The registry is a **plain dict** — the interfaces are the extensibility
mechanism; a plugin system for a five-entry table would be ceremony.

## Provider contracts (binding)

### LLMProvider

- Input: prompt (rendered from a template in `docs/prompts/`), expected
  output schema.
- **One shared parse-and-validate layer** sits between every provider and
  the pipeline. Mock and Anthropic responses flow through the *same*
  schema-validation code, so CI exercises the exact parsing path production
  uses. The Anthropic adapter additionally gets fixture-based contract tests
  (canned API responses fed to the real parsing code); the untested surface
  shrinks to the HTTP call itself.
- Every call records provider, model, prompt hash, and seed into the
  manifest.

### TTSProvider

- Input: the segmented script. Output: **per-segment audio clips with
  measured durations** (`list[(segment_id, wav_bytes, duration_s)]`).
- Never a single estimated-length WAV. Downstream timing uses measured
  durations only.
- The offline providers deliberately emit **non-uniform** per-segment
  durations so downstream code cannot silently assume uniform or
  WPM-derived timing.
- `silence`: paced silence (WPM heuristic *internal* to this provider).
- `tone`: distinct sine pitch per segment (stdlib `wave` + `math`) — makes
  A/V sync audible and decode-verifiable in CI at zero dependency cost.
- `edge`: real speech via edge-tts (network, no API key). Default for
  non-offline runs.

### VisualProvider

- Input: script segments + visual intents. Output: one visual asset per
  segment, referenced in the timeline.
- `slides`: 2–3 style presets (colors, font scale, layout) keyed off the
  channel profile's `style` field, so two channels' videos don't look
  identical.
- **Fonts:** the package bundles DejaVu Sans (redistributable); system font
  paths are never relied on. At pipeline start, glyph coverage is validated
  against the profile's language — a `zh` profile without a configured
  CJK-capable `font_path` fails loudly at step 0, never renders tofu.

### Renderer

- Input: timeline + voice track. Output: decode-verified mp4
  (H.264/AAC, `yuv420p`).
- **Architecture is mandated:** one still image per timeline entry, fed to
  ffmpeg via the concat demuxer with per-entry durations, single ffmpeg
  invocation (`-tune stillimage`). Generating video frames in a Python loop
  at target fps is **prohibited** (a 10-minute video would push ~100 GB of
  raw frames through a pipe for still content).
- Output verification: `ffmpeg -v error -i out.mp4 -f null -` decode check +
  stream/duration parsing from ffmpeg stderr. `ffprobe` is **not available**
  in the bundled distribution; "file exists" is not verification.
- Captions: `.srt` sidecar generated from segments + measured timings
  (burn-in optional, only where the bundled ffmpeg supports it).

### Publisher

- `dryrun` writes `PUBLISH_CHECKLIST.md`: the exact file to upload, title
  and description to paste, tags, thumbnail to set, visibility — a concrete
  checklist, not prose. Returns a `publish_result` artifact.
- Real YouTube upload is a post-MVP provider behind the same interface.

## Model routing

`ModelRouter` is typed as a **policy function**:
`(step, requirements, context) → provider selection`.

The MVP implementation is a config table (per-step provider/model mapping in
the channel profile or global config). The function signature is the point:
quality/cost/latency routing and analytics-driven routing later become new
implementations, not interface changes.

## Configuration and secrets

- Channel profile: TOML (stdlib `tomllib`), human-editable. See
  [`04-cli-and-outputs.md`](04-cli-and-outputs.md).
- Global config: `pvfactory.toml` (provider defaults, router table, output
  root).
- Secrets **only** via environment variables (`ANTHROPIC_API_KEY`,
  `ARK_API_KEY`, `GEMINI_API_KEY`, …). Never in TOML, never in the manifest,
  never in logs - API keys travel in request headers, never in URLs.
- Real LLM adapters are thin HTTP (no vendor SDKs); the Ark base URL is
  overridable via `ARK_BASE_URL` for other regions/gateways.

## Draft policy (ADR-0005)

- Offline/mock content providers are **never selected silently**: they
  require `--offline` (or explicit config).
- Any run using them is a **draft**: `manifest.draft = true`, a visible
  `DRAFT` watermark on rendered slides, and a `DRAFT` prefix in the package
  directory name.
- The default (no `--offline`) resolution requires real content providers
  and fails with a clear message if they are unavailable — an honest error
  beats a silent skeleton.
