"""Engine: assembly validation, checkpointing, idempotent resume."""

import pytest

from pvfactory.artifacts import LocalArtifactStore
from pvfactory.engine import RunContext, Runner, StepDef, StepResult, Workflow
from pvfactory.errors import ValidationError
from pvfactory.manifest import STATUS_DONE, STATUS_FAILED, Manifest


def _ctx(tmp_path):
    return RunContext(
        store=LocalArtifactStore(tmp_path),
        profile=None,
        providers={},
        seed=1,
        draft=True,
    )


def _manifest():
    return Manifest(run_id="r1", channel_id="c1", workflow="toy", draft=True, seed=1)


def test_miswired_workflow_fails_at_assembly():
    step = StepDef("s1", ("missing",), ("out",), lambda ctx: StepResult({}))
    with pytest.raises(ValidationError, match="consumes 'missing'"):
        Workflow("toy", [step])


def test_duplicate_output_fails_at_assembly():
    s1 = StepDef("s1", (), ("a",), lambda ctx: StepResult({}))
    s2 = StepDef("s2", ("a",), ("a",), lambda ctx: StepResult({}))
    with pytest.raises(ValidationError, match="re-produces"):
        Workflow("toy", [s1, s2])


def _toy_workflow(counter, fail_at=None):
    def make(name, inputs, outputs):
        def fn(ctx):
            counter[name] = counter.get(name, 0) + 1
            if name == fail_at:
                raise RuntimeError("boom")
            return StepResult({o: ctx.store.put_text(f"{o}.txt", name) for o in outputs})

        return StepDef(name, inputs, outputs, fn)

    return Workflow(
        "toy",
        [make("s1", (), ("a",)), make("s2", ("a",), ("b",)), make("s3", ("b",), ("c",))],
    )


def test_failure_recorded_then_resume_skips_done_steps(tmp_path):
    counter: dict[str, int] = {}
    ctx = _ctx(tmp_path)
    manifest = _manifest()
    with pytest.raises(RuntimeError):
        Runner(_toy_workflow(counter, fail_at="s2"), ctx, manifest).run()
    assert manifest.step("s1").status == STATUS_DONE
    assert manifest.step("s2").status == STATUS_FAILED
    assert "boom" in manifest.step("s2").error

    # resume from persisted manifest: s1 must NOT re-execute
    store = LocalArtifactStore(tmp_path)
    loaded = Manifest.load(store)
    ctx2 = _ctx(tmp_path)
    Runner(_toy_workflow(counter), ctx2, loaded).run()
    assert counter == {"s1": 1, "s2": 2, "s3": 1}
    assert [s.status for s in loaded.steps] == [STATUS_DONE] * 3
    assert ctx2.artifacts["a"] == "artifact://a.txt"


def test_undeclared_outputs_rejected(tmp_path):
    bad = StepDef("s1", (), ("a",), lambda ctx: StepResult({}))
    wf = Workflow("toy", [bad])
    with pytest.raises(Exception, match="declared outputs not produced"):
        Runner(wf, _ctx(tmp_path), _manifest()).run()
