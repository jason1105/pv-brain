# Testing Guide

66 tests, ~1.3s wall-clock, zero network, zero API keys, zero cost
(spec 05). Run them:

```bash
pip install -e ".[dev]"
ruff check src tests
pytest
```

## The test pyramid

1. **Unit tests per step/provider** — most files (`test_artifacts.py`,
   `test_tts.py`, `test_visuals.py`, `test_render.py`, `test_profile.py`,
   `test_engine.py`).
2. **Invariant assertions, not string assertions**, against `MockLLM`
   output (`test_llm.py`): assert segment count, non-empty narration,
   title length — never exact strings. Exact-string tests test the mock,
   not the pipeline, and break the moment the mock's phrasing changes.
3. **Contract tests for real adapters** (`test_llm_http.py`): canned,
   real-shaped API responses driven through the *actual* production
   parsing code via an injected transport. This is how the untested
   surface of a real provider shrinks to "the HTTP call itself."
4. **One capped end-to-end smoke test** (`test_pipeline_e2e.py`): a full
   offline `produce_video()` run producing a real, tiny, decode-verified
   mp4. Budget: 320×180, fast pacing (`conftest.py`'s `tiny_profile`
   fixture) — keep it that way; ffmpeg startup costs ~3.5s regardless of
   content size, so don't add a second full e2e test, extend assertions
   on the existing one.
5. **Regression tests for review findings**
   (`test_review_regressions.py`): one test per confirmed bug from the
   pre-merge adversarial code reviews (see PRs #14, #16). Add to this file
   when a `/code-review` finding gets fixed.

## Rules

- **Never touch the network or require an API key.** If you're testing an
  HTTP adapter, inject a fake transport (see `_transport()` helper in
  `test_llm_http.py`) — do not `monkeypatch` around `urllib` internals.
- **Assert invariants for anything backed by a non-deterministic or
  swappable provider.** If a test would break when `MockLLM`'s phrasing
  changes, it's testing the wrong thing.
- **Keep the e2e test capped.** Check `conftest.tiny_profile`
  (320×180, `tts_wpm=6000`) before writing anything that renders a real
  video — reuse it.
- **`ruff check` must pass** before a PR (line length 100, import order,
  the `select` rules in `pyproject.toml`). CI enforces this; run it
  locally first.

## Fixtures

`tests/conftest.py` defines `tiny_profile` — the one shared e2e-safe
channel profile. Add new shared fixtures there, not duplicated per test
file.
