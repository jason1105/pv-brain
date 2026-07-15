"""Prompt construction for LLM steps.

Each prompt carries a `prompt_ref` pointing at its source template in
docs/prompts/ so the repo's Prompt layer and the runtime stay one system
(docs/specs/02). The TASK/TOPIC header lines are a machine-readable contract
consumed by offline providers and ignored by real ones.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .profile import ChannelProfile


@dataclass(frozen=True)
class Prompt:
    task: str
    text: str
    prompt_ref: str

    @property
    def prompt_hash(self) -> str:
        return "sha256:" + hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def _header(task: str, topic: str) -> str:
    return f"TASK: {task}\nTOPIC: {topic}\n\n"


def brief_prompt(profile: ChannelProfile, topic: str) -> Prompt:
    text = _header("brief", topic) + (
        f"Create a faceless YouTube video concept for a {profile.niche} channel "
        f"targeting {profile.audience}, on the topic: {topic}.\n"
        f"Tone: {profile.tone}. Language: {profile.language}.\n\n"
        "Return ONLY a JSON object with keys:\n"
        '  "angle" (string): the specific angle that makes this clickable,\n'
        '  "working_title" (string),\n'
        '  "audience_intent" (string): what the viewer wants from this video,\n'
        '  "thumbnail_text" (string): 3-5 words for the thumbnail,\n'
        '  "thumbnail_emotion" (string).\n'
    )
    return Prompt("brief", text, "docs/prompts/youtube/production.md#faceless-video-concept")


def script_prompt(profile: ChannelProfile, topic: str, angle: str) -> Prompt:
    text = _header("script", topic) + (
        f"Write a HIGH-RETENTION YouTube narration script about {topic} "
        f"for {profile.audience}, angle: {angle}. "
        f"Target length: {profile.video_minutes_target} minutes. "
        f"Tone: {profile.tone}. Language: {profile.language}.\n\n"
        "Hook in the first sentence, open loops, a re-engagement beat, and a "
        "natural CTA at the end.\n\n"
        "Return ONLY a JSON object with keys:\n"
        '  "segments": list of objects, each with\n'
        '     "role" (one of "hook", "body", "re_engage", "cta"),\n'
        '     "heading" (string, short),\n'
        '     "narration" (string, the spoken text),\n'
        '     "visual_intent" (string, what should be on screen).\n'
        "The first segment must be role=hook and the last role=cta.\n"
    )
    return Prompt("script", text, "docs/prompts/youtube/production.md#high-retention-script")


def metadata_prompt(profile: ChannelProfile, topic: str, working_title: str) -> Prompt:
    text = _header("metadata", topic) + (
        f"Package a YouTube video about {topic} (working title: {working_title}) "
        f"for a {profile.niche} channel targeting {profile.audience}.\n\n"
        "Return ONLY a JSON object with keys:\n"
        '  "title" (string, <=100 chars, click-optimized),\n'
        '  "description" (string, 2-3 short paragraphs),\n'
        '  "tags" (list of 8-15 strings),\n'
        '  "category" (string).\n'
    )
    return Prompt("metadata", text, "docs/prompts/youtube/packaging.md#viral-title-generator")
