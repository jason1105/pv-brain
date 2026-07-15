"""Provider registry + draft semantics (ADR-0005) and resume mode fidelity."""

import pytest

from pvfactory.errors import ConfigError
from pvfactory.llm import MockLLM
from pvfactory.llm_http import ArkLLM
from pvfactory.profile import ChannelProfile
from pvfactory.runs import resolve_providers
from pvfactory.tts import ToneTTS


def _profile(**providers):
    return ChannelProfile(
        channel_id="c", name="C", niche="tech", audience="learners", providers=providers
    )


def test_offline_resolves_mock_and_offline_tts_as_draft():
    providers, draft = resolve_providers(_profile(tts="tone"), offline=True)
    assert isinstance(providers["llm"], MockLLM)
    assert isinstance(providers["tts"], ToneTTS)
    assert draft is True


def test_offline_never_reaches_for_network_tts():
    providers, draft = resolve_providers(_profile(tts="edge"), offline=True)
    assert isinstance(providers["tts"], ToneTTS)
    assert draft is True


def test_online_without_llm_config_is_actionable_error():
    with pytest.raises(ConfigError, match="providers"):
        resolve_providers(_profile(), offline=False)


def test_online_mock_llm_rejected():
    # ADR-0005: the mock is never selected without explicit --offline
    with pytest.raises(ConfigError):
        resolve_providers(_profile(llm="mock"), offline=False)


def test_online_real_llm_with_offline_tts_is_still_draft(monkeypatch):
    monkeypatch.setenv("ARK_API_KEY", "k")
    providers, draft = resolve_providers(
        _profile(llm="ark", llm_model="doubao-pro", tts="tone"), offline=False
    )
    assert isinstance(providers["llm"], ArkLLM)
    assert draft is True  # any offline content provider => draft


def test_unknown_providers_rejected():
    with pytest.raises(ConfigError, match="unknown llm"):
        resolve_providers(_profile(llm="skynet"), offline=False)
    with pytest.raises(ConfigError, match="unknown tts"):
        resolve_providers(
            _profile(llm="anthropic", llm_model="m", tts="shout"), offline=False
        )
