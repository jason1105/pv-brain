"""Renderer unit: srt building + validation without invoking ffmpeg.

The single ffmpeg render of the suite lives in test_pipeline_e2e (budget:
docs/specs/05).
"""

import pytest

from pvfactory.errors import ValidationError
from pvfactory.render import FfmpegRenderer, TimelineEntry, build_srt, srt_timestamp


def test_srt_timestamps_and_structure():
    srt = build_srt(
        [{"narration": "First."}, {"narration": "Second."}],
        [1.5, 2.25],
    )
    lines = srt.splitlines()
    assert lines[0] == "1"
    assert lines[1] == "00:00:00,000 --> 00:00:01,500"
    assert lines[4] == "2"
    assert lines[5] == "00:00:01,500 --> 00:00:03,750"


def test_srt_timestamp_rollover():
    assert srt_timestamp(3661.007) == "01:01:01,007"


def test_srt_length_mismatch_fails():
    with pytest.raises(ValidationError):
        build_srt([{"narration": "x"}], [1.0, 2.0])


def test_render_rejects_degenerate_timeline(tmp_path):
    r = FfmpegRenderer()
    with pytest.raises(ValidationError, match="empty timeline"):
        r.render([], tmp_path / "a.wav", tmp_path / "out.mp4")
    entry = TimelineEntry("seg-001", tmp_path / "missing.png", -1.0)
    with pytest.raises(ValidationError, match="non-positive duration"):
        r.render([entry], tmp_path / "a.wav", tmp_path / "out.mp4")


def test_verify_rejects_missing_or_empty(tmp_path):
    r = FfmpegRenderer()
    with pytest.raises(ValidationError, match="missing or empty"):
        r.verify(tmp_path / "nope.mp4")
    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    with pytest.raises(ValidationError, match="missing or empty"):
        r.verify(empty)
    garbage = tmp_path / "garbage.mp4"
    garbage.write_bytes(b"not a video at all")
    with pytest.raises(ValidationError):
        r.verify(garbage)
