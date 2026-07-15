"""EdgeTTS: real speech via edge-tts (optional extra `pvfactory[edge]`).

Honors the binding TTS contract (spec 03): per-segment audio with MEASURED
durations. Audio arrives as mp3 and is transcoded to the pipeline's WAV
parameters with the bundled ffmpeg, then measured with the wave module -
never estimated.
"""

from __future__ import annotations

import asyncio
import subprocess

from .errors import ConfigError, StepError
from .render import ffmpeg_exe
from .tts import CHANNELS, SAMPLE_RATE, SegmentAudio, TTSProvider, wav_duration

DEFAULT_VOICE = "en-US-GuyNeural"
TRANSCODE_TIMEOUT_S = 120


def transcode_to_wav(audio_bytes: bytes) -> bytes:
    """Any-format audio -> pipeline WAV (22050 Hz mono s16) via pipes."""
    proc = subprocess.run(
        [
            ffmpeg_exe(),
            "-i", "pipe:0",
            "-f", "wav", "-acodec", "pcm_s16le",
            "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS),
            "pipe:1",
        ],
        input=audio_bytes,
        capture_output=True,
        timeout=TRANSCODE_TIMEOUT_S,
    )
    if proc.returncode != 0 or not proc.stdout:
        raise StepError(
            "synthesize_voice",
            f"audio transcode failed: {proc.stderr.decode('utf-8', 'replace')[-500:]}",
        )
    return proc.stdout


class EdgeTTS(TTSProvider):
    """Microsoft Edge neural voices - free, keyless, network required."""

    name = "edge"

    def __init__(self, voice: str = DEFAULT_VOICE):
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            raise ConfigError(
                "the 'edge' TTS provider needs the edge-tts package: "
                "pip install 'pvfactory[edge]'"
            ) from None
        self.voice = voice

    async def _synth_mp3(self, text: str) -> bytes:
        import edge_tts

        chunks = []
        async for chunk in edge_tts.Communicate(text, self.voice).stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)

    def synthesize(self, segments: list[dict], seed: int) -> list[SegmentAudio]:
        out: list[SegmentAudio] = []
        for i, seg in enumerate(segments):
            narration = str(seg.get("narration", "")).strip()
            if not narration:
                raise StepError("synthesize_voice", f"segment {seg.get('id', i)} empty narration")
            mp3 = asyncio.run(self._synth_mp3(narration))
            if not mp3:
                raise StepError(
                    "synthesize_voice", f"edge-tts returned no audio for {seg.get('id', i)}"
                )
            wav = transcode_to_wav(mp3)
            out.append(SegmentAudio(seg["id"], wav, wav_duration(wav)))
        return out
