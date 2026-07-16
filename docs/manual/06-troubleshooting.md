# Troubleshooting

Run `pvfactory doctor` first — it catches most environment problems.
Exit code `2` = configuration problem (fix input and retry); `1` = a
pipeline step failed (use `inspect`, fix, `resume`).

| Symptom | Cause | Fix |
|---------|-------|-----|
| `provider 'anthropic' needs the ANTHROPIC_API_KEY environment variable` | No key in this shell | `export ANTHROPIC_API_KEY=…` (or switch `[providers] llm`, or `--offline`) |
| `set [providers] llm to one of ['anthropic','ark','gemini']` | Profile has no real LLM configured and you ran without `--offline` | Add `[providers] llm`/`llm_model`, or run `--offline` |
| `the 'edge' TTS provider needs the edge-tts package` | Optional extra not installed | `pip install 'pvfactory[edge]'` |
| `the configured font cannot render language 'zh'` | Bundled font has no CJK glyphs | Set `[render] font_path` to a covering font (e.g. Noto Sans CJK) |
| `[render] resolution must have even width and height` | Odd dimensions | Use even numbers (H.264/yuv420p constraint) |
| `[channel] id must be a slug` | id contains `/`, spaces, uppercase… | Lowercase letters, digits, `-`, `_` only |
| `unknown key(s) in [section]` | Typo in the profile | Check spelling against the profile reference |
| `rendered file fails decode check` | Corrupt render (rare) | Re-run; if persistent, `pip install --force-reinstall imageio-ffmpeg` |
| `HTTP 401/403 from …` | Wrong/expired API key | Rotate the key; for `ark`, also verify `ARK_BASE_URL` region |
| `HTTP 404` from ark | `llm_model` is not your endpoint id | Use the endpoint/model id from the Volcengine console |
| `cannot reach …` | No network / proxy blocks the API | Check connectivity; offline work still runs with `--offline` |
| Run interrupted (Ctrl-C, crash) | — | `pvfactory resume --run <id>` continues from the last completed step |
| Output is watermarked DRAFT unexpectedly | An offline content provider was used (`--offline`, or `tts = "tone"/"silence"`) | Configure a real LLM **and** `tts = "edge"`, run without `--offline` |

Still stuck? `pvfactory inspect --run <id>` shows exactly which step failed
and the error recorded in the manifest.
