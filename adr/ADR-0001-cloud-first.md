# ADR-0001 — Cloud First Runtime

- **Status:** Accepted
- **Date:** 2026-07-05

## Context

The Autonomous Content Company is meant to run continuously — planning,
generating, and preparing content without waiting on a person's machine to
be awake. It must scale work across many models, run long tasks
unattended, and be reachable from anywhere.

## Decision

The system is designed as an always-on cloud runtime instead of a local
desktop application.

## Consequences

- The runtime can operate autonomously and continuously, not only while a
  user's computer is running.
- Compute, storage, and model access scale independently of any one device.
- The design must account for cloud concerns from the start: deployment,
  observability, cost control, and secure remote access.
- Local desktop-only workflows are explicitly out of scope.
