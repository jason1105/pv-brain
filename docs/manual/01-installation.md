# Installation & First Run

## Requirements

- Python 3.11+
- pip. No system ffmpeg needed — a static binary ships inside the
  `imageio-ffmpeg` wheel.

## Install

```bash
git clone https://github.com/jason1105/pv-brain.git
cd pv-brain
pip install -e .            # add ".[edge]" for real speech, ".[dev]" for tests
```

## Verify

```bash
pvfactory doctor
```

`doctor` checks Python, the bundled ffmpeg, Pillow, and the bundled font,
then lists which LLM providers have API keys configured and whether the
`edge` TTS is installed. Exit code 0 means you can produce videos.

Pass `--profile examples/channel.toml` to also validate a profile (schema,
style, font coverage for its language).

## First video (offline draft)

```bash
pvfactory produce --profile examples/channel.toml \
  --topic "why solid state drives fail" --offline --seed 42
```

This runs the whole pipeline with deterministic offline providers: no
network, no keys, no cost. The last stdout line is the package directory —
prefixed `DRAFT-`, watermarked, with tone audio instead of speech. Drafts
verify the pipeline; they are not for upload.

## First real video

Configure a provider key (see [`04-providers.md`](04-providers.md)), set
`[providers]` in your profile, then run the same command **without**
`--offline`. The package is produced with real script content and real
narration, ready for the publish checklist inside it.
