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
from .manifest import MANIFEST_NAME, Manifest
from .pipeline import build_workflow
from .profile import ChannelProfile, load_profile
from .publish import DryRunPublisher
from .render import FfmpegRenderer
from .tts import OFFLINE_TTS
from .visuals import SlidesVisualProvider, validate_glyph_coverage

PROFILE_SNAPSHOT = "profile.toml"


def slugify(text: str, max_len: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "video"


def resolve_providers(profile: ChannelProfile, offline: bool) -> dict:
    """ADR-0005: offline content providers are never selected silently."""
    if not offline:
        raise ConfigError(
            "real content providers (LLM/TTS) arrive in milestone M3. "
            "Until then, run with --offline to produce a clearly-labeled draft."
        )
    tts_name = str(profile.providers.get("tts", "tone"))
    if tts_name not in OFFLINE_TTS:
        raise ConfigError(
            f"offline runs support tts providers {sorted(OFFLINE_TTS)}, got {tts_name!r}"
        )
    wpm = profile.providers.get("tts_wpm", 150)
    if not isinstance(wpm, int):
        raise ConfigError("[providers] tts_wpm must be an integer")
    return {
        "llm": MockLLM(),
        "tts": OFFLINE_TTS[tts_name](wpm=wpm),
        "visuals": SlidesVisualProvider(),
        "renderer": FfmpegRenderer(),
        "publisher": DryRunPublisher(),
    }


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
    providers = resolve_providers(profile, offline)
    draft = offline  # every offline run is a draft (ADR-0005)

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
    topic_ref = store.put_text("topic.txt", topic)

    manifest = Manifest(
        run_id=run_id,
        channel_id=profile.channel_id,
        workflow="produce-video",
        draft=draft,
        seed=seed,
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

    LocalChannelStore(output_root / "channels.json").record_topic(
        profile.channel_id, topic, run_id
    )
    return pkg_dir


def find_run(output_root: Path, run_id: str) -> Path:
    """Locate a run's package directory by run_id."""
    for manifest_path in output_root.glob(f"*/*/{MANIFEST_NAME}"):
        store = LocalArtifactStore(manifest_path.parent)
        try:
            if Manifest.load(store).run_id == run_id:
                return manifest_path.parent
        except (ValueError, KeyError):
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
    providers = resolve_providers(profile, offline=manifest.draft)
    ctx = RunContext(
        store=store,
        profile=profile,
        providers=providers,
        seed=manifest.seed,
        draft=manifest.draft,
        artifacts={"topic": "artifact://topic.txt"},
    )
    Runner(build_workflow(), ctx, manifest).run(log)
    return pkg_dir
