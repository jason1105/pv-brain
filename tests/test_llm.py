"""Shared parse/validate layer + MockLLM invariants (never exact strings)."""

import pytest

from pvfactory.errors import ValidationError
from pvfactory.llm import MockLLM, call_llm, extract_json, validate_schema
from pvfactory.pipeline import BRIEF_SCHEMA, METADATA_SCHEMA, SCRIPT_SCHEMA
from pvfactory.profile import ChannelProfile
from pvfactory.prompts import brief_prompt, metadata_prompt, script_prompt

PROFILE = ChannelProfile(
    channel_id="c", name="C", niche="tech", audience="learners", video_minutes_target=2
)


def test_extract_json_from_noisy_text():
    assert extract_json('Sure! {"a": {"b": "with } brace"}} trailing') == {
        "a": {"b": "with } brace"}
    }


@pytest.mark.parametrize("text", ["no json here", "{broken", '{"unterminated": "'])
def test_extract_json_rejects_garbage(text):
    with pytest.raises(ValidationError):
        extract_json(text)


def test_validate_schema_rejects_missing_and_empty():
    with pytest.raises(ValidationError, match="missing required"):
        validate_schema({}, {"title": str})
    with pytest.raises(ValidationError, match="non-empty string"):
        validate_schema({"title": "  "}, {"title": str})
    with pytest.raises(ValidationError, match="non-empty list"):
        validate_schema({"tags": []}, {"tags": list})


def test_mock_llm_deterministic_and_schema_valid():
    llm = MockLLM()
    brief_p = brief_prompt(PROFILE, "why ssds die")
    one = call_llm(llm, brief_p, BRIEF_SCHEMA, seed=42)
    two = call_llm(llm, brief_p, BRIEF_SCHEMA, seed=42)
    other = call_llm(llm, brief_p, BRIEF_SCHEMA, seed=43)
    assert one == two
    assert one != other  # seed actually matters
    assert 1 <= len(one["thumbnail_text"].split()) <= 5


def test_mock_script_invariants():
    llm = MockLLM()
    script = call_llm(llm, script_prompt(PROFILE, "why ssds die", "angle"), SCRIPT_SCHEMA, 42)
    segments = script["segments"]
    assert len(segments) >= 3
    assert segments[0]["role"] == "hook"
    assert segments[-1]["role"] == "cta"
    assert all(seg["narration"].strip() for seg in segments)
    assert any(seg["role"] == "re_engage" for seg in segments)


def test_mock_metadata_invariants():
    llm = MockLLM()
    meta = call_llm(llm, metadata_prompt(PROFILE, "why ssds die", "t"), METADATA_SCHEMA, 42)
    assert len(meta["title"]) <= 100
    assert len(meta["tags"]) >= 4
