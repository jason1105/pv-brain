"""LLM providers and the shared parse-and-validate layer.

Binding contract (docs/specs/03): ALL LLM output - mock and real alike -
flows through `call_llm`, so CI exercises the exact parsing code production
uses. Providers return raw text; nothing else.
"""

from __future__ import annotations

import json
import random
import re
from abc import ABC, abstractmethod

from .errors import ValidationError
from .prompts import Prompt

# --- schema validation (deliberately small: required keys + types) ---------

Schema = dict[str, type | tuple]


def extract_json(text: str) -> dict:
    """Extract the first JSON *object* from possibly-noisy LLM output.

    Prose may contain stray braces (e.g. "the {topic} JSON"), so every '{'
    is a candidate and the real parser decides - never a hand-rolled scan.
    """
    decoder = json.JSONDecoder()
    start = text.find("{")
    while start != -1:
        try:
            obj, _ = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
            continue
        if isinstance(obj, dict):
            return obj
        start = text.find("{", start + 1)
    raise ValidationError("LLM output contains no valid JSON object")


def validate_schema(obj: dict, schema: Schema) -> dict:
    for key, expected in schema.items():
        if key not in obj:
            raise ValidationError(f"LLM output missing required key {key!r}")
        value = obj[key]
        if expected is list or isinstance(expected, tuple) and expected[0] is list:
            if not isinstance(value, list) or not value:
                raise ValidationError(f"LLM output key {key!r} must be a non-empty list")
        elif expected is str:
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"LLM output key {key!r} must be a non-empty string")
        elif not isinstance(value, expected):
            raise ValidationError(f"LLM output key {key!r} has wrong type")
    return obj


class LLMProvider(ABC):
    name: str = "abstract"
    model: str = ""

    @abstractmethod
    def complete(self, prompt: str, seed: int) -> str: ...


def call_llm(provider: LLMProvider, prompt: Prompt, schema: Schema, seed: int) -> dict:
    """The one path from any provider to the pipeline."""
    raw = provider.complete(prompt.text, seed)
    return validate_schema(extract_json(raw), schema)


# --- deterministic offline provider ----------------------------------------


def _prompt_field(prompt: str, field: str) -> str:
    m = re.search(rf"^{field}: (.*)$", prompt, re.MULTILINE)
    return m.group(1).strip() if m else ""


class MockLLM(LLMProvider):
    """Seeded, deterministic content generator (ADR-0005: drafts only).

    Reads the TASK/TOPIC header contract from the prompt and emits JSON
    wrapped in prose, so the shared extract/validate path is exercised the
    same way a real model's output would be.
    """

    name = "mock"
    model = "mock-deterministic-v1"

    _ANGLES = [
        "the counterintuitive truth nobody mentions",
        "what insiders actually do differently",
        "the mistake almost everyone makes first",
        "the 5 facts that change how you see it",
    ]
    _HOOKS = [
        "Everything you think you know about {t} is about to change.",
        "Nobody tells you this about {t} - until it costs you.",
        "In the next few minutes, {t} will finally make sense.",
    ]
    _BODIES = [
        "Here is the part about {t} that surprises everyone. {x}",
        "Most people get {t} wrong for one simple reason. {x}",
        "The data behind {t} tells a different story. {x}",
        "There is a pattern in {t} that professionals rely on. {x}",
    ]
    _FILL = [
        "Once you see it, you cannot unsee it.",
        "And it changes what you should do next.",
        "The details matter more than the headline.",
        "This is where it gets interesting.",
    ]

    def complete(self, prompt: str, seed: int) -> str:
        task = _prompt_field(prompt, "TASK")
        topic = _prompt_field(prompt, "TOPIC") or "this topic"
        rng = random.Random(f"{seed}:{task}:{topic}")
        make = {
            "brief": self._brief,
            "script": self._script,
            "metadata": self._metadata,
        }.get(task)
        if make is None:
            raise ValidationError(f"MockLLM does not understand TASK {task!r}")
        obj = make(rng, topic, prompt)
        # Wrap in prose so extraction is genuinely exercised.
        return f"Sure - here is the JSON you asked for:\n\n{json.dumps(obj, ensure_ascii=False)}\n"

    def _brief(self, rng: random.Random, topic: str, prompt: str) -> dict:
        words = [w.strip(".,!?").title() for w in topic.split()[:4]]
        return {
            "angle": rng.choice(self._ANGLES),
            "working_title": f"{' '.join(words)}: What Nobody Tells You",
            "audience_intent": f"understand {topic} without the jargon",
            "thumbnail_text": " ".join(words[:3]) or "The Truth",
            "thumbnail_emotion": rng.choice(["surprise", "curiosity", "urgency"]),
        }

    def _script(self, rng: random.Random, topic: str, prompt: str) -> dict:
        m = re.search(r"Target length: (\d+) minutes", prompt)
        minutes = int(m.group(1)) if m else 5
        n_body = max(2, min(8, minutes + 1))
        segments = [
            {
                "role": "hook",
                "heading": "Hook",
                "narration": rng.choice(self._HOOKS).format(t=topic),
                "visual_intent": f"bold title card about {topic}",
            }
        ]
        for i in range(n_body):
            if i == n_body // 2:
                segments.append(
                    {
                        "role": "re_engage",
                        "heading": "But wait",
                        "narration": f"And if you think that is all there is to {topic}, "
                        "the next part is the reason you clicked.",
                        "visual_intent": "pattern interrupt, contrasting slide",
                    }
                )
            segments.append(
                {
                    "role": "body",
                    "heading": f"Point {i + 1}",
                    "narration": rng.choice(self._BODIES).format(t=topic, x=rng.choice(self._FILL)),
                    "visual_intent": f"key point {i + 1} with supporting text",
                }
            )
        segments.append(
            {
                "role": "cta",
                "heading": "What next",
                "narration": "If this changed how you think, subscribe - the next video "
                "goes one level deeper.",
                "visual_intent": "subscribe call to action",
            }
        )
        return {"segments": segments}

    def _metadata(self, rng: random.Random, topic: str, prompt: str) -> dict:
        words = [w.strip(".,!?") for w in topic.lower().split()]
        title = f"{topic.title()} - What Nobody Tells You"
        return {
            "title": title[:100],
            "description": (
                f"The honest breakdown of {topic}: what matters, what does not, "
                "and what to do about it.\n\n"
                "New videos every week on this channel."
            ),
            "tags": list(dict.fromkeys(words + ["explainer", "guide", "facts", "explained"]))[:15],
            "category": "Education",
        }
