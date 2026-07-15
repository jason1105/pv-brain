"""Workflow-as-data engine (docs/specs/02, ADR-0002, ADR-0004).

A workflow is a declared, ordered sequence of steps with typed, named
artifact contracts. The contract graph is validated at assembly - a wiring
mistake fails before anything runs. Runs are durable: the manifest persists
at every step boundary and `Runner.run` resumes idempotently.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .artifacts import ArtifactStore, is_ref
from .errors import StepError, ValidationError
from .manifest import STATUS_DONE, Manifest, StepRecord


@dataclass
class RunContext:
    """Everything a step may touch. Steps read inputs from `artifacts` and
    return their outputs; they never mutate `artifacts` directly."""

    store: ArtifactStore
    profile: Any
    providers: Mapping[str, Any]
    seed: int
    draft: bool
    artifacts: dict[str, str] = field(default_factory=dict)

    def artifact(self, name: str) -> str:
        try:
            return self.artifacts[name]
        except KeyError:
            raise StepError("<engine>", f"artifact {name!r} not available") from None


@dataclass(frozen=True)
class StepDef:
    name: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    fn: Callable[[RunContext], StepResult]


@dataclass
class StepResult:
    outputs: dict[str, str]
    provenance: dict[str, Any] = field(default_factory=dict)


class Workflow:
    def __init__(self, name: str, steps: list[StepDef], initial: tuple[str, ...] = ()):
        self.name = name
        self.steps = steps
        self.initial = initial
        self._validate()

    def _validate(self) -> None:
        """Assembly-time contract-graph validation (spec 02)."""
        available = set(self.initial)
        seen_steps: set[str] = set()
        for step in self.steps:
            if step.name in seen_steps:
                raise ValidationError(f"workflow {self.name}: duplicate step {step.name!r}")
            seen_steps.add(step.name)
            for inp in step.inputs:
                if inp not in available:
                    raise ValidationError(
                        f"workflow {self.name}: step {step.name!r} consumes {inp!r}, "
                        f"which no earlier step produces and is not an initial artifact"
                    )
            for out in step.outputs:
                if out in available:
                    raise ValidationError(
                        f"workflow {self.name}: step {step.name!r} re-produces {out!r}"
                    )
                available.add(out)


class Runner:
    """Executes a workflow with checkpointing at every step boundary."""

    def __init__(self, workflow: Workflow, ctx: RunContext, manifest: Manifest):
        self.workflow = workflow
        self.ctx = ctx
        self.manifest = manifest
        if not manifest.steps:
            manifest.steps = [StepRecord(name=s.name) for s in workflow.steps]

    def run(self, log: Callable[[str], None] = lambda _: None) -> Manifest:
        for step in self.workflow.steps:
            rec = self.manifest.step(step.name)
            if rec.status == STATUS_DONE:
                # Idempotent resume: restore outputs, never re-execute.
                self.ctx.artifacts.update(rec.outputs)
                log(f"skip {step.name} (done)")
                continue
            self.manifest.start_step(step.name)
            self.manifest.save(self.ctx.store)
            log(f"run  {step.name}")
            try:
                result = step.fn(self.ctx)
                missing = [o for o in step.outputs if o not in result.outputs]
                if missing:
                    raise StepError(step.name, f"declared outputs not produced: {missing}")
                bad = [r for r in result.outputs.values() if not is_ref(r)]
                if bad:
                    raise StepError(step.name, f"outputs must be artifact refs, got: {bad}")
            except Exception as exc:
                self.manifest.fail_step(step.name, f"{type(exc).__name__}: {exc}")
                self.manifest.save(self.ctx.store)
                raise
            self.ctx.artifacts.update(result.outputs)
            self.manifest.finish_step(
                step.name, result.outputs, self.ctx.store, result.provenance
            )
            self.manifest.save(self.ctx.store)
        return self.manifest
