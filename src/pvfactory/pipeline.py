"""The produce-video workflow: 9 steps (docs/workflow/produce-video.md,
docs/specs/02). Validation at every step boundary - the pipeline must never
"succeed" into a broken package.
"""

from __future__ import annotations

from . import prompts
from .engine import RunContext, StepDef, StepResult, Workflow
from .errors import ValidationError
from .llm import call_llm
from .render import FfmpegRenderer, TimelineEntry, build_srt
from .tts import SegmentAudio, concat_wavs

MIN_SEGMENTS = 3
MIN_SEGMENT_SECONDS = 0.3

BRIEF_SCHEMA = {
    "angle": str,
    "working_title": str,
    "audience_intent": str,
    "thumbnail_text": str,
    "thumbnail_emotion": str,
}
SCRIPT_SCHEMA = {"segments": list}
METADATA_SCHEMA = {"title": str, "description": str, "tags": list, "category": str}
_ROLES = {"hook", "body", "re_engage", "cta"}


def _provenance(ctx: RunContext, prompt) -> dict:
    llm = ctx.providers["llm"]
    return {
        "provider": llm.name,
        "model": llm.model,
        "prompt_ref": prompt.prompt_ref,
        "prompt_hash": prompt.prompt_hash,
        "seed": ctx.seed,
    }


def _load_json(ctx: RunContext, name: str) -> dict:
    obj = ctx.store.get_json(ctx.artifact(name))
    assert isinstance(obj, dict)
    return obj


# --- steps ------------------------------------------------------------------


def ideate(ctx: RunContext) -> StepResult:
    topic = ctx.store.get_text(ctx.artifact("topic"))
    prompt = prompts.brief_prompt(ctx.profile, topic)
    brief = call_llm(ctx.providers["llm"], prompt, BRIEF_SCHEMA, ctx.seed)
    brief["topic"] = topic
    ref = ctx.store.put_json("brief.json", brief)
    return StepResult({"brief": ref}, _provenance(ctx, prompt))


def write_script(ctx: RunContext) -> StepResult:
    brief = _load_json(ctx, "brief")
    prompt = prompts.script_prompt(ctx.profile, brief["topic"], brief["angle"])
    script = call_llm(ctx.providers["llm"], prompt, SCRIPT_SCHEMA, ctx.seed)

    segments = script["segments"]
    if len(segments) < MIN_SEGMENTS:
        raise ValidationError(f"script has {len(segments)} segments; need >= {MIN_SEGMENTS}")
    for i, seg in enumerate(segments):
        if not isinstance(seg, dict) or not str(seg.get("narration", "")).strip():
            raise ValidationError(f"script segment {i} has empty narration")
        if seg.get("role") not in _ROLES:
            raise ValidationError(f"script segment {i} has invalid role {seg.get('role')!r}")
        seg["id"] = f"seg-{i + 1:03d}"
        seg.setdefault("heading", f"Part {i + 1}")
        seg.setdefault("visual_intent", "")
    if segments[0]["role"] != "hook" or segments[-1]["role"] != "cta":
        raise ValidationError("script must start with a hook and end with a cta")

    doc = {
        "schema_version": 1,
        "topic": brief["topic"],
        "title_working": brief["working_title"],
        "segments": segments,
    }
    ref = ctx.store.put_json("script.json", doc)
    md = [f"# {brief['working_title']}", ""]
    for seg in segments:
        md += [f"## {seg['heading']} ({seg['role']})", "", seg["narration"], ""]
    md_ref = ctx.store.put_text("script.md", "\n".join(md))
    return StepResult({"script": ref, "script_md": md_ref}, _provenance(ctx, prompt))


def synthesize_voice(ctx: RunContext) -> StepResult:
    script = _load_json(ctx, "script")
    tts = ctx.providers["tts"]
    clips: list[SegmentAudio] = tts.synthesize(script["segments"], ctx.seed)
    if len(clips) != len(script["segments"]):
        raise ValidationError("tts returned wrong clip count")
    track = []
    for clip in clips:
        if clip.duration_s < MIN_SEGMENT_SECONDS:
            raise ValidationError(f"segment {clip.segment_id} audio too short")
        ref = ctx.store.put_bytes(f"voice/{clip.segment_id}.wav", clip.wav_bytes)
        track.append({"segment_id": clip.segment_id, "ref": ref, "duration_s": clip.duration_s})
    full_ref = ctx.store.put_bytes("voiceover.wav", concat_wavs([c.wav_bytes for c in clips]))
    doc = {"schema_version": 1, "provider": tts.name, "segments": track}
    ref = ctx.store.put_json("voice_track.json", doc)
    return StepResult(
        {"voice_track": ref, "voiceover": full_ref},
        {"provider": tts.name, "seed": ctx.seed},
    )


def plan_visuals(ctx: RunContext) -> StepResult:
    script = _load_json(ctx, "script")
    voice = _load_json(ctx, "voice_track")
    slides = ctx.providers["visuals"]
    segments = script["segments"]
    entries = []
    for i, (seg, clip) in enumerate(zip(segments, voice["segments"], strict=True)):
        png = slides.make_slide(
            ctx.profile, seg["heading"], seg["narration"], i, len(segments), ctx.draft
        )
        img_ref = ctx.store.put_bytes(f"slides/{seg['id']}.png", png)
        entries.append(
            {
                "segment_id": seg["id"],
                "visual": {"kind": "slide", "asset": img_ref},
                "audio": {"asset": clip["ref"], "duration_s": clip["duration_s"]},
            }
        )
    doc = {"schema_version": 1, "entries": entries}
    ref = ctx.store.put_json("timeline.json", doc)
    return StepResult({"timeline": ref}, {"provider": slides.name})


