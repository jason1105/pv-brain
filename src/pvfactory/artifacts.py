"""Artifact storage behind URI-like references (docs/specs/02, ADR-0004).

Nothing outside LocalArtifactStore may know artifacts live on a local
filesystem. `path_for()` is the single documented escape hatch for handing
files to subprocesses (ffmpeg).
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from pathlib import Path

SCHEME = "artifact://"


def is_ref(value: str) -> bool:
    return isinstance(value, str) and value.startswith(SCHEME)


def ref_name(ref: str) -> str:
    if not is_ref(ref):
        raise ValueError(f"not an artifact ref: {ref!r}")
    return ref[len(SCHEME) :]


class ArtifactStore(ABC):
    @abstractmethod
    def put_bytes(self, name: str, data: bytes) -> str: ...

    @abstractmethod
    def get_bytes(self, ref: str) -> bytes: ...

    @abstractmethod
    def exists(self, ref: str) -> bool: ...

    @abstractmethod
    def path_for(self, ref: str) -> Path:
        """Filesystem path for subprocess consumption. Escape hatch - see module doc."""

    def put_text(self, name: str, text: str) -> str:
        return self.put_bytes(name, text.encode("utf-8"))

    def put_json(self, name: str, obj: object) -> str:
        return self.put_text(name, json.dumps(obj, ensure_ascii=False, indent=2))

    def get_text(self, ref: str) -> str:
        return self.get_bytes(ref).decode("utf-8")

    def get_json(self, ref: str) -> object:
        return json.loads(self.get_text(ref))

    def sha256(self, ref: str) -> str:
        return hashlib.sha256(self.get_bytes(ref)).hexdigest()


class LocalArtifactStore(ArtifactStore):
    """Artifacts as files under a run directory."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        p = (self.root / name).resolve()
        if not p.is_relative_to(self.root.resolve()):
            raise ValueError(f"artifact name escapes store root: {name!r}")
        return p

    def put_bytes(self, name: str, data: bytes) -> str:
        p = self._path(name)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return f"{SCHEME}{name}"

    def get_bytes(self, ref: str) -> bytes:
        return self._path(ref_name(ref)).read_bytes()

    def exists(self, ref: str) -> bool:
        return self._path(ref_name(ref)).is_file()

    def path_for(self, ref: str) -> Path:
        return self._path(ref_name(ref))
