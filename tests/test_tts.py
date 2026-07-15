import wave
from io import BytesIO

import pytest

from pvfactory.errors import ValidationError
from pvfactory.tts import SilenceTTS, ToneTTS, concat_wavs, wav_duration

SEGMENTS = [
    {"id": "seg-001", "narration": "Ten words of narration exactly here to measure timing now."},
    {"id": "seg-002", "narration": "Short one."},
    {
        "id": "seg-003",
        "narration": "A slightly longer narration segment with quite a few more words.",
    },
]


@pytest.mark.parametrize("cls", [SilenceTTS, ToneTTS])
def test_measured_durations_nonuniform_and_valid(cls):
    clips = cls(wpm=300).synthesize(SEGMENTS, seed=7)
    assert [c.segment_id for c in clips] == ["seg-001", "seg-002", "seg-003"]
    for c in clips:
        assert c.duration_s == pytest.approx(wav_duration(c.wav_bytes))
        assert c.duration_s >= 0.4
    durations = [c.duration_s for c in clips]
    assert len(set(durations)) == len(durations)  # deliberately non-uniform


def test_tone_is_audible_silence_is_not():
    tone = ToneTTS(wpm=600).synthesize(SEGMENTS[:1], seed=7)[0]
    silence = SilenceTTS(wpm=600).synthesize(SEGMENTS[:1], seed=7)[0]
    with wave.open(BytesIO(tone.wav_bytes)) as w:
        assert max(w.readframes(w.getnframes())) > 0
    with wave.open(BytesIO(silence.wav_bytes)) as w:
        assert max(w.readframes(w.getnframes())) == 0


def test_empty_narration_hard_fails():
    with pytest.raises(ValidationError, match="empty narration"):
        ToneTTS().synthesize([{"id": "seg-001", "narration": "   "}], seed=7)


def test_concat_matches_sum_of_durations():
    clips = ToneTTS(wpm=600).synthesize(SEGMENTS, seed=7)
    total = wav_duration(concat_wavs([c.wav_bytes for c in clips]))
    assert total == pytest.approx(sum(c.duration_s for c in clips), abs=0.01)
