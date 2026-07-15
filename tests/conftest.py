from pathlib import Path

import pytest

# E2E budget (docs/specs/05): tiny resolution, ultra-fast narration pacing so
# total audio stays within seconds, one ffmpeg render for the whole suite.
TINY_PROFILE = """\
schema_version = 1

[channel]
id = "test-channel"
name = "Test Channel"
niche = "testing"
audience = "test runners"
language = "en"

[content]
tone = "brisk"
video_minutes_target = 1
style = "dark"

[render]
resolution = "320x180"
fps = 10

[providers]
tts = "tone"
tts_wpm = 6000
"""


@pytest.fixture
def tiny_profile(tmp_path: Path) -> Path:
    p = tmp_path / "profile.toml"
    p.write_text(TINY_PROFILE, "utf-8")
    return p
