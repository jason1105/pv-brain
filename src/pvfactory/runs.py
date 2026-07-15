"""Run orchestration: the engine's pure-function entry point (ADR-0004).

The CLI is a thin shell over `produce_video` / `resume_run` - no TTY, no
interactivity, everything via arguments.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import re
import shutil
from collections.abc import Callable
from pathlib import Path

from .artifacts import LocalArtifactStore
from .channelstore import LocalChannelStore
from .engine import RunContext, Runner
from .errors import ConfigError
from .llm import MockLLM
from .llm_http import AnthropicLLM, ArkLLM, GeminiLLM
from .manifest import MANIFEST_NAME, Manifest
from .pipeline import build_workflow
from .profile import ChannelProfile, load_profile
from .publish import DryRunPublisher
from .render import FfmpegRenderer
from .tts import OFFLINE_TTS
from .visuals import SlidesVisualProvider, validate_glyph_coverage

PROFILE_SNAPSHOT = "profile.toml"
TOPIC_ARTIFACT = "topic.txt"


def slugify(text: str, max_len: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "video"


# Registries (spec 03: "the registry is a plain dict"). Factories take the
# profile and return a provider instance; construction validates env keys.

LLM_FACTORIES: dict[str, Callable[[ChannelProfile], object]] = {
    "mock": lambda p: MockLLM(),
    "anthropic": lambda p: AnthropicLLM(str(p.providers.get("llm_model", ""))),
    "ark": lambda p: ArkLLM(str(p.providers.get("llm_model", ""))),
    "gemini": lambda p: GeminiLLM(str(p.providers.get("llm_model", ""))),
}


def _make_offline_tts(profile: ChannelProfile, name: str):
    wpm = profile.providers.get("tts_wpm", 150)
    if not isinstance(wpm, int):
        raise ConfigError("[providers] tts_wpm must be an integer")
    return OFFLINE_TTS[name](wpm=wpm)


def _make_edge_tts(profile: ChannelProfile):
    from .tts_edge import DEFAULT_VOICE, EdgeTTS  # optional dependency

    return EdgeTTS(voice=str(profile.providers.get("tts_voice", DEFAULT_VOICE)))


TTS_FACTORIES: dict[str, Callable[[ChannelProfile], object]] = {
    **{name: (lambda p, _n=name: _make_offline_tts(p, _n)) for name in OFFLINE_TTS},
    "edge": _make_edge_tts,
}

OFFLINE_LLMS = {"mock"}


def resolve_providers(profile: ChannelProfile, offline: bool) -> tuple[dict, bool]:
    """Returns (providers, draft). ADR-0005: offline content providers are
    never selected silently - the mock LLM requires --offline; a run using
    ANY offline content provider is a draft."""
    if offline:
        llm_name = "mock"
        tts_name = str(profile.providers.get("tts", "tone"))
        if tts_name not in OFFLINE_TTS:
            tts_name = "tone"  # offline runs never reach for the network
    else:
        llm_name = str(profile.providers.get("llm", "")).strip()
        if not llm_name or llm_name in OFFLINE_LLMS:
            options = sorted(set(LLM_FACTORIES) - OFFLINE_LLMS)
            raise ConfigError(
                f"set [providers] llm to one of {options} in the channel profile "
                "(each needs its API key env var), or run with --offline for a draft."
            )
        tts_name = str(profile.providers.get("tts", "edge"))

    if llm_name not in LLM_FACTORIES:
        raise ConfigError(f"unknown llm provider {llm_name!r}; options: {sorted(LLM_FACTORIES)}")
    if tts_name not in TTS_FACTORIES:
        raise ConfigError(f"unknown tts provider {tts_name!r}; options: {sorted(TTS_FACTORIES)}")

    providers = {
        "llm": LLM_FACTORIES[llm_name](profile),
        "tts": TTS_FACTORIES[tts_name](profile),
        "visuals": SlidesVisualProvider(),
        "renderer": FfmpegRenderer(),
        "publisher": DryRunPublisher(),
    }
    draft = llm_name in OFFLINE_LLMS or tts_name in OFFLINE_TTS
    return providers, draft


def _make_run_id(topic: str, seed: int) -> str:
    stamp = _dt.datetime.now(_dt.UTC).strftime("%Y%m%d-%H%M%S")
    digest = hashlib.sha256(f"{topic}:{seed}:{stamp}".encode()).hexdigest()[:6]
    return f"run-{stamp}-{digest}"


def produce_video(
    profile_path: Path,
    topic: str,
    output_root: Path,
    offline: bool,
    seed: int,
    log: Callable[[str], None] = lambda _: None,
) -> Path:
    """Produce one video package; returns the package directory."""
    profile = load_profile(profile_path)
    validate_glyph_coverage(profile)
    providers, draft = resolve_providers(profile, offline)

    seed = int(seed)
    run_id = _make_run_id(topic, seed)
    date = _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%d")
    prefix = "DRAFT-" if draft else ""
    pkg_dir = output_root / profile.channel_id / f"{prefix}{date}-{slugify(topic)}"
    n = 2
    while pkg_dir.exists():
        pkg_dir = output_root / profile.channel_id / f"{prefix}{date}-{slugify(topic)}-{n}"
        n += 1

    store = LocalArtifactStore(pkg_dir)
    shutil.copy(profile_path, pkg_dir / PROFILE_SNAPSHOT)  # resume needs the profile
    topic_ref = store.put_text(TOPIC_ARTIFACT, topic)

    manifest = Manifest(
        run_id=run_id,
        channel_id=profile.channel_id,
        workflow="produce-video",
        draft=draft,
        seed=seed,
        offline=offline,
    )
    ctx = RunContext(
        store=store,
        profile=profile,
        providers=providers,
        seed=seed,
        draft=draft,
        artifacts={"topic": topic_ref},
    )
    runner = Runner(build_workflow(), ctx, manifest)
    manifest.save(store)
    runner.run(log)
    _record_topic(output_root, profile.channel_id, topic, run_id)
    return pkg_dir


def _record_topic(output_root: Path, channel_id: str, topic: str, run_id: str) -> None:
    LocalChannelStore(output_root / "channels.json").record_topic(channel_id, topic, run_id)


def find_run(output_root: Path, run_id: str) -> Path:
    """Locate a run's package directory by run_id. Foreign or corrupt
    manifest.json files under the output root are skipped, never fatal."""
    for manifest_path in output_root.rglob(MANIFEST_NAME):
        store = LocalArtifactStore(manifest_path.parent)
        try:
            if Manifest.load(store).run_id == run_id:
                return manifest_path.parent
        except Exception:  # noqa: BLE001 - any unreadable manifest is not ours
            continue
    raise ConfigError(f"no run with id {run_id!r} under {output_root}")


def resume_run(
    output_root: Path, run_id: str, log: Callable[[str], None] = lambda _: None
) -> Path:
    """Resume a failed/interrupted run from its last completed step."""
    pkg_dir = find_run(output_root, run_id)
    store = LocalArtifactStore(pkg_dir)
    manifest = Manifest.load(store)
    profile = load_profile(pkg_dir / PROFILE_SNAPSHOT)
    # resume reconstructs the original provider MODE from the manifest,
    # not from the draft label (a real-LLM + offline-TTS run is a draft
    # but must not resume all-mock)
    providers, _ = resolve_providers(profile, offline=manifest.offline)
    ctx = RunContext(
        store=store,
        profile=profile,
        providers=providers,
        seed=manifest.seed,
        draft=manifest.draft,
        artifacts={"topic": f"artifact://{TOPIC_ARTIFACT}"},
    )
    Runner(build_workflow(), ctx, manifest).run(log)
    # runs finished via resume must reach topic history too (record_topic
    # dedupes by run_id, so resuming an already-recorded run is a no-op)
    topic = store.get_text(f"artifact://{TOPIC_ARTIFACT}")
    _record_topic(output_root, manifest.channel_id, topic, manifest.run_id)
    return pkg_dir
