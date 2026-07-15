"""CLI: thin headless shell over the engine (docs/specs/04, ADR-0004).

Exit codes: 0 success, 1 pipeline failure, 2 config/environment error.
Progress goes to stderr; the final stdout line is the package path.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from . import __version__
from .artifacts import LocalArtifactStore
from .errors import PvError
from .manifest import Manifest
from .profile import load_profile
from .runs import find_run, produce_video, resume_run
from .visuals import bundled_font_path, load_font, validate_glyph_coverage


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _cmd_produce(args: argparse.Namespace) -> int:
    topics: list[str] = []
    if args.topic:
        topics.append(args.topic)
    if args.backlog:
        backlog = Path(args.backlog)
        if not backlog.is_file():
            _log(f"error: backlog file not found: {backlog}")
            return 2
        topics += [t.strip() for t in backlog.read_text("utf-8").splitlines() if t.strip()]
    if not topics:
        _log("error: provide --topic and/or a non-empty --backlog")
        return 2

    seed = args.seed if args.seed is not None else int(time.time())
    failures = 0
    for i, topic in enumerate(topics):
        _log(f"[{i + 1}/{len(topics)}] producing: {topic}")
        try:
            pkg = produce_video(
                profile_path=Path(args.profile),
                topic=topic,
                output_root=Path(args.output_root),
                offline=args.offline,
                seed=seed + i,
                log=_log,
            )
            print(pkg)
        except PvError as e:
            _log(f"error: {e}")
            if e.exit_code == 2:
                return 2
            failures += 1
    return 1 if failures else 0


def _cmd_resume(args: argparse.Namespace) -> int:
    pkg = resume_run(Path(args.output_root), args.run, log=_log)
    print(pkg)
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    pkg_dir = find_run(Path(args.output_root), args.run)
    manifest = Manifest.load(LocalArtifactStore(pkg_dir))
    _log(f"run       {manifest.run_id}")
    _log(f"channel   {manifest.channel_id}")
    _log(f"workflow  {manifest.workflow}")
    _log(f"draft     {manifest.draft}")
    for s in manifest.steps:
        extra = f"  [{s.provider}]" if s.provider else ""
        dur = f"  {s.duration_s:.1f}s" if s.duration_s is not None else ""
        err = f"  error: {s.error}" if s.error else ""
        _log(f"  {s.status:<18} {s.name}{extra}{dur}{err}")
    print(pkg_dir)
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    ok = True

    def check(label: str, fn) -> None:
        nonlocal ok
        try:
            detail = fn() or "ok"
            _log(f"  ok    {label}: {detail}")
        except Exception as e:  # noqa: BLE001 - doctor reports, never crashes
            ok = False
            _log(f"  FAIL  {label}: {e}")

    _log(f"pvfactory {__version__} doctor")
    check("python", lambda: sys.version.split()[0])

    def _ffmpeg() -> str:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        out = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=30)
        if out.returncode != 0:
            raise RuntimeError("ffmpeg binary does not run")
        return out.stdout.splitlines()[0]

    check("ffmpeg", _ffmpeg)
    check("pillow", lambda: __import__("PIL").__version__)
    check("bundled font", lambda: bundled_font_path().name)

    if args.profile:
        def _profile() -> str:
            profile = load_profile(Path(args.profile))
            validate_glyph_coverage(profile)
            load_font(profile, 40)
            return f"{profile.channel_id} ({profile.language}, {profile.style})"

        check("profile", _profile)

    _log("providers: llm=mock tts=silence,tone visuals=slides renderer=ffmpeg publisher=dryrun")
    _log("real providers (anthropic, edge-tts): milestone M3")
    return 0 if ok else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pvfactory", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)

    prod = sub.add_parser("produce", help="produce video package(s) from a topic or backlog")
    prod.add_argument("--profile", required=True, help="channel profile TOML")
    prod.add_argument("--topic", help="one topic")
    prod.add_argument("--backlog", help="file with one topic per line")
    prod.add_argument("--offline", action="store_true", help="offline draft providers (ADR-0005)")
    prod.add_argument("--seed", type=int, default=None, help="deterministic seed")
    prod.add_argument("--output-root", default="output", help="output root directory")
    prod.set_defaults(fn=_cmd_produce)

    res = sub.add_parser("resume", help="resume a failed/interrupted run")
    res.add_argument("--run", required=True, help="run id")
    res.add_argument("--output-root", default="output")
    res.set_defaults(fn=_cmd_resume)

    ins = sub.add_parser("inspect", help="print a run's manifest summary")
    ins.add_argument("--run", required=True, help="run id")
    ins.add_argument("--output-root", default="output")
    ins.set_defaults(fn=_cmd_inspect)

    doc = sub.add_parser("doctor", help="verify the environment")
    doc.add_argument("--profile", help="also validate this channel profile")
    doc.set_defaults(fn=_cmd_doctor)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except PvError as e:
        _log(f"error: {e}")
        return e.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
