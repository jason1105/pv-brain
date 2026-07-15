# Architecture Overview

The system is organized as a top-down flow. Each layer constrains and feeds
the one below it: the vision shapes the knowledge, the knowledge informs the
architecture, the architecture defines the workflows, the workflows are
expressed as prompts, and the runtime executes them.

```
Vision
  ↓
Knowledge
  ↓
Architecture
  ↓
Workflow
  ↓
Prompt
  ↓
Runtime
```

## Layers

- **Vision** — why the system exists and what it should become. The stable
  intent that everything else serves.
- **Knowledge** — distilled, reusable understanding of the domain, derived
  from the vision and from research.
- **Architecture** — how the system is structured to realize the vision,
  including the model router and the cloud runtime boundaries.
- **Workflow** — the core abstraction. Business workflows describe what the
  system does, step by step, independent of which agent or model runs them.
- **Prompt** — the concrete instructions that drive models within a
  workflow step.
- **Runtime** — the always-on cloud execution layer that runs the workflows
  and routes each step to the right model.

## Why this order

Higher layers are more stable and change slowly; lower layers are more
concrete and change often. Keeping the flow explicit means a change in
intent propagates deliberately downward, and no implementation detail
silently redefines the vision.
