# Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | ffmpeg render produces corrupt/black output undetected | Med | High | Decode verification is part of the renderer contract, not just tests (spec 03); e2e uses `tone` audio so sync is observable. |
| 2 | Real TTS (edge-tts) breaks or is blocked (network policy, service changes) | Med | High | TTS contract is provider-agnostic; silence/tone keep the pipeline alive; a second real provider (paid API) is a small adapter. |
| 3 | Anthropic adapter drifts from mock behavior | Med | Med | One shared parse/validate layer + fixture contract tests (spec 05); adapter contains no parsing logic of its own. |
| 4 | CJK profiles render tofu | High (if unguarded) | Med | Glyph-coverage validation at step 0 fails loudly; `font_path` profile key documented (spec 03/04). |
| 5 | CI slow/flaky from ffmpeg startup costs | Med | Med | Hard e2e caps (≤320×180, ≤3 s audio, timeouts); ffmpeg invocation budget (spec 05). |
| 6 | Draft output mistaken for deliverable | Low (post ADR-0005) | High | Explicit `--offline`, watermark, `DRAFT-` prefix, manifest flag — four independent markers. |
| 7 | Engine accretes CLI-only assumptions, service milestone becomes a rewrite | Med | High | ADR-0004 structural rules (pure function, no TTY, ArtifactStore, durable runs) enforced from M1; the service milestone is the test. |
| 8 | Scope creep into strategy tooling before production quality lands | Med | Med | Spec 01 non-goals; strategy is workflow #2, post-MVP. |
| 9 | Docs-repo CI friction (Python checks blocking docs PRs) | Low | Low | Path-filtered workflows from M0 (ADR-0003). |
| 10 | Licensing surprise if pvfactory is distributed (GPL ffmpeg build) | Low | Med | Recorded in spec 05; revisit at distribution time. |
