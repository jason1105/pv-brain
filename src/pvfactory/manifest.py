"""The manifest: versioned provenance record and durable run state.

Step boundaries are checkpoint boundaries (docs/specs/02): the manifest is
persisted after every step transition, and `resume` replays from it.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any

from .artifacts import ArtifactStore

MANIFEST_NAME = "manifest.json"
SCHEMA_VERSION = 1

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"
STATUS_AWAITING_APPROVAL = "awaiting_approval"

_STATUSES = {STATUS_PENDING, STATUS_RUNNING, STATUS_DONE, STATUS_FAILED, STATUS_AWAITING_APPROVAL}


def _now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")


@dataclass
class StepRecord:
    name: str
    status: str = STATUS_PENDING
    provider: str | None = None
    model: str | None = None
    prompt_ref: str | None = None
    prompt_hash: str | None = None
    seed: int | None = None
    started_at: str | None = None
    duration_s: float | None = None
    error: str | None = None
    outputs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v not in (None, {})}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StepRecord:
        rec = cls(name=d["name"])
        for k, v in d.items():
            setattr(rec, k, v)
        if rec.status not in _STATUSES:
            raise ValueError(f"unknown step status {rec.status!r}")
        return rec


@dataclass
class Manifest:
    run_id: str
    channel_id: str
    workflow: str
    draft: bool
    seed: int
    created_at: str = field(default_factory=_now)
    steps: list[StepRecord] = field(default_factory=list)
    artifacts: dict[str, dict[str, str]] = field(default_factory=dict)

    def step(self, name: str) -> StepRecord:
        for s in self.steps:
            if s.name == name:
                return s
        raise KeyError(name)

    def start_step(self, name: str) -> StepRecord:
        rec = self.step(name)
        rec.status = STATUS_RUNNING
        rec.started_at = _now()
        return rec

    def finish_step(
        self,
        name: str,
        outputs: dict[str, str],
        store: ArtifactStore,
        provenance: dict[str, Any] | None = None,
    ) -> None:
        rec = self.step(name)
        rec.status = STATUS_DONE
        rec.outputs = dict(outputs)
        if rec.started_at:
            started = _dt.datetime.fromisoformat(rec.started_at)
            rec.duration_s = round((_dt.datetime.now(_dt.UTC) - started).total_seconds(), 3)
        for k, v in (provenance or {}).items():
            setattr(rec, k, v)
        for aname, ref in outputs.items():
            entry = {"ref": ref}
            if store.exists(ref):
                entry["sha256"] = store.sha256(ref)
            self.artifacts[aname] = entry

    def fail_step(self, name: str, error: str) -> None:
        rec = self.step(name)
        rec.status = STATUS_FAILED
        rec.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "channel_id": self.channel_id,
            "workflow": self.workflow,
            "draft": self.draft,
            "seed": self.seed,
            "created_at": self.created_at,
            "steps": [s.to_dict() for s in self.steps],
            "artifacts": self.artifacts,
        }

    def save(self, store: ArtifactStore) -> None:
        store.put_json(MANIFEST_NAME, self.to_dict())

    @classmethod
    def load(cls, store: ArtifactStore) -> Manifest:
        d = store.get_json(f"artifact://{MANIFEST_NAME}")
        assert isinstance(d, dict)
        if d.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"unsupported manifest schema_version {d.get('schema_version')!r}")
        m = cls(
            run_id=d["run_id"],
            channel_id=d["channel_id"],
            workflow=d["workflow"],
            draft=d["draft"],
            seed=d["seed"],
            created_at=d["created_at"],
        )
        m.steps = [StepRecord.from_dict(s) for s in d["steps"]]
        m.artifacts = d.get("artifacts", {})
        return m
