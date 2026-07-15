# Quality: Testing, CI, Performance, Security

## Environment baseline (verified in sandbox)

- Python 3.11+, pip-only installs.
- No system ffmpeg, no espeak, no ffprobe. `imageio-ffmpeg` ships a static
  ffmpeg 7.0.2 binary **inside the wheel** (no runtime download) with
  libx264 + AAC; PNG+WAV → mp4 mux verified offline.
- Pin `imageio-ffmpeg` and `Pillow` versions in `pyproject.toml`; require an
  imageio-ffmpeg version whose wheel bundles the binary (older versions
  downloaded at runtime — a hidden CI network dependency).

## Testing strategy

The test pyramid, from the adversarial review's binding conclusions:

1. **Unit tests per step and per provider.** Steps are tested in isolation
   against artifact contracts.
2. **Invariant assertions, not string assertions.** Tests against MockLLM
   output assert schemas and invariants (segment count ≥ N, title length,
   non-empty narration, metadata fields present) — never exact strings.
   Exact-string tests test the mock, not the pipeline.
3. **Shared parse layer under test.** All LLM output flows through one
   parse-and-validate layer; Anthropic adapter gets fixture-based contract
   tests (canned API responses through the real parsing code).
4. **One e2e smoke test** producing a real, tiny, decode-verified mp4 with
   `--offline` deterministic providers (`tone` TTS so sync is audible in
   the decoded stream).
5. **Degenerate-input tests.** Empty script, zero segments, zero-duration
   audio must hard-fail at step boundaries — the pipeline must never
   "succeed" into a broken package.

### E2E budget (hard caps)

- Resolution ≤ 320×180, total audio ≤ 3 s, subprocess timeouts on every
  ffmpeg call, minimal ffmpeg invocations per suite (each costs ~3.5 s in
  startup). The suite must stay fast enough to run on every push without
  flaking under runner load.

### Verification without ffprobe

`ffmpeg -v error -i out.mp4 -f null -` decode check + stream/duration
parsing from stderr. "File exists and is > 0 bytes" is not verification.

## CI

- GitHub Actions: `ruff check` + `pytest` on push/PR.
- **Path-filtered:** docs-only changes do not trigger (or block on) Python
  CI — this repo is also a knowledge base and docs PRs must stay
  friction-free.
- No API keys in CI; the acceptance run (spec 01) is executed and documented
  manually when real providers are configured.

## Performance budgets

- Render architecture (spec 03) is the budget: one PNG per slide, one ffmpeg
  invocation via concat demuxer. PIL slide generation ~5 ms/frame; a
  5-minute video renders in seconds, not minutes.
- `produce` wall-clock (offline, default resolution): < 60 s per video.

## Security

- Secrets only via environment variables; never in config files, manifests,
  logs, or committed fixtures.
- Generated packages contain no secrets by construction (manifest records
  provider *names*, prompt hashes — not keys, not raw prompts with injected
  secrets).
- External content (LLM output) is data, not code: it is parsed against
  schemas, never eval'd, and filenames derive from slugified controlled
  fields only.

## Licensing notes

- Bundled static ffmpeg includes libx264 → the binary is GPL. Fine for
  internal/self-hosted use; revisit before ever *distributing* pvfactory
  binaries.
- DejaVu Sans is redistributable (bundled as the default font).
- Prompt templates derive from a public X thread, archived with citation in
  `docs/research/`.
