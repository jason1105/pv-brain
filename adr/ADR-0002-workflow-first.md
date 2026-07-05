# ADR-0002 — Workflow First

- **Status:** Accepted
- **Date:** 2026-07-05

## Context

There are many ways to organize an AI system: around models, around agents,
or around the work itself. Agent-centric designs tend to drift as models
change, and they make the *business* intent hard to see. We need an
abstraction that stays stable while the underlying models and agents evolve.

## Decision

Business workflow is the core abstraction. Agents are implementation
details.

## Consequences

- Workflows describe *what* the system does, independent of which agent or
  model performs each step.
- Agents, models, and prompts can be swapped or upgraded without changing
  the workflow's meaning.
- Design conversations start from the workflow, not from a specific agent
  framework.
- A model router can select the right model per workflow step without the
  workflow needing to know the details.
