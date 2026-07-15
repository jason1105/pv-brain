"""Channel profile: TOML, schema_version-gated, unknown keys rejected.

Schema per docs/specs/04-cli-and-outputs.md.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import ConfigError

PROFILE_SCHEMA_VERSION = 1
STYLE_PRESETS = ("dark", "light", "bold")

_KNOWN = {
    "": {"schema_version", "channel", "content", "render", "providers"},
    "channel": {"id", "name", "niche", "audience", "language"},
    "content": {"tone", "video_minutes_target", "style"},
    "render": {"resolution", "fps", "font_path"},
    "providers": {"llm", "llm_model", "tts", "tts_voice", "tts_wpm"},
}


@dataclass
class ChannelProfile:
    channel_id: str
    name: str
    niche: str
    audience: str
    language: str = "en"
    tone: str = "clear, direct"
    video_minutes_target: int = 5
    style: str = "dark"
    width: int = 1920
    height: int = 1080
    fps: int = 30
    font_path: str | None = None
    providers: dict[str, str | int] = field(default_factory=dict)

    @property
    def resolution(self) -> tuple[int, int]:
        return (self.width, self.height)


def _reject_unknown(section: str, data: dict) -> None:
    unknown = set(data) - _KNOWN[section]
    if unknown:
        where = f"[{section}]" if section else "profile top level"
        raise ConfigError(f"unknown key(s) in {where}: {sorted(unknown)}")


def load_profile(path: Path | str) -> ChannelProfile:
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"profile not found: {path}")
    with path.open("rb") as f:
        data = tomllib.load(f)

    _reject_unknown("", data)
    if data.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ConfigError(
            f"profile schema_version must be {PROFILE_SCHEMA_VERSION}, "
            f"got {data.get('schema_version')!r}"
        )

    channel = data.get("channel")
    if not isinstance(channel, dict):
        raise ConfigError("profile missing [channel] section")
    _reject_unknown("channel", channel)
    for req in ("id", "name", "niche", "audience"):
        if not channel.get(req):
            raise ConfigError(f"profile [channel] missing required key {req!r}")

    content = data.get("content", {})
    _reject_unknown("content", content)
    style = content.get("style", "dark")
    if style not in STYLE_PRESETS:
        raise ConfigError(f"[content] style must be one of {STYLE_PRESETS}, got {style!r}")
    minutes = content.get("video_minutes_target", 5)
    if not isinstance(minutes, int) or minutes < 1:
        raise ConfigError("[content] video_minutes_target must be a positive integer")

    render = data.get("render", {})
    _reject_unknown("render", render)
    resolution = render.get("resolution", "1920x1080")
    try:
        w, h = (int(x) for x in str(resolution).lower().split("x"))
        if w < 64 or h < 64:
            raise ValueError
    except ValueError:
        raise ConfigError(
            f"[render] resolution must look like '1920x1080', got {resolution!r}"
        ) from None
    fps = render.get("fps", 30)
    if not isinstance(fps, int) or not 1 <= fps <= 60:
        raise ConfigError("[render] fps must be an integer in 1..60")

    providers = data.get("providers", {})
    _reject_unknown("providers", providers)

    return ChannelProfile(
        channel_id=str(channel["id"]),
        name=str(channel["name"]),
        niche=str(channel["niche"]),
        audience=str(channel["audience"]),
        language=str(channel.get("language", "en")),
        tone=str(content.get("tone", "clear, direct")),
        video_minutes_target=minutes,
        style=style,
        width=w,
        height=h,
        fps=fps,
        font_path=render.get("font_path"),
        providers=dict(providers),
    )
