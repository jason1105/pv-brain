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
pvfactory produce --profile channel.toml --topic "your topic" --offline
```

Offline runs produce clearly-labeled DRAFT packages (mock content, tone
audio). Real LLM/TTS providers arrive in milestone M3 - see
[`docs/plan/`](docs/plan/) and [`docs/specs/`](docs/specs/).

## New here?

Start with:

1. [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) for a quick introduction.
2. [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) for repository conventions and workflows.
3. [`docs/vision/`](docs/vision/) to understand the long-term direction.
4. [`docs/architecture/`](docs/architecture/) to understand how the system is organized.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the project roadmap and [`docs/CHANGELOG.md`](docs/CHANGELOG.md) for notable repository changes.
