# Command Reference

All commands are headless: progress goes to stderr, results to stdout, and
exit codes are `0` success, `1` pipeline step failure, `2` configuration or
environment error.

## `pvfactory produce`

```bash
pvfactory produce --profile CHANNEL.toml --topic "one topic"
pvfactory produce --profile CHANNEL.toml --backlog topics.txt
```

| Flag | Meaning |
|------|---------|
| `--profile PATH` | Channel profile TOML (required) |
| `--topic "…"` | Produce one video for this topic |
| `--backlog FILE` | One topic per line; produces N packages sequentially |
| `--offline` | Use deterministic draft providers (no network/keys); output is a watermarked DRAFT |
| `--seed N` | Reproducible offline runs; backlog items use seed N, N+1, … |
| `--output-root DIR` | Where packages go (default `./output`) |

The final stdout line per video is its package path — pipe-friendly.

## `pvfactory resume --run RUN_ID`

Continues a failed or interrupted run from its last completed step.
Completed steps are never re-executed; the original provider mode (offline
or real) is restored from the run's manifest. Find the RUN_ID with
`inspect` or in `manifest.json`.

## `pvfactory inspect --run RUN_ID`

Prints the run's summary: channel, workflow, draft flag, and per-step
status/provider/duration/error. Use it to see where a run failed before
resuming.

## `pvfactory doctor [--profile CHANNEL.toml]`

Environment check: Python, bundled ffmpeg, Pillow, bundled font, configured
API keys, edge-tts availability — plus profile validation when given one.
Run it first whenever something misbehaves.

## Typical session

```bash
export ARK_API_KEY=...                       # or ANTHROPIC_API_KEY / GEMINI_API_KEY
pvfactory doctor --profile channels/tech.toml
pvfactory produce --profile channels/tech.toml --backlog this-week.txt
# one package failed? see why, then continue it:
pvfactory inspect --run run-20260715-231927-06dca8
pvfactory resume  --run run-20260715-231927-06dca8
```
