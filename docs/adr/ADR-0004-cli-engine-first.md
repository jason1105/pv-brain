# ADR-0004 — CLI Engine First, Service Wrapper Later

- **Status:** Accepted
- **Date:** 2026-07-15

## Context

ADR-0001 commits to an always-on cloud runtime. The MVP, however, ships a
CLI. Adversarial review concluded the entry point is not where cloud-first
is won or lost — the **data model** is: a runtime whose state lives in an
in-process dict with raw local paths can never be wrapped into a service
without a rewrite.

## Decision

The engine is a **library** with a pure-function entry point; the CLI is a
thin, headless shell over it and milestone 1 of the cloud runtime — not a
desktop product. Cloud-first is enforced structurally:

- Durable run state: stable `run_id`, persistence at every step boundary,
  idempotent resume.
- Artifacts behind an `ArtifactStore` interface with URI-like references;
  only the local implementation knows about the filesystem.
- No step may require a TTY or interactive input; config via files/env;
  machine-readable manifest and exit codes.

## Consequences

- The later always-on service (scheduler, API) wraps the same engine — a
  wrapper, not a rewrite. That is the test of this ADR.
- CLI-only conveniences (interactive prompts, terminal UX as API) are
  prohibited in the engine.
- ADR-0001 stands: this sequences it, it does not weaken it.
