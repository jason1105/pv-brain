# Providers & API Keys

Content quality comes from two pluggable seams: the LLM (script, titles,
metadata) and the TTS (narration). Keys go in **environment variables
only** — never in TOML files, never in the repo.

## LLM providers

| `[providers] llm` | Env var | Notes |
|-------------------|---------|-------|
| `anthropic` | `ANTHROPIC_API_KEY` | `llm_model` e.g. `claude-sonnet-5` |
| `ark` | `ARK_API_KEY` | Volcengine 火山方舟 (Doubao/豆包). `llm_model` is your endpoint or model id. Non-default region/gateway: set `ARK_BASE_URL` |
| `gemini` | `GEMINI_API_KEY` | `llm_model` e.g. `gemini-2.5-flash` |
| `mock` | — | Deterministic template content. Only selectable via `--offline`; output is always a DRAFT |

Whichever key you have works — the pipeline is identical behind the seam.

## TTS providers

| `[providers] tts` | Needs | Notes |
|-------------------|-------|-------|
| `edge` | `pip install 'pvfactory[edge]'`, network | Microsoft neural voices, keyless. Set `tts_voice` (e.g. `en-US-GuyNeural`, `zh-CN-YunxiNeural`) |
| `tone` / `silence` | nothing | Offline placeholders for CI and drafts |

## Draft semantics (important)

A run is a **DRAFT** if *any* content provider is offline/mock — even a
real-LLM + tone-audio run. Drafts are unmistakable on purpose: `DRAFT-`
directory prefix, watermark on every frame and the thumbnail,
`"draft": true` in the manifest and metadata. Only a run with a real LLM
**and** real TTS produces a clean, uploadable package.

## Cost & safety notes

- The LLM is called 3 times per video (brief, script, metadata) — a few
  thousand tokens per run.
- Keys are sent in request headers only; they never appear in URLs, logs,
  manifests, or packages.
- `pvfactory doctor` shows which keys the current shell has configured.
