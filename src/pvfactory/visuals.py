"""Slides visual provider, thumbnail, fonts, glyph-coverage validation.

Spec 03: bundled DejaVu font, never system font paths; glyph coverage is
validated against the profile language at pipeline start and fails loudly.
Draft runs get an unmissable watermark (ADR-0005).
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .errors import ConfigError
from .profile import ChannelProfile


@dataclass(frozen=True)
class Style:
    bg: tuple[int, int, int]
    fg: tuple[int, int, int]
    accent: tuple[int, int, int]
    muted: tuple[int, int, int]


STYLES: dict[str, Style] = {
    "dark": Style(bg=(17, 19, 26), fg=(240, 240, 245), accent=(255, 196, 0), muted=(150, 155, 170)),
    "light": Style(
        bg=(247, 247, 244), fg=(24, 26, 32), accent=(11, 94, 215), muted=(110, 112, 120)
    ),
    "bold": Style(
        bg=(96, 12, 24), fg=(255, 250, 245), accent=(255, 214, 60), muted=(220, 170, 170)
    ),
}

# Sample characters per language family for glyph-coverage validation.
_LANGUAGE_SAMPLES = {
    "zh": "视频内容",
    "ja": "動画のコンテンツ",
    "ko": "동영상 콘텐츠",
    "ru": "видео контент",
    "ar": "محتوى الفيديو",
    "hi": "वीडियो सामग्री",
    "th": "เนื้อหาวิดีโอ",
}


def bundled_font_path(bold: bool = False) -> Path:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return Path(str(resources.files("pvfactory.fonts").joinpath(name)))


def load_font(profile: ChannelProfile, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = Path(profile.font_path) if profile.font_path else bundled_font_path(bold)
    if not path.is_file():
        raise ConfigError(f"font not found: {path}")
    return ImageFont.truetype(str(path), size)


def font_covers(font: ImageFont.FreeTypeFont, text: str) -> bool:
    # A missing glyph renders as .notdef ("tofu"), which HAS ink - so an
    # empty-bbox check cannot detect it. Instead, compare each glyph's
    # rendering against a codepoint guaranteed to be absent (private use
    # area): identical bytes means .notdef.
    notdef = bytes(font.getmask("\ue000"))
    for ch in text:
        if ch.isspace():
            continue
        mask = font.getmask(ch)
        if mask.getbbox() is None or bytes(mask) == notdef:
            return False
    return True


def validate_glyph_coverage(profile: ChannelProfile) -> None:
    """Fail loudly at step 0 rather than render tofu (spec 03)."""
    lang = profile.language.lower().split("-")[0]
    sample = _LANGUAGE_SAMPLES.get(lang)
    if sample is None:
        return  # latin-script default; DejaVu covers it
    font = load_font(profile, 40)
    if not font_covers(font, sample):
        raise ConfigError(
            f"the configured font cannot render language {profile.language!r} "
            f"(sample {sample!r} has no glyphs). Set [render] font_path in the "
            "channel profile to a font covering this language."
        )


def _wrap(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int
) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_w or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _draft_watermark(img: Image.Image) -> None:
    w, h = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = ImageFont.truetype(str(bundled_font_path(bold=True)), max(24, w // 8))
    text = "DRAFT"
    tw = draw.textlength(text, font=font)
    draw.text(((w - tw) / 2, h * 0.38), text, font=font, fill=(255, 255, 255, 56))
    rotated = layer.rotate(-20, resample=Image.BICUBIC)
    img.paste(rotated, (0, 0), rotated)


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


class SlidesVisualProvider:
    """Styled text-slides: one PNG per segment (spec 03)."""

    name = "slides"

    def make_slide(
        self,
        profile: ChannelProfile,
        heading: str,
        narration: str,
        index: int,
        total: int,
        draft: bool,
    ) -> bytes:
        w, h = profile.resolution
        style = STYLES[profile.style]
        img = Image.new("RGB", (w, h), style.bg)
        draw = ImageDraw.Draw(img)
        margin = w // 12

        # accent bar + heading
        draw.rectangle([margin, h * 0.16, margin + w // 60, h * 0.16 + h // 9], fill=style.accent)
        heading_font = load_font(profile, max(12, h // 12), bold=True)
        draw.text((margin + w // 30, h * 0.16), heading[:60], font=heading_font, fill=style.fg)

        # body: first sentences of the narration
        body_font = load_font(profile, max(10, h // 22))
        body = narration if len(narration) <= 220 else narration[:217] + "..."
        y = h * 0.38
        for line in _wrap(draw, body, body_font, w - 2 * margin)[:6]:
            draw.text((margin, y), line, font=body_font, fill=style.muted)
            y += h // 16

        # footer
        footer_font = load_font(profile, max(8, h // 30))
        draw.text((margin, h * 0.9), f"{index + 1} / {total}", font=footer_font, fill=style.accent)

        if draft:
            _draft_watermark(img)
        return _png(img)

    def make_thumbnail(
        self, profile: ChannelProfile, text: str, emotion: str, draft: bool
    ) -> bytes:
        """1280x720, <=5 words, legible small (spec 04)."""
        w, h = 1280, 720
        style = STYLES[profile.style]
        img = Image.new("RGB", (w, h), style.bg)
        draw = ImageDraw.Draw(img)
        # accent field for contrast
        draw.rectangle([0, h * 0.72, w, h], fill=style.accent)
        words = text.split()[:5]
        font = ImageFont.truetype(
            str(Path(profile.font_path) if profile.font_path else bundled_font_path(bold=True)),
            150,
        )
        # shrink until it fits
        while font.size > 40:
            lines = _wrap(draw, " ".join(words), font, w - 160)
            if len(lines) <= 3 and all(draw.textlength(ln, font=font) <= w - 160 for ln in lines):
                break
            font = font.font_variant(size=font.size - 10)
        y = 80
        for ln in lines:
            draw.text((80, y), ln, font=font, fill=style.fg)
            y += font.size + 18
        small = ImageFont.truetype(str(bundled_font_path(bold=True)), 48)
        draw.text((80, h * 0.78), emotion.upper()[:24], font=small, fill=style.bg)
        if draft:
            _draft_watermark(img)
        return _png(img)
