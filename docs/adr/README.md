# Architecture Decision Records

This directory records significant architectural decisions and the reasoning
behind them. Each ADR captures one decision, its context, and its
consequences, so future readers understand *why* — not just *what*.

## Conventions

- One decision per file, named `ADR-NNNN-short-title.md`.
- Numbers are sequential and never reused.
- Once accepted, an ADR is not edited to reverse its meaning; instead a new
  ADR supersedes it.

## Records

- [ADR-0001 — Cloud First Runtime](ADR-0001-cloud-first.md)
- [ADR-0002 — Workflow First](ADR-0002-workflow-first.md)
- [ADR-0003 — Runtime Code Lives in the pv-brain Monorepo](ADR-0003-runtime-in-monorepo.md)
- [ADR-0004 — CLI Engine First, Service Wrapper Later](ADR-0004-cli-engine-first.md)
- [ADR-0005 — Offline-First Providers with Explicit Draft Labeling](ADR-0005-offline-first-providers.md)
