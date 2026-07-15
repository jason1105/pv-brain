# Specifications

Product and technical specifications for **PV Factory** (`pvfactory`) — the
auto video generation software, the first executable workflow of the
Autonomous Content Company.

The design was stress-tested by a three-lens adversarial review
(feasibility/testability, product value/scope, architecture/extensibility)
before these documents were finalized; their binding conclusions are folded
into the specs below.

## Documents

| Document | Contents |
|----------|----------|
| [`01-overview.md`](01-overview.md) | Product definition, goals, non-goals, acceptance criteria, glossary |
| [`02-workflow-and-pipeline.md`](02-workflow-and-pipeline.md) | Workflow model, pipeline steps, artifacts, data model, run lifecycle |
| [`03-providers.md`](03-providers.md) | Provider interfaces and contracts, model routing, configuration, secrets |
| [`04-cli-and-outputs.md`](04-cli-and-outputs.md) | CLI commands, channel profile schema, output layout, exit codes |
| [`05-quality.md`](05-quality.md) | Testing strategy, CI, performance budgets, security, licensing |

## Related

- Business workflow definition: [`../workflow/produce-video.md`](../workflow/produce-video.md)
- Prompt templates consumed by the pipeline: [`../prompts/youtube/`](../prompts/youtube/)
- Decisions: [ADR-0003](../adr/ADR-0003-runtime-in-monorepo.md),
  [ADR-0004](../adr/ADR-0004-cli-engine-first.md),
  [ADR-0005](../adr/ADR-0005-offline-first-providers.md)
