"""Bounded, in-memory checkpoint registry for the rollback control plane."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
from threading import RLock
from typing import Iterable

from .manager import CheckpointSpec


@dataclass(frozen=True)
class CheckpointRecord:
    spec: CheckpointSpec
    fingerprint: str


class CheckpointStore:
    """Thread-safe bounded checkpoint metadata store; it never restores targets itself."""

    def __init__(self, max_records: int = 64) -> None:
        if max_records < 1:
            raise ValueError("max_records must be >= 1")
        self._max_records = max_records
        self._records: OrderedDict[str, CheckpointRecord] = OrderedDict()
        self._lock = RLock()

    @staticmethod
    def fingerprint(spec: CheckpointSpec) -> str:
        material = "|".join(
            (spec.checkpoint_id, spec.scope, spec.target, spec.created_at.isoformat(), spec.parent_id or "")
        )
        return sha256(material.encode("utf-8")).hexdigest()

    def put(self, spec: CheckpointSpec) -> CheckpointRecord:
        record = CheckpointRecord(spec=spec, fingerprint=self.fingerprint(spec))
        with self._lock:
            self._records[spec.checkpoint_id] = record
            self._records.move_to_end(spec.checkpoint_id)
            while len(self._records) > self._max_records:
                self._records.popitem(last=False)
        return record

    def get(self, checkpoint_id: str) -> CheckpointRecord | None:
        with self._lock:
            return self._records.get(checkpoint_id)

    def all(self) -> tuple[CheckpointRecord, ...]:
        with self._lock:
            return tuple(self._records.values())

    def remove(self, checkpoint_id: str) -> bool:
        with self._lock:
            return self._records.pop(checkpoint_id, None) is not None
