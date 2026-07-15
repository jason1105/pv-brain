# Changelog

Notable changes to the pv-brain knowledge base. This file tracks the
evolution of the documentation, not application releases.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

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
