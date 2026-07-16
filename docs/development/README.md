# PV Factory — Developer Guide

For contributors working on `src/pvfactory/`. For contracts and design
rationale, read [`../specs/`](../specs/) and the ADRs in
[`../adr/`](../adr/) first — this guide assumes them and focuses on *how to
change the code*.

| Chapter | Covers |
|---------|--------|
| [`01-codebase-map.md`](01-codebase-map.md) | Every module, one line each, and how they fit together |
| [`02-adding-a-provider.md`](02-adding-a-provider.md) | Adding an LLM or TTS adapter |
| [`03-adding-a-workflow-step.md`](03-adding-a-workflow-step.md) | Adding/changing pipeline steps, artifact contracts |
| [`04-testing.md`](04-testing.md) | Test pyramid, fixtures, what must never touch the network |
| [`05-contributing.md`](05-contributing.md) | Issue → worktree → PR → CI → merge, and the invariants every PR must hold |
