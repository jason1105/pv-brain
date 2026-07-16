# Adding a Provider

Providers are the seam the whole architecture is built to swap through
(ADR-0002, spec 03). Adding one should never touch `pipeline.py`.

## Adding an LLM adapter

1. Subclass `LLMProvider` (`llm.py`) in a new module (follow `llm_http.py`'s
   pattern: `name`, `_request()` returns `(url, headers, payload)`, `_lift()`
   extracts the text from the response envelope). Put NO content-parsing
   logic here — that's the shared layer's job (`llm.call_llm`).
2. Validate required config (API key, model) **at construction**, not on
   first call — failures must surface at step 0, not mid-pipeline
   (`_HttpLLM.__init__` in `llm_http.py` does this via `ENV_KEY` +
   `_require_env`).
3. Accept an injectable `transport` parameter so tests never hit the
   network (see `_urllib_transport` and every adapter's `__init__`).
4. Register it in `runs.py`:
   ```python
   LLM_FACTORIES: dict[str, Callable[[ChannelProfile], object]] = {
       ...,
       "yourprovider": lambda p: YourLLM(str(p.providers.get("llm_model", ""))),
   }
   ```
5. Write a **contract test** in `tests/test_llm_http.py`: a canned
   real-shaped response driven through `llm.call_llm` (see the
   `@pytest.mark.parametrize` block covering all three adapters). This is
   the binding testing contract (spec 05) — it must exercise the exact
   production parsing path, no network, no key.
6. Update `docs/manual/04-providers.md` and `docs/specs/03-providers.md`.

## Adding a TTS adapter

1. Subclass `TTSProvider` (`tts.py`): `synthesize(segments, seed) ->
   list[SegmentAudio]`.
2. **Binding contract**: return one clip **per segment** with a **measured**
   duration (`tts.wav_duration`, never estimated) — the renderer times
   slides from these values, not from words-per-minute. See `tts_edge.py`
   for the real-audio pattern (any format → WAV via `render.ffmpeg_exe()`).
3. If the adapter needs an optional dependency, import it lazily inside
   `__init__` and raise `ConfigError` with an install hint on `ImportError`
   (see `EdgeTTS.__init__`) — the base install must stay dependency-light.
4. Register it in `runs.py`'s `TTS_FACTORIES` dict.
5. Decide draft status: if your provider can produce non-draft output, it
   must **not** be added to `tts.OFFLINE_TTS` (that set drives both the
   `--offline` provider choice and the "is this run a draft" check in
   `resolve_providers`).
6. Tests: reuse the parametrized shape in `tests/test_tts.py` (measured
   duration equals `wav_duration`, non-empty narration required, distinct
   durations across segments).

## Rules that apply to both

- **No parsing/validation logic in the adapter.** LLM output always flows
  through `llm.call_llm`; audio always reports measured, not estimated,
  duration. This is what keeps the offline/real paths behaviorally
  identical to the pipeline.
- **Fail at construction/step-0, not mid-run.** Config problems are
  `ConfigError` (exit 2); provider-side failures during a call are
  `StepError` (exit 1, resumable).
- **Never log or embed secrets.** Keys travel in HTTP headers only — see
  the `assert "test-key" not in captured["url"]` pattern in the contract
  tests and copy it for new adapters.
