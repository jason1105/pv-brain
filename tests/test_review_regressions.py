"""Regression tests for the pre-merge adversarial code-review findings."""

from pathlib import Path

import pytest

from pvfactory.channelstore import LocalChannelStore
from pvfactory.cli import main
from pvfactory.engine import RunContext, Runner, StepDef, StepResult, Workflow
from pvfactory.errors import ConfigError
from pvfactory.llm import extract_json
from pvfactory.manifest import (
    STATUS_AWAITING_APPROVAL,
    STATUS_DONE,
    Manifest,
    StepRecord,
)
from pvfactory.profile import load_profile
from pvfactory.render import _concat_quote


def test_extract_json_skips_braces_in_prose():
    # a real LLM may echo template braces before the actual JSON
    noisy = 'Here is the {topic} JSON you asked for: {"angle": "x", "n": 1}'
    assert extract_json(noisy) == {"angle": "x", "n": 1}


def test_concat_quote_escapes_apostrophes():
    quoted = _concat_quote(Path("/data/bob's channel/seg-001.png"))
    assert quoted == "'/data/bob'\\''s channel/seg-001.png'"


def test_step_error_cleared_after_successful_rerun(tmp_path):
    from pvfactory.artifacts import LocalArtifactStore

    calls = {"n": 0}

    def flaky(ctx):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return StepResult({"a": ctx.store.put_text("a.txt", "ok")})

    wf = Workflow("toy", [StepDef("s1", (), ("a",), flaky)])
    ctx = RunContext(
        store=LocalArtifactStore(tmp_path), profile=None, providers={}, seed=1, draft=True
    )
    manifest = Manifest(run_id="r", channel_id="c", workflow="toy", draft=True, seed=1)
    with pytest.raises(RuntimeError):
        Runner(wf, ctx, manifest).run()
    assert manifest.step("s1").error
    Runner(wf, ctx, manifest).run()
    assert manifest.step("s1").status == STATUS_DONE
    assert manifest.step("s1").error is None  # stale error must not survive


def test_engine_halts_at_awaiting_approval(tmp_path):
    from pvfactory.artifacts import LocalArtifactStore

    executed = []

    def make(name):
        def fn(ctx):
            executed.append(name)
            return StepResult({name: ctx.store.put_text(f"{name}.txt", name)})

        return StepDef(name, (), (name,), fn)

    wf = Workflow("toy", [make("s1"), make("s2")])
    ctx = RunContext(
        store=LocalArtifactStore(tmp_path), profile=None, providers={}, seed=1, draft=True
    )
    manifest = Manifest(run_id="r", channel_id="c", workflow="toy", draft=True, seed=1)
    manifest.steps = [StepRecord(name="s1"), StepRecord(name="s2")]
    manifest.steps[1].status = STATUS_AWAITING_APPROVAL
    Runner(wf, ctx, manifest).run()
    assert executed == ["s1"]  # the gate is never executed through
    assert manifest.step("s2").status == STATUS_AWAITING_APPROVAL


def test_step_record_rejects_unknown_keys():
    with pytest.raises(ValueError, match="invalid step record"):
        StepRecord.from_dict({"name": "s1", "bogus_key": 1})


def test_backlog_missing_file_is_config_error(tiny_profile):
    code = main(
        ["produce", "--profile", str(tiny_profile), "--backlog", "no-such-file.txt", "--offline"]
    )
    assert code == 2


@pytest.mark.parametrize(
    "override,match",
    [
        ('resolution = "1281x719"', "even"),
        ('resolution = "1280x719"', "even"),
    ],
)
def test_odd_resolution_rejected_at_profile_load(tmp_path, override, match):
    body = (
        "schema_version = 1\n[channel]\nid='x'\nname='x'\nniche='x'\naudience='x'\n"
        f"[render]\n{override}\n"
    )
    p = tmp_path / "p.toml"
    p.write_text(body, "utf-8")
    with pytest.raises(ConfigError, match=match):
        load_profile(p)


def test_channel_id_must_be_slug(tmp_path):
    body = "schema_version = 1\n[channel]\nid='brand/tech'\nname='x'\nniche='x'\naudience='x'\n"
    p = tmp_path / "p.toml"
    p.write_text(body, "utf-8")
    with pytest.raises(ConfigError, match="slug"):
        load_profile(p)


def test_record_topic_idempotent_by_run_id(tmp_path):
    store = LocalChannelStore(tmp_path / "channels.json")
    store.record_topic("c1", "topic a", "run-1")
    store.record_topic("c1", "topic a", "run-1")  # resume of a recorded run
    store.record_topic("c1", "topic b", "run-2")
    assert store.topics("c1") == ["topic a", "topic b"]


def test_corrupt_foreign_manifest_does_not_break_find_run(tmp_path, tiny_profile):
    from pvfactory.runs import find_run, produce_video

    pkg = produce_video(
        profile_path=tiny_profile,
        topic="find run robustness",
        output_root=tmp_path / "out",
        offline=True,
        seed=7,
    )
    # plant corrupt + foreign manifests that must be skipped, not fatal
    weird = tmp_path / "out" / "foreign" / "thing"
    weird.mkdir(parents=True)
    (weird / "manifest.json").write_text("[1, 2, 3]", "utf-8")
    (tmp_path / "out" / "broken").mkdir()
    (tmp_path / "out" / "broken" / "manifest.json").write_text("{not json", "utf-8")

    import json

    run_id = json.loads((pkg / "manifest.json").read_text("utf-8"))["run_id"]
    assert find_run(tmp_path / "out", run_id) == pkg
