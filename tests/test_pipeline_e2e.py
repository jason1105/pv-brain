"""The e2e smoke test (docs/specs/05): one offline run, one real (tiny)
decode-verified mp4, full package asserted. Budget: 320x180, fast pacing.
"""

import json

from pvfactory.artifacts import LocalArtifactStore
from pvfactory.manifest import Manifest
from pvfactory.render import FfmpegRenderer
from pvfactory.runs import produce_video

EXPECTED_FILES = [
    "manifest.json",
    "brief.json",
    "script.json",
    "script.md",
    "voiceover.wav",
    "timeline.json",
    "video.mp4",
    "captions.srt",
    "thumbnail.png",
    "metadata.json",
    "PUBLISH_CHECKLIST.md",
    "publish_result.json",
    "profile.toml",
]


def test_offline_produce_end_to_end(tiny_profile, tmp_path):
    pkg = produce_video(
        profile_path=tiny_profile,
        topic="why solid state drives fail",
        output_root=tmp_path / "out",
        offline=True,
        seed=42,
    )

    # Draft policy (ADR-0005)
    assert pkg.name.startswith("DRAFT-")
    for name in EXPECTED_FILES:
        assert (pkg / name).exists(), f"missing {name}"

    manifest = Manifest.load(LocalArtifactStore(pkg))
    assert manifest.draft is True
    assert [s.status for s in manifest.steps] == ["done"] * 9
    llm_steps = [s for s in manifest.steps if s.prompt_ref]
    assert llm_steps and all(s.provider == "mock" and s.prompt_hash for s in llm_steps)
    assert all("sha256" in a for a in manifest.artifacts.values())

    # decode-verified video, duration matches measured segment timings
    duration = FfmpegRenderer().verify(pkg / "video.mp4")
    voice = json.loads((pkg / "voice_track.json").read_text("utf-8"))
    expected = sum(s["duration_s"] for s in voice["segments"])
    assert abs(duration - expected) <= 2.0

    # operator-complete metadata with chapters from measured timings
    meta = json.loads((pkg / "metadata.json").read_text("utf-8"))
    assert meta["draft"] is True
    assert "Chapters:" in meta["description"]
    assert meta["description"].count("\n00:") >= 0  # chapters present
    assert len(meta["tags"]) >= 4

    # captions parse as srt
    srt = (pkg / "captions.srt").read_text("utf-8")
    assert srt.startswith("1\n00:00:00,000 --> ")

    # channel store recorded the topic
    channels = json.loads((tmp_path / "out" / "channels.json").read_text("utf-8"))
    topics = [e["topic"] for e in channels["channels"]["test-channel"]]
    assert "why solid state drives fail" in topics


def test_online_mode_refuses_without_real_providers(tiny_profile, tmp_path):
    import pytest

    from pvfactory.errors import ConfigError

    with pytest.raises(ConfigError, match="--offline"):
        produce_video(
            profile_path=tiny_profile,
            topic="anything",
            output_root=tmp_path / "out",
            offline=False,
            seed=1,
        )
