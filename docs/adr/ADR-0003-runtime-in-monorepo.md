# ADR-0003 — Runtime Code Lives in the pv-brain Monorepo

- **Status:** Accepted
- **Date:** 2026-07-15

## Context

pv-brain was framed as pure knowledge, "independent of any specific
implementation" (2026-07-05 brainstorm). The first executable workflow
(PV Factory, the auto video generator) needs a home. A separate repo keeps
the framing pure but splits specs from code, doubles process overhead, and
slows the tight docs↔code loop this phase needs.

## Decision

Implementation code lives in this repository: Python package under `src/`,
documentation stays under `docs/`. The knowledge base's
implementation-independence claim is consciously superseded for this phase.

## Consequences

- Specs, ADRs, prompts, and the code that implements them evolve in one
  place, one PR at a time.
- CI must be path-filtered so docs-only changes never run or block on
  Python checks.
- **Extraction condition:** if a second runtime consumer appears (another
  product embedding the engine) or release/distribution needs diverge from
  the knowledge base's cadence, `pvfactory` is extracted to its own repo and
  this ADR is superseded.

## Supersedes / amends

Amends the implementation-independence stance recorded in the 2026-07-05
brainstorm note; ADR-0001 and ADR-0002 are unaffected.
