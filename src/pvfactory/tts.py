"""TTS providers.

Binding contract (docs/specs/03): providers return per-segment audio with
MEASURED durations. Words-per-minute estimation never leaves the inside of
the offline providers, and their per-segment durations are deliberately
non-uniform so downstream code cannot assume uniform timing.
"""

from __future__ import annotations

import io
import math
import random
import struct
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .errors import ValidationError

SAMPLE_RATE = 22050
SAMPLE_WIDTH = 2  # 16-bit
CHANNELS = 1


@dataclass(frozen=True)
class SegmentAudio:
    segment_id: str
    wav_bytes: bytes
    duration_s: float


class TTSProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def synthesize(self, segments: list[dict], seed: int) -> list[SegmentAudio]:
        """segments: script segments (id, narration). Returns one clip each."""


def _write_wav(frames: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(SAMPLE_WIDTH)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(frames)
    return buf.getvalue()


def wav_duration(wav_bytes: bytes) -> float:
    with wave.open(io.BytesIO(wav_bytes), "rb") as w:
        return w.getnframes() / w.getframerate()


def concat_wavs(clips: list[bytes]) -> bytes:
    frames = bytearray()
    for clip in clips:
        with wave.open(io.BytesIO(clip), "rb") as w:
            if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (
                CHANNELS,
                SAMPLE_WIDTH,
                SAMPLE_RATE,
            ):
                raise ValidationError("cannot concatenate WAVs with mismatched parameters")
            frames.extend(w.readframes(w.getnframes()))
    return _write_wav(bytes(frames))


class _OfflineTTS(TTSProvider):
    """Shared duration logic: WPM heuristic + seeded non-uniform jitter,
    strictly internal to this class (spec 03)."""

    def __init__(self, wpm: int = 150):
        if not 30 <= wpm <= 20000:
            raise ValidationError(f"tts wpm out of range: {wpm}")
        self.wpm = wpm

    def _duration(self, narration: str, rng: random.Random) -> float:
        words = max(1, len(narration.split()))
        base = words / self.wpm * 60.0
        return max(0.4, base * rng.uniform(0.75, 1.3))

    def synthesize(self, segments: list[dict], seed: int) -> list[SegmentAudio]:
        out: list[SegmentAudio] = []
        for i, seg in enumerate(segments):
            narration = seg.get("narration", "")
            if not narration.strip():
                raise ValidationError(f"segment {seg.get('id', i)} has empty narration")
            rng = random.Random(f"{seed}:{self.name}:{i}")
            n_frames = int(self._duration(narration, rng) * SAMPLE_RATE)
            frames = self._frames(n_frames, i)
            wav = _write_wav(frames)
            out.append(SegmentAudio(seg["id"], wav, wav_duration(wav)))
        return out

    def _frames(self, n_frames: int, index: int) -> bytes:
        raise NotImplementedError


class SilenceTTS(_OfflineTTS):
    """Paced silence. CI-grade placeholder (ADR-0005: drafts only)."""

    name = "silence"

    def _frames(self, n_frames: int, index: int) -> bytes:
        return b"\x00\x00" * n_frames


class ToneTTS(_OfflineTTS):
    """Distinct sine pitch per segment - makes A/V sync audible and
    decode-verifiable offline at zero dependency cost (spec 03)."""

    name = "tone"

    def _frames(self, n_frames: int, index: int) -> bytes:
        freq = 220.0 + 40.0 * (index % 8)
        amp = 0.25 * 32767
        fade = min(n_frames // 10, SAMPLE_RATE // 20) or 1
        buf = bytearray()
        for n in range(n_frames):
            envelope = min(1.0, n / fade, (n_frames - 1 - n) / fade)
            sample = int(amp * envelope * math.sin(2 * math.pi * freq * n / SAMPLE_RATE))
            buf += struct.pack("<h", sample)
        return bytes(buf)


OFFLINE_TTS = {"silence": SilenceTTS, "tone": ToneTTS}
