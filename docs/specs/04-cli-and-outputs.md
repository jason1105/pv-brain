# CLI, Channel Profile, and Outputs

## CLI

The CLI is a thin, **headless** shell over the engine's pure-function entry
point (ADR-0004): no interactive prompts, no TTY dependence, all inputs via
files/flags/env, machine-readable results.

```
pvfactory produce --profile channels/tech.toml --topic "Why SSDs die"
pvfactory produce --profile channels/tech.toml --backlog topics.txt
pvfactory produce --profile channels/tech.toml --topic "..." --offline
pvfactory resume  --run <run_id>
pvfactory inspect --run <run_id>
pvfactory doctor
```

| Command | Behavior |
|---------|----------|
| `produce` | Run the `produce-video` workflow. `--backlog FILE` (one topic per line) produces N packages sequentially. `--offline` selects deterministic draft providers (ADR-0005). `--seed N` for reproducible offline runs. |
| `resume` | Resume a failed/interrupted run from its last completed step. |
| `inspect` | Print a run's manifest summary: step statuses, providers, artifacts. |
| `doctor` | Verify the environment: ffmpeg present and functional, fonts loadable, which providers are available, which env keys are set. |

Exit codes: `0` success, `1` pipeline step failure (manifest records which),
`2` configuration/environment error. Progress goes to stderr; the final line
on stdout is the package path (scriptable).

## Channel profile (TOML)

```toml
schema_version = 1

[channel]
id = "tech-explains"            # stable channel_id
name = "Tech Explains"
niche = "consumer tech explainers"
audience = "curious non-experts, 18-40"
language = "en"                  # BCP-47; drives glyph-coverage validation

[content]
tone = "curious, punchy, no hype"
video_minutes_target = 5
style = "dark"                   # slide style preset: dark | light | bold

[render]
resolution = "1920x1080"
# font_path = "/path/to/NotoSansCJK.otf"  # required for CJK languages

[providers]                       # router table: step -> provider/model
llm = "anthropic"
llm_model = "claude-sonnet-5"
tts = "edge"
tts_voice = "en-US-GuyNeural"
```

Unknown keys are rejected (typo protection). `schema_version` gates future
migration.

## Output: the video package

One directory per run: `<output_root>/<channel_id>/<date>-<slug>/`
(prefixed `DRAFT-` for draft runs).

| File | Contents |
|------|----------|
| `manifest.json` | Versioned provenance record (spec 02) |
| `brief.json` | Ideation output: angle, audience intent, working title |
| `script.json` / `script.md` | Canonical segmented script / human-readable view |
| `voice/seg-*.wav` + `voiceover.wav` | Per-segment audio + concatenated track |
| `timeline.json` | The EDL the renderer consumed |
| `video.mp4` | Decode-verified render (H.264/AAC, yuv420p) |
| `captions.srt` | Captions from segments + measured timings |
| `thumbnail.png` | 1280×720, profile-driven colors, ≤5 words, legible at 10% size |
| `metadata.json` | Operator-complete: final title, description **with chapter timestamps** (derived from segment timings), tags, category, visibility |
| `PUBLISH_CHECKLIST.md` | DryRunPublisher output: exact upload steps |

## Metadata is operator-complete

`metadata.json` exists to make manual upload near-zero-work: every field
paste-ready, chapters derived from real segment timings, description ending
with the channel's standard blocks (from profile). If a human has to write
anything, the step failed its job.
