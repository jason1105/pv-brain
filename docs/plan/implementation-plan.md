# PV Factory — Implementation Plan

Milestones are sequential; each has an **exit gate** that must hold before
the next begins. M0–M2 are implementable and verifiable entirely offline
(this sandbox, CI). M3 needs real credentials for its acceptance run.

Process per change: GitHub issue → worktree branch → PR (path-filtered CI
green) → merge.

## M0 — Scaffolding

**Deliverables**

- `pyproject.toml` (src/ layout, `pvfactory` package, console script),
  pinned `Pillow` + `imageio-ffmpeg` (wheel-bundled binary version).
- Bundled DejaVu Sans font as package data.
- `ruff` + `pytest` config; GitHub Actions workflow **path-filtered to
  code paths** (`src/**`, `tests/**`, `pyproject.toml`, workflow file) so
  docs PRs stay friction-free.
- `pvfactory doctor` skeleton: verifies Python, ffmpeg binary, font
  loadable.

**Exit gate:** CI green on a trivial test; `pip install -e .` +
`pvfactory doctor` works in a clean environment.

## M1 — Engine core

**Deliverables**

- Workflow-as-data: step registry with typed named inputs/outputs; assembly
  validation of the artifact contract graph (spec 02).
- `RunContext` + durable run state: `run_id`, persistence at every step
  boundary, idempotent `resume`; status enum incl. `awaiting_approval`.
- `ArtifactStore` interface + local-directory implementation
  (`artifact://` refs).
- Manifest writer (versioned provenance record; spec 02 schema).
- `ChannelStore` stub with local JSON topic history.
- Channel profile loader: TOML, `schema_version`, unknown-key rejection,
  glyph-coverage validation hook.

**Exit gate:** unit tests prove: contract-graph validation catches a
mis-wired workflow at assembly; a run killed mid-way resumes without
re-executing completed steps; manifest records per-step provenance.

## M2 — Offline pipeline end to end

**Deliverables**

- Providers: `MockLLM` (seeded, deterministic) behind the **shared
  parse/validate layer**; `silence` + `tone` TTS (per-segment measured
  durations, deliberately non-uniform); `slides` visuals (style presets,
  bundled font, DRAFT watermark); `ffmpeg` renderer (concat demuxer, single
  invocation, decode verification); `dryrun` publisher (checklist).
- All 9 `produce-video` steps wired; captions (.srt) from measured timings;
  1280×720 thumbnail; operator-complete `metadata.json` with chapter
  timestamps.
- CLI: `produce` (incl. `--backlog`, `--offline`, `--seed`), `resume`,
  `inspect`, `doctor` complete.
- Draft policy enforced (ADR-0005): explicit `--offline`, `DRAFT-` package
  prefix, `manifest.draft`.
- Test suite per spec 05: step/provider unit tests (invariants, not
  strings), degenerate-input hard-failure tests, one capped e2e producing a
  decode-verified tiny mp4 with `tone` audio.

**Exit gate:** `pvfactory produce --offline --seed 42` yields a complete
draft package on a clean machine with no network; e2e decode check passes
in CI; suite wall-clock within budget.

## M3 — Real providers + acceptance run (MVP done)

**Deliverables**

- `anthropic` LLM adapter through the same parse/validate layer +
  fixture-based contract tests (canned API responses).
- `edge` TTS adapter (real speech, per-segment durations) + contract tests.
- Provider resolution per ADR-0005: real providers default, actionable
  error when unavailable.
- **The documented acceptance run** (spec 01): real profile, real LLM + TTS,
  output reviewed against the "uploadable unedited" bar; result recorded in
  `docs/research/` with the manifest.

**Exit gate:** acceptance-run write-up exists with an honest pass/fail per
criterion. This — not CI — is the MVP definition of done.

## Post-MVP outlook (not scheduled)

1. **Service milestone** (proves ADR-0004): scheduler + API wrapping the
   unchanged engine; `awaiting_approval` surfaced as a human review queue.
2. **YouTube upload provider** (OAuth, resumable upload, quota handling);
   `publish_result` feeds the ChannelStore.
3. **Richer visuals:** stock-footage provider (timeline `kind: "clip"`),
   generated imagery.
4. **Analytics loop:** ingest per-video performance keyed by
   `publish_result`, route back into ideation/routing (the Model Router's
   policy-function seam).
5. **Channel strategy workflow** (workflow #2) from the existing prompt
   templates.

## Sizing note

M0+M1 land together in one PR if small enough to review; M2 is the large
PR (reviewed before merge); M3 is a focused PR per provider. Every PR
updates `docs/CHANGELOG.md`.