def render_video(ctx: RunContext) -> StepResult:
    timeline = _load_json(ctx, "timeline")
    renderer: FfmpegRenderer = ctx.providers["renderer"]
    entries = [
        TimelineEntry(
            segment_id=e["segment_id"],
            image_path=ctx.store.path_for(e["visual"]["asset"]),
            duration_s=e["audio"]["duration_s"],
        )
        for e in timeline["entries"]
    ]
    out_path = ctx.store.path_for("artifact://video.mp4")
    duration = renderer.render(
        entries, ctx.store.path_for(ctx.artifact("voiceover")), out_path, fps=ctx.profile.fps
    )
    expected = sum(e.duration_s for e in entries)
    if abs(duration - expected) > max(2.0, expected * 0.1):
        raise ValidationError(
            f"rendered duration {duration:.1f}s deviates from timeline {expected:.1f}s"
        )
    return StepResult({"video": "artifact://video.mp4"}, {"provider": renderer.name})


def make_captions(ctx: RunContext) -> StepResult:
    script = _load_json(ctx, "script")
    voice = _load_json(ctx, "voice_track")
    srt = build_srt(script["segments"], [s["duration_s"] for s in voice["segments"]])
    ref = ctx.store.put_text("captions.srt", srt)
    return StepResult({"captions": ref})


def make_thumbnail(ctx: RunContext) -> StepResult:
    brief = _load_json(ctx, "brief")
    slides = ctx.providers["visuals"]
    png = slides.make_thumbnail(
        ctx.profile, brief["thumbnail_text"], brief["thumbnail_emotion"], ctx.draft
    )
    ref = ctx.store.put_bytes("thumbnail.png", png)
    return StepResult({"thumbnail": ref}, {"provider": slides.name})


def package_metadata(ctx: RunContext) -> StepResult:
    brief = _load_json(ctx, "brief")
    script = _load_json(ctx, "script")
    voice = _load_json(ctx, "voice_track")
    prompt = prompts.metadata_prompt(ctx.profile, brief["topic"], brief["working_title"])
    meta = call_llm(ctx.providers["llm"], prompt, METADATA_SCHEMA, ctx.seed)
    if len(meta["title"]) > 100:
        raise ValidationError("metadata title exceeds 100 chars")

    # Chapters from MEASURED segment timings (spec 04).
    chapters, t = [], 0.0
    for seg, clip in zip(script["segments"], voice["segments"], strict=True):
        m, s = divmod(int(t), 60)
        chapters.append(f"{m:02d}:{s:02d} {seg['heading']}")
        t += clip["duration_s"]
    meta["description"] = meta["description"].rstrip() + "\n\nChapters:\n" + "\n".join(chapters)
    meta["language"] = ctx.profile.language
    meta["draft"] = ctx.draft
    # operator-complete (spec 04): every upload field present, safe default
    meta["visibility"] = "unlisted"

    ref = ctx.store.put_json("metadata.json", meta)
    return StepResult({"metadata": ref}, _provenance(ctx, prompt))


def publish(ctx: RunContext) -> StepResult:
    meta = _load_json(ctx, "metadata")
    publisher = ctx.providers["publisher"]
    result = publisher.publish(
        {
            "metadata": meta,
            "video_name": "video.mp4",
            "thumbnail_name": "thumbnail.png",
            "captions_name": "captions.srt",
            "language": ctx.profile.language,
        }
    )
    checklist = result.pop("checklist", None)
    outputs = {}
    if checklist:
        outputs["publish_checklist"] = ctx.store.put_text("PUBLISH_CHECKLIST.md", checklist)
    outputs["publish_result"] = ctx.store.put_json("publish_result.json", result)
    return StepResult(outputs, {"provider": publisher.name})


def build_workflow() -> Workflow:
    return Workflow(
        name="produce-video",
        initial=("topic",),
        steps=[
            StepDef("ideate", ("topic",), ("brief",), ideate),
            StepDef("write_script", ("brief",), ("script", "script_md"), write_script),
            StepDef(
                "synthesize_voice", ("script",), ("voice_track", "voiceover"), synthesize_voice
            ),
            StepDef("plan_visuals", ("script", "voice_track"), ("timeline",), plan_visuals),
            StepDef("render_video", ("timeline", "voiceover"), ("video",), render_video),
            StepDef("make_captions", ("script", "voice_track"), ("captions",), make_captions),
            StepDef("make_thumbnail", ("brief",), ("thumbnail",), make_thumbnail),
            StepDef(
                "package_metadata",
                ("brief", "script", "voice_track"),
                ("metadata",),
                package_metadata,
            ),
            StepDef(
                "publish",
                ("video", "thumbnail", "captions", "metadata"),
                ("publish_result",),  # a checklist is publisher-specific extra output
                publish,
            ),
        ],
    )

