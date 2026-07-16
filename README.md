# pv-brain

**pv-brain** is the long-term knowledge repository for building an **Autonomous Content Company**.

## Layout

| Path | Purpose |
|------|---------|
| [`docs/`](docs/) | All documentation: vision, architecture, ADRs, specs, plans, prompts, research. |
| [`src/pvfactory/`](src/pvfactory/) | PV Factory - the auto video generation pipeline (first executable workflow). |
| [`tests/`](tests/) | Test suite for PV Factory. |

## PV Factory quickstart

```bash
pip install -e ".[dev]"
pvfactory doctor                       # verify the environment
pvfactory produce --profile examples/channel.toml --topic "your topic" --offline
```

Offline runs produce clearly-labeled DRAFT packages (mock content, tone
audio) - no network, no keys, no cost. Configure a real LLM (Anthropic,
Volcengine Ark, or Gemini) and TTS provider to produce publishable video
packages; see [`docs/manual/`](docs/manual/) for the full walkthrough.

- **Operators:** [`docs/manual/`](docs/manual/) - installation, channel
  profiles, commands, providers, the output package, troubleshooting.
- **Contributors:** [`docs/development/`](docs/development/) - codebase
  map, adding providers/workflow steps, testing, contribution process.
- **Design:** [`docs/specs/`](docs/specs/) (binding contracts),
  [`docs/adr/`](docs/adr/) (decisions), [`docs/plan/`](docs/plan/)
  (roadmap and milestones).

## New here?

Start with:

1. [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) for a quick introduction.
2. [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) for repository conventions and workflows.
3. [`docs/vision/`](docs/vision/) to understand the long-term direction.
4. [`docs/architecture/`](docs/architecture/) to understand how the system is organized.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the project roadmap and [`docs/CHANGELOG.md`](docs/CHANGELOG.md) for notable repository changes.
