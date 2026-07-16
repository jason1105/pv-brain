# Codebase Map

`src/pvfactory/` (~2200 lines). Grouped by layer, roughly bottom-up.

## Foundation

| Module | Purpose |
|--------|---------|
| `errors.py` | `PvError` taxonomy: `ConfigError` (exit 2), `ValidationError`/`StepError` (exit 1) |
| `artifacts.py` | `ArtifactStore` — `artifact://` refs over a backing store. `LocalArtifactStore` is the only implementation; `path_for()` is the documented escape hatch for handing files to subprocesses (ffmpeg) |
| `manifest.py` | `Manifest`/`StepRecord` — the versioned provenance record, persisted at every step boundary. Status enum incl. `awaiting_approval` |
| `profile.py` | `ChannelProfile` + `load_profile()` — TOML parsing, schema validation, unknown-key rejection |

## Engine (workflow-as-data)

| Module | Purpose |
|--------|---------|
| `engine.py` | `Workflow` (declared steps + assembly-time contract validation), `Runner` (checkpointed, idempotent-resume execution), `RunContext` (what a step can touch) |
| `pipeline.py` | The concrete `produce-video` workflow: 9 `StepDef`s + their implementations (`ideate`, `write_script`, …) |
| `runs.py` | The engine's pure-function entry point: `produce_video()`, `resume_run()`, `find_run()`, and the **provider registries** (`LLM_FACTORIES`, `TTS_FACTORIES`) |

## Providers

| Module | Purpose |
|--------|---------|
| `llm.py` | `LLMProvider` ABC, the **shared parse/validate layer** (`call_llm`, `extract_json`, `validate_schema`) every LLM output flows through, and `MockLLM` |
| `llm_http.py` | Real LLM adapters: `AnthropicLLM`, `ArkLLM`, `GeminiLLM` — thin HTTP, injectable transport |
| `tts.py` | `TTSProvider` ABC, WAV helpers, offline providers `SilenceTTS`/`ToneTTS` |
| `tts_edge.py` | `EdgeTTS` — real speech, optional dependency |
| `visuals.py` | `SlidesVisualProvider` (slides + thumbnails), font loading, glyph-coverage validation, DRAFT watermark |
| `render.py` | `FfmpegRenderer` (concat-demuxer render + decode verification), `.srt` caption building |
| `publish.py` | `Publisher` ABC, `DryRunPublisher` |
| `prompts.py` | Prompt template construction (`brief_prompt`, `script_prompt`, `metadata_prompt`) — mirrors `docs/prompts/youtube/` |
| `channelstore.py` | `ChannelStore` — cross-run topic history, keyed by channel |

## Entry point

| Module | Purpose |
|--------|---------|
| `cli.py` | `produce`/`resume`/`inspect`/`doctor` — a thin shell over `runs.py`, no logic of its own |

## Data flow (one `produce` call)

```
cli.py
  -> runs.produce_video(profile_path, topic, output_root, offline, seed)
       -> profile.load_profile()          # parse + validate
       -> visuals.validate_glyph_coverage() # fail fast on font/language mismatch
       -> runs.resolve_providers()         # profile [providers] -> provider instances
       -> engine.Runner(pipeline.build_workflow(), ctx, manifest).run()
            for each StepDef:
              step.fn(ctx)                 # e.g. pipeline.ideate
                -> ctx.providers["llm"].complete(...)   # provider does I/O
                -> llm.call_llm(...)                    # shared parse/validate
                -> ctx.store.put_json(...)              # -> artifact:// ref
              manifest.finish_step(...)    # checkpoint: provenance + sha256
              manifest.save(ctx.store)     # persisted after EVERY step
```

Read `pipeline.py` top to bottom — it is the clearest single file for
understanding the whole system, since every step is <20 lines and the
`StepDef` list at the bottom shows the full artifact dependency graph.
