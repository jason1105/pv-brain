"""Real LLM providers: Anthropic, Volcengine Ark (Doubao), Gemini.

Thin HTTP adapters (stdlib urllib, no SDKs). They contain NO parsing logic
of their own beyond lifting the text out of the response envelope - all
content parsing flows through the shared layer in llm.py (spec 03). The
transport is injectable so contract tests drive canned real-shaped
responses through this exact code without network or keys.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable

from .errors import ConfigError, StepError
from .llm import LLMProvider

HTTP_TIMEOUT_S = 120

# transport: (url, headers, payload) -> decoded JSON dict
Transport = Callable[[str, dict[str, str], dict], dict]


def _urllib_transport(url: str, headers: dict[str, str], payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise StepError("<llm>", f"HTTP {e.code} from {url}: {detail}") from e
    except urllib.error.URLError as e:
        raise StepError("<llm>", f"cannot reach {url}: {e.reason}") from e


def _require_env(name: str, provider: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(
            f"provider {provider!r} needs the {name} environment variable. "
            f"Set it, choose another [providers] llm, or run with --offline."
        )
    return value


class _HttpLLM(LLMProvider):
    ENV_KEY = ""  # subclasses set the env var carrying the API key

    def __init__(self, model: str, transport: Transport | None = None):
        if not model:
            raise ConfigError(
                f"provider {self.name!r} needs [providers] llm_model in the channel profile"
            )
        self.model = model
        # fail at provider resolution (step 0), not mid-pipeline
        self._key = _require_env(self.ENV_KEY, self.name)
        self._transport = transport or _urllib_transport

    def _lift(self, resp: dict) -> str:
        """Extract the assistant text from the provider's response envelope."""
        raise NotImplementedError

    def _request(self, prompt: str) -> tuple[str, dict[str, str], dict]:
        raise NotImplementedError

    def complete(self, prompt: str, seed: int) -> str:
        url, headers, payload = self._request(prompt)
        resp = self._transport(url, headers, payload)
        try:
            text = self._lift(resp)
        except (KeyError, IndexError, TypeError) as e:
            raise StepError(
                "<llm>", f"unexpected {self.name} response shape: {type(e).__name__}: {e}"
            ) from e
        if not isinstance(text, str) or not text.strip():
            raise StepError("<llm>", f"{self.name} returned an empty completion")
        return text


class AnthropicLLM(_HttpLLM):
    name = "anthropic"
    ENV_KEY = "ANTHROPIC_API_KEY"
    URL = "https://api.anthropic.com/v1/messages"

    def _request(self, prompt: str) -> tuple[str, dict[str, str], dict]:
        headers = {"x-api-key": self._key, "anthropic-version": "2023-06-01"}
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        return self.URL, headers, payload

    def _lift(self, resp: dict) -> str:
        return "".join(
            part.get("text", "") for part in resp["content"] if part.get("type") == "text"
        )


class ArkLLM(_HttpLLM):
    """Volcengine Ark (Doubao) - OpenAI-compatible chat completions."""

    name = "ark"
    ENV_KEY = "ARK_API_KEY"
    DEFAULT_BASE = "https://ark.cn-beijing.volces.com/api/v3"

    def _request(self, prompt: str) -> tuple[str, dict[str, str], dict]:
        base = os.environ.get("ARK_BASE_URL", self.DEFAULT_BASE).rstrip("/")
        headers = {"authorization": f"Bearer {self._key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        return f"{base}/chat/completions", headers, payload

    def _lift(self, resp: dict) -> str:
        return resp["choices"][0]["message"]["content"]


class GeminiLLM(_HttpLLM):
    name = "gemini"
    ENV_KEY = "GEMINI_API_KEY"
    BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def _request(self, prompt: str) -> tuple[str, dict[str, str], dict]:
        # key goes in a header, never in the URL (it would leak into logs)
        headers = {"x-goog-api-key": self._key}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        return f"{self.BASE}/{self.model}:generateContent", headers, payload

    def _lift(self, resp: dict) -> str:
        parts = resp["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)
