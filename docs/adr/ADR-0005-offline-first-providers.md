# ADR-0005 — Offline-First Providers with Explicit Draft Labeling

- **Status:** Accepted
- **Date:** 2026-07-15

## Context

The pipeline must be runnable and testable with zero network, zero API keys,
and zero cost (CI, development, this sandbox). But a run using mock content
providers produces template text and non-speech audio — an unpublishable
artifact. Adversarial review's product verdict: offline defaults are honest
engineering but a dishonest product if they are what a user gets silently.

## Decision

Every provider seam has a deterministic offline implementation, **and**
offline content providers are never selected silently:

- Offline runs require explicit `--offline` (or explicit config).
- Any such run is a **draft**: `manifest.draft = true`, a visible `DRAFT`
  watermark on rendered output, `DRAFT-` prefix on the package directory.
- The default path requires real content providers (LLM with key, real TTS)
  and fails with a clear, actionable error when they are unavailable.
- CI uses the offline providers; the MVP's definition of done is a
  documented acceptance run with real providers (spec 01).

## Consequences

- Deterministic tests and a fully offline development loop, with no risk of
  a draft being mistaken for a deliverable.
- Mock and real providers share one parse-and-validate layer, so CI green
  is meaningful for production parsing code.
- The first-run experience requires either credentials or an explicit
  `--offline` choice — an honest error beats a silent skeleton.
