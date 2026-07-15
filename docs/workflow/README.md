# Workflow

Business workflow definitions.

Workflows are the core abstraction of the system (see
[ADR-0002](../adr/ADR-0002-workflow-first.md)). Documents here describe *what*
the Autonomous Content Company does, step by step — independent of which
agent or model executes each step. Keep workflows expressed in business
terms so they remain stable as the underlying agents and models change.

## Workflows

- [`produce-video.md`](produce-video.md) — per-video production, the first
  executable workflow (implemented by PV Factory).
