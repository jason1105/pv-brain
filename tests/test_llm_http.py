"""Contract tests for real LLM adapters (spec 05): canned real-shaped API
responses driven through the exact production parsing code via an injected
transport. No network, no keys - the untested surface is the HTTP call only.
"""

import json

import pytest

from pvfactory.errors import ConfigError, StepError
from pvfactory.llm import call_llm
from pvfactory.llm_http import AnthropicLLM, ArkLLM, GeminiLLM
from pvfactory.pipeline import BRIEF_SCHEMA
from pvfactory.profile import ChannelProfile
from pvfactory.prompts import brief_prompt

PROFILE = ChannelProfile(channel_id="c", name="C", niche="tech", audience="learners")

BRIEF_JSON = json.dumps(
    {
        "angle": "the counterintuitive truth",
        "working_title": "T",
        "audience_intent": "learn",
        "thumbnail_text": "The Truth",
        "thumbnail_emotion": "surprise",
    }
)

# Real response envelope shapes, per each vendor's API docs.
ANTHROPIC_RESP = {
    "id": "msg_01",
    "type": "message",
    "role": "assistant",
    "content": [{"type": "text", "text": f"Here is the JSON:\n{BRIEF_JSON}"}],
    "model": "claude-sonnet-5",
    "stop_reason": "end_turn",
    "usage": {"input_tokens": 10, "output_tokens": 50},
}
ARK_RESP = {
    "id": "chatcmpl-01",
    "object": "chat.completion",
    "model": "doubao-pro-32k",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": BRIEF_JSON},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 50},
}
GEMINI_RESP = {
    "candidates": [
        {
            "content": {"parts": [{"text": BRIEF_JSON}], "role": "model"},
            "finishReason": "STOP",
        }
    ],
    "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 50},
}


def _transport(canned, captured):
    def post(url, headers, payload):
        captured.update({"url": url, "headers": headers, "payload": payload})
        return canned

    return post


@pytest.mark.parametrize(
    "cls,env,canned,url_part",
    [
        (AnthropicLLM, "ANTHROPIC_API_KEY", ANTHROPIC_RESP, "api.anthropic.com"),
        (ArkLLM, "ARK_API_KEY", ARK_RESP, "volces.com"),
        (GeminiLLM, "GEMINI_API_KEY", GEMINI_RESP, "generativelanguage"),
    ],
)
def test_adapter_lifts_text_through_shared_parse_layer(monkeypatch, cls, env, canned, url_part):
    monkeypatch.setenv(env, "test-key")
    captured = {}
    llm = cls("some-model", transport=_transport(canned, captured))
    obj = call_llm(llm, brief_prompt(PROFILE, "why ssds die"), BRIEF_SCHEMA, seed=1)
    assert obj["angle"] == "the counterintuitive truth"
    assert url_part in captured["url"]
    # the key must be in a header, never in the URL (it would leak into logs)
    assert "test-key" not in captured["url"]
    assert any("test-key" in v for v in captured["headers"].values())


@pytest.mark.parametrize(
    "cls,env",
    [
        (AnthropicLLM, "ANTHROPIC_API_KEY"),
        (ArkLLM, "ARK_API_KEY"),
        (GeminiLLM, "GEMINI_API_KEY"),
    ],
)
def test_missing_key_is_actionable_config_error(monkeypatch, cls, env):
    monkeypatch.delenv(env, raising=False)
    with pytest.raises(ConfigError, match=env):  # at construction = step 0
        cls("some-model", transport=_transport({}, {}))


def test_missing_model_is_config_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    with pytest.raises(ConfigError, match="llm_model"):
        AnthropicLLM("")


def test_unexpected_response_shape_is_step_error(monkeypatch):
    monkeypatch.setenv("ARK_API_KEY", "test-key")
    llm = ArkLLM("m", transport=_transport({"choices": []}, {}))
    with pytest.raises(StepError, match="response shape"):
        llm.complete("x", seed=1)


def test_empty_completion_is_step_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    resp = {"candidates": [{"content": {"parts": [{"text": "   "}]}}]}
    llm = GeminiLLM("m", transport=_transport(resp, {}))
    with pytest.raises(StepError, match="empty completion"):
        llm.complete("x", seed=1)


def test_ark_base_url_override(monkeypatch):
    monkeypatch.setenv("ARK_API_KEY", "test-key")
    monkeypatch.setenv("ARK_BASE_URL", "https://ark.example.com/api/v3/")
    captured = {}
    llm = ArkLLM("m", transport=_transport(ARK_RESP, captured))
    llm.complete("x", seed=1)
    assert captured["url"] == "https://ark.example.com/api/v3/chat/completions"
