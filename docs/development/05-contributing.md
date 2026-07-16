# Contributing

## Process

1. **Open an issue** describing why and what, scoped to one coherent
   change.
2. **Branch from `main`** (a worktree, if working alongside other changes):
   `git worktree add ../wt-name -b your-branch-name main`.
3. **Implement.** Run `ruff check src tests` and `pytest` before every
   commit.
4. **Push and open a PR** against `main`, referencing the issue
   (`Closes #N`).
5. **CI must be green** (`ruff` + full `pytest` — see
   `.github/workflows/ci.yml`, path-filtered to `src/`, `tests/`,
   `pyproject.toml` so docs-only PRs never trigger it).
6. **Merge.**

## Invariants every PR must hold

These are the binding contracts from `docs/specs/`; violating them is a
bug, not a style choice.

- **No parsing/validation logic inside a provider adapter.** All LLM output
  goes through `llm.call_llm`; all TTS durations are measured, never
  estimated.
- **Every workflow-step output is an `artifact://` ref.** No raw
  filesystem paths cross a step boundary (the one narrow exception is
  `ArtifactStore.path_for()`, used only to hand a file to a subprocess).
- **Fail at the earliest possible boundary.** Config problems
  (`ConfigError`, exit 2) at profile-load/provider-resolution time;
  pipeline problems (`StepError`/`ValidationError`, exit 1) at the step
  that detects them — never let a bad input propagate silently.
- **Offline/mock content providers are never selected silently**
  (ADR-0005). Any run using one is a draft: watermarked, `DRAFT-`
  prefixed, `manifest.json` flagged.
- **Secrets only via environment variables**, sent only in HTTP headers.
  Never in TOML, manifests, logs, or committed fixtures.
- **The manifest is a provenance record, checkpointed at every step
  boundary** — don't buffer step results in memory across multiple steps
  before persisting.

## Code review

For nontrivial changes, run `/code-review` (or the equivalent
skill-driven review) before merging — see PRs #14 and #16 for the
standard this repo holds: findings get fixed with regression tests in the
same PR, not deferred. Findings that reveal a real architectural gap
(e.g. "the registry doesn't exist yet") get filed as a note in the PR
description under a "Deferred to M-next" heading, not silently dropped.

## Documentation

- Code changes that alter a **contract** (a provider interface, an
  artifact shape, the CLI surface) must update the matching
  `docs/specs/` file in the same PR.
- User-visible changes (new provider, new flag, new profile key) update
  `docs/manual/`.
- Structural/internal changes (new module, new pattern) update
  `docs/development/`.
- Every PR that changes behavior gets a `docs/CHANGELOG.md` entry.
