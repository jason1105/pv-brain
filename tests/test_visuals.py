from io import BytesIO

import pytest
from PIL import Image

from pvfactory.errors import ConfigError
from pvfactory.profile import ChannelProfile
from pvfactory.visuals import SlidesVisualProvider, validate_glyph_coverage

PROFILE = ChannelProfile(
    channel_id="c", name="C", niche="tech", audience="learners", width=320, height=180
)


def _img(png: bytes) -> Image.Image:
    return Image.open(BytesIO(png))


def test_slide_dimensions_and_draft_watermark_differs():
    slides = SlidesVisualProvider()
    plain = slides.make_slide(PROFILE, "Heading", "Some narration text.", 0, 3, draft=False)
    draft = slides.make_slide(PROFILE, "Heading", "Some narration text.", 0, 3, draft=True)
    assert _img(plain).size == (320, 180)
    assert plain != draft  # watermark visibly changes the render


def test_thumbnail_is_1280x720_max_five_words():
    slides = SlidesVisualProvider()
    png = slides.make_thumbnail(
        PROFILE, "one two three four five six seven", "surprise", draft=False
    )
    assert _img(png).size == (1280, 720)


def test_cjk_profile_without_font_fails_loudly():
    zh = ChannelProfile(
        channel_id="c", name="C", niche="tech", audience="learners", language="zh"
    )
    with pytest.raises(ConfigError, match="font_path"):
        validate_glyph_coverage(zh)


def test_latin_profile_passes_glyph_check():
    validate_glyph_coverage(PROFILE)
