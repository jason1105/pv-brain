"""ChannelStore: cross-run channel state (docs/specs/02).

MVP stub with topic history only - reserves the seam the scheduler and
"don't repeat recent topics" logic will need.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path


class ChannelStore(ABC):
    @abstractmethod
    def topics(self, channel_id: str) -> list[str]: ...

    @abstractmethod
    def record_topic(self, channel_id: str, topic: str, run_id: str) -> None: ...


class LocalChannelStore(ChannelStore):
    def __init__(self, path: Path):
        self.path = Path(path)

    def _load(self) -> dict:
        if self.path.is_file():
            return json.loads(self.path.read_text("utf-8"))
        return {"schema_version": 1, "channels": {}}

    def topics(self, channel_id: str) -> list[str]:
        data = self._load()
        return [e["topic"] for e in data["channels"].get(channel_id, [])]

    def record_topic(self, channel_id: str, topic: str, run_id: str) -> None:
        data = self._load()
        entries = data["channels"].setdefault(channel_id, [])
        if any(e["run_id"] == run_id for e in entries):
            return  # idempotent: resuming a recorded run must not duplicate
        entries.append({"topic": topic, "run_id": run_id})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
