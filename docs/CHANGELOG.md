# Changelog

Notable changes to the pv-brain knowledge base. This file tracks the
evolution of the documentation, not application releases.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [0.8.0] — 2026-07-16

### Added

- `manual/` — PV Factory user manual: installation & quickstart, channel
  profile reference, command reference, providers & API keys, the output
  package explained, troubleshooting.
- `development/` — PV Factory developer guide: codebase map, adding an
  LLM/TTS provider, adding a workflow step, testing guide, contribution
  process.

### Changed

- Root `README.md` and `docs/README.md` now route operators and
  contributors to the new manual/developer guide; corrected stale wording
  claiming real providers "arrive in milestone M3" (shipped in 0.7.0).

## [0.7.0] — 2026-07-15

### Added

- M3 real providers: `anthropic`, `ark` (Volcengine/Doubao), `gemini` LLM
  adapters (thin HTTP, shared parse layer, contract-tested with canned
  responses); `edge` TTS (optional extra `pvfactory[edge]`).
- Provider registry in `runs.py`; profile `[providers]` now drives real
  provider selection; manifest records the offline flag so `resume`
  reconstructs the original provider mode.
- `doctor` reports configured API keys and edge-tts availability.

## [0.6.0] — 2026-07-15

### Added

- PV Factory MVP milestones M0-M2 (`src/pvfactory/`, `tests/`): workflow
  engine with durable resumable runs, the 9-step produce-video pipeline,
  offline providers, ffmpeg renderer with decode verification, headless CLI
  (`produce`/`resume`/`inspect`/`doctor`), 39-test suite, path-filtered CI.

## [0.5.0] — 2026-07-15

### Added

- `plan/` — milestone-based implementation plan for PV Factory (M0
  scaffolding → M1 engine core → M2 offline pipeline → M3 real providers +
  acceptance run) with per-milestone exit gates and a risk register.

## [0.4.0] — 2026-07-15

### Added

- `specs/` — specification suite for PV Factory, the auto video generation
  software (overview, workflow & pipeline, providers, CLI & outputs,
  quality), finalized after a three-lens adversarial design review.
- `workflow/produce-video.md` — business definition of the first executable
  workflow.
- ADR-0003 (runtime in monorepo), ADR-0004 (CLI engine first),
  ADR-0005 (offline-first providers with draft labeling).

## [0.3.0] — 2026-07-15

### Added

- `research/2026-07-15-youtube-12-prompt-playbook.md` — external source
  material: the 12-prompt YouTube playbook, with pipeline mapping and
  assessment.
- `prompts/youtube/` — reusable, variable-normalized prompt templates
  grouped by pipeline stage.

## [0.2.0] — 2026-07-15

### Changed

- Consolidated all documentation under `docs/` to keep the repository root
  free for implementation code. Root `README.md` remains as the landing page.

### Added

- `docs/README.md` as the documentation index.

## [0.1.0] — 2026-07-05

### Added

- Initial knowledge base structure.
- Top-level `README.md`, `ROADMAP.md`, and this `CHANGELOG.md`.
- `vision/` with the product vision.
- `architecture/` with the high-level architecture overview.
- `adr/` with ADR-0001 (Cloud First Runtime) and ADR-0002 (Workflow First).
- `brainstorm/` with the first dated exploration note.
- Placeholder sections for `knowledge/`, `workflow/`, `agents/`,
  `prompts/`, `research/`, and `assets/`.
