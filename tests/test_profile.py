import pytest

from pvfactory.errors import ConfigError
from pvfactory.profile import load_profile


def test_tiny_profile_parses(tiny_profile):
    p = load_profile(tiny_profile)
    assert p.channel_id == "test-channel"
    assert p.resolution == (320, 180)
    assert p.fps == 10
    assert p.providers["tts"] == "tone"


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("schema_version = 1\n[channel]\nid='x'\nname='x'\nniche='x'\naudience='x'\nbogus='y'",
         "unknown key"),
        ("schema_version = 2\n[channel]\nid='x'\nname='x'\nniche='x'\naudience='x'",
         "schema_version"),
        ("schema_version = 1\n[channel]\nid='x'\nname='x'\nniche='x'\naudience='x'\n"
         "[content]\nstyle='vaporwave'", "style"),
        ("schema_version = 1\n[channel]\nid='x'\nname='x'\nniche='x'\naudience='x'\n"
         "[render]\nresolution='huge'", "resolution"),
        ("schema_version = 1\n[channel]\nname='x'\nniche='x'\naudience='x'", "missing required"),
    ],
)
def test_bad_profiles_rejected(tmp_path, mutation, match):
    p = tmp_path / "bad.toml"
    p.write_text(mutation, "utf-8")
    with pytest.raises(ConfigError, match=match):
        load_profile(p)
