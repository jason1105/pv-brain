# End-to-End Viral Video Generator

- **Date:** 2026-07-05

Summary of today's discussion. Exploratory notes, not final decisions.

## End-to-end viral video generator

The starting point: a system that takes an idea and produces a complete,
distribution-ready video on its own — from concept and script through
generation and assembly — optimized for reach. The goal is *end to end*, not
a tool that helps at one step.

## Autonomous Content Company

The video generator is one expression of a larger idea: an **Autonomous
Content Company**. Instead of a single app, we imagine a company that runs
itself — planning, producing, and preparing content continuously, with
humans directing rather than operating.

## Creator Brain

The company needs a durable core — a **Creator Brain** — that holds the
vision, knowledge, workflows, and decisions. This repository is that brain.
It exists so the system's thinking is captured and reusable, independent of
any specific implementation.

## Workflow instead of Agent

We agreed the right central abstraction is the **workflow**, not the agent.
Business workflows describe what the company does; agents are implementation
details that carry out steps. This keeps the design stable as agents and
frameworks change (recorded as ADR-0002).

## Model Router

Different workflow steps need different models. A **Model Router** selects
the right model per step — balancing quality, cost, and latency — so
workflows stay model-agnostic and can improve as new models arrive.

## Cloud First

For the company to be always-on and autonomous, it must run in the cloud
rather than on a personal machine. This is a **Cloud First** runtime
(recorded as ADR-0001).

## Open threads

- How much human review sits between "generated" and "published"?
- What are the first workflows worth defining concretely?
- What signals define "viral" for the router to optimize toward?
