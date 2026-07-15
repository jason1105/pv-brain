"""FFmpeg renderer (docs/specs/03, binding architecture).

One still image per timeline entry, fed to ffmpeg via the concat demuxer
with per-entry durations, in a SINGLE invocation. Generating video frames in
a Python loop is prohibited. Output is decode-verified; ffprobe does not
exist in the bundled distribution.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg

from .errors import StepError, ValidationError

FFMPEG_TIMEOUT_S = 300


def _concat_quote(path: Path) -> str:
    """Quote a path for an ffmpeg concat list. The format has no in-string
    escape: a literal single quote must be spliced as '\\''."""
    return "'" + path.as_posix().replace("'", "'\\''") + "'"


@dataclass(frozen=True)
class TimelineEntry:
    segment_id: str
    image_path: Path
    duration_s: float


def ffmpeg_exe() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(args: list[str], timeout: int = FFMPEG_TIMEOUT_S) -> subprocess.CompletedProcess:
    return subprocess.run(
        [ffmpeg_exe(), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class FfmpegRenderer:
    name = "ffmpeg"

    def render(
        self,
        entries: list[TimelineEntry],
        audio_path: Path,
        out_path: Path,
        fps: int = 30,
        timeout_s: int = FFMPEG_TIMEOUT_S,
    ) -> float:
        """Render and decode-verify; returns measured duration in seconds."""
        if not entries:
            raise ValidationError("renderer: empty timeline")
        for e in entries:
            if e.duration_s <= 0:
                raise ValidationError(f"renderer: non-positive duration for {e.segment_id}")
            if not e.image_path.is_file():
                raise ValidationError(f"renderer: missing image for {e.segment_id}")
        if not audio_path.is_file():
            raise ValidationError("renderer: missing audio track")

        # The concat list is renderer-internal scratch, not a package file
        # (spec 04 defines the exact package contents) - keep it in a tempdir.
        with tempfile.TemporaryDirectory(prefix="pvfactory-render-") as tmp:
            concat = Path(tmp) / "concat.txt"
            lines = []
            for e in entries:
                lines.append(f"file {_concat_quote(e.image_path)}")
                lines.append(f"duration {e.duration_s:.3f}")
            # concat demuxer quirk: repeat the last file so its duration applies
            lines.append(f"file {_concat_quote(entries[-1].image_path)}")
            concat.write_text("\n".join(lines) + "\n", "utf-8")

            proc = _run(
                [
                    "-y",
                    "-f", "concat", "-safe", "0", "-i", concat.as_posix(),
                    "-i", audio_path.as_posix(),
                    "-c:v", "libx264", "-tune", "stillimage",
                    "-vf", f"fps={fps},format=yuv420p",
                    "-c:a", "aac",
                    "-shortest",
                    out_path.as_posix(),
                ],
                timeout=timeout_s,
            )
        if proc.returncode != 0:
            raise StepError("render_video", f"ffmpeg failed:\n{proc.stderr[-2000:]}")
        return self.verify(out_path)

    def verify(self, path: Path) -> float:
        """Decode check + duration parse from stderr. 'File exists' is not
        verification (spec 05)."""
        if not path.is_file() or path.stat().st_size == 0:
            raise ValidationError(f"render output missing or empty: {path}")
        proc = _run(["-v", "error", "-i", path.as_posix(), "-f", "null", "-"])
        if proc.returncode != 0 or proc.stderr.strip():
            raise ValidationError(f"rendered file fails decode check: {proc.stderr[-1000:]}")
        banner = _run(["-i", path.as_posix()])  # exits non-zero by design; stderr has metadata
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", banner.stderr)
        if not m:
            raise ValidationError("could not determine rendered duration")
        hours, minutes, seconds = int(m.group(1)), int(m.group(2)), float(m.group(3))
        duration = hours * 3600 + minutes * 60 + seconds
        if duration <= 0:
            raise ValidationError("rendered file has zero duration")
        if "Video:" not in banner.stderr or "Audio:" not in banner.stderr:
            raise ValidationError("rendered file is missing a video or audio stream")
        return duration


def srt_timestamp(t: float) -> str:
    ms = round(t * 1000)
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(segments: list[dict], durations: list[float]) -> str:
    """Captions from segments + MEASURED timings (spec 02)."""
    if len(segments) != len(durations):
        raise ValidationError("captions: segments and durations differ in length")
    out = []
    t = 0.0
    for i, (seg, dur) in enumerate(zip(segments, durations, strict=True), start=1):
        out.append(str(i))
        out.append(f"{srt_timestamp(t)} --> {srt_timestamp(t + dur)}")
        out.append(seg["narration"].strip())
        out.append("")
        t += dur
    return "\n".join(out)
