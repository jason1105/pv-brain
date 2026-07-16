# Channel Profile Reference

One TOML file per channel. Unknown keys are rejected (typo protection);
[`../../examples/channel.toml`](../../examples/channel.toml) is a working
starting point.

```toml
schema_version = 1          # required, must be 1

[channel]
id = "tech-explains"        # required; slug only ([a-z0-9-_], becomes a directory name)
name = "Tech Explains"      # required
niche = "consumer tech explainers"   # required; feeds every prompt
audience = "curious non-experts"     # required; feeds every prompt
language = "en"             # BCP-47. Non-latin languages need font_path (below)

[content]
tone = "curious, punchy, no hype"    # voice of the script
video_minutes_target = 5    # target length; drives script segment count
style = "dark"              # slide/thumbnail preset: dark | light | bold

[render]
resolution = "1920x1080"    # even width/height required (H.264 constraint)
fps = 30                    # 1..60
# font_path = "/path/to/NotoSansCJK.otf"   # REQUIRED for zh/ja/ko/ru/ar/hi/th

[providers]
llm = "anthropic"           # anthropic | ark | gemini  (mock only via --offline)
llm_model = "claude-sonnet-5"   # ark: endpoint/model id; gemini: e.g. gemini-2.5-flash
tts = "edge"                # edge | tone | silence
tts_voice = "en-US-GuyNeural"   # edge voices; try zh-CN-YunxiNeural for Chinese
# tts_wpm = 150             # offline tts pacing only (tests/CI)
```

Notes:

- **`language` and fonts.** The bundled DejaVu font covers latin scripts.
  For CJK and other non-latin languages the pipeline fails fast at step 0
  unless `font_path` points to a covering font (e.g. Noto Sans CJK) —
  by design, so you never render tofu boxes silently.
- **`style`** changes slide colors/layout and thumbnail colors so two
  channels don't look identical.
- The profile is snapshotted into every package (`profile.toml`), which is
  what `resume` uses — editing your profile never breaks old runs.
