# The Video Package

Every run writes one self-contained directory:
`<output_root>/<channel_id>/<date>-<topic-slug>/` (prefixed `DRAFT-` for
drafts; a numeric suffix is added if the name already exists).

| File | What it is | What you do with it |
|------|-----------|---------------------|
| `video.mp4` | Decode-verified H.264/AAC render | Upload it |
| `thumbnail.png` | 1280×720, ≤5 words, style-preset colors | Set as thumbnail |
| `captions.srt` | Captions timed from the real narration audio | Upload as subtitles |
| `metadata.json` | Final title, description **with chapter timestamps**, tags, category, visibility | Copy-paste at upload |
| `PUBLISH_CHECKLIST.md` | Exact upload steps in order | Follow it |
| `script.md` / `script.json` | The narration, human/machine form | Review or reuse |
| `brief.json` | Angle, working title, thumbnail concept | Review the ideation |
| `voiceover.wav`, `voice/seg-*.wav` | Full and per-segment narration audio | Re-edit if desired |
| `timeline.json` | Which visual plays over which audio span | Debugging/re-rendering |
| `manifest.json` | Full provenance: per-step provider, model, prompt hash, seed, timings, artifact checksums | Audit, `inspect`, `resume` |
| `topic.txt`, `profile.toml` | The inputs, snapshotted | Reproducibility |

## Publishing (current milestone)

Publishing is **dry-run by design**: PV Factory prepares everything and a
human uploads, following `PUBLISH_CHECKLIST.md`. Start visibility at
Unlisted, review playback, then switch to Public. Direct YouTube upload is
a planned post-MVP provider behind the same `publish` step.

## Reproducibility

`manifest.json` records everything needed to explain any artifact: which
provider and model produced it, the prompt hash, the seed, and per-file
sha256. Offline runs with the same `--seed` are bit-for-bit deterministic
in content.
