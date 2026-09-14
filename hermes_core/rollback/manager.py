"""Governed rollback control plane; concrete adapters perform target restoration."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable
from uuid import uuid4


@dataclass(frozen=True)
class CheckpointSpec:
    checkpoint_id: str = field(default_factory=lambda: "cp_" + uuid4().hex)
    scope: str = "workspace"
    target: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    parent_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.scope.strip():
            raise ValueError("scope must not be empty")
        if not self.target.strip():
            raise ValueError("target must not be empty")


@dataclass(frozen=True)
class RollbackResult:
    checkpoint_id: str
    restored: bool
    verified: bool
    dry_run: bool
    idempotent: bool
    summary: str


class RollbackManager:
    """Create checkpoints and request restoration without silently mutating targets."""

    def __init__(self, create: Callable[[CheckpointSpec], Any] | None = None, restore: Callable[[CheckpointSpec], bool] | None = None, verify: Callable[[CheckpointSpec], bool] | None = None) -> None:
        self.create = create
        self.restore = restore
        self.verify = verify
        self._lock = RLock()
        self._completed: set[str] = set()

    def checkpoint(self, scope: str = "workspace", target: str = "") -> CheckpointSpec:
        spec = CheckpointSpec(scope=scope, target=target)
        if self.create is not None:
            self.create(spec)
        return spec

    def rollback(self, spec: CheckpointSpec, *, dry_run: bool = False) -> RollbackResult:
        with self._lock:
            if spec.checkpoint_id in self._completed:
                return RollbackResult(spec.checkpoint_id, True, True, dry_run, True, "rollback already completed")
            if dry_run:
                return RollbackResult(spec.checkpoint_id, False, False, True, False, "rollback planned; target not mutated")
            if self.restore is None:
                return RollbackResult(spec.checkpoint_id, False, False, False, False, "restore adapter not configured")
            restored = bool(self.restore(spec))
            if not restored:
                return RollbackResult(spec.checkpoint_id, False, False, False, False, "rollback failed")
            verified = bool(self.verify(spec)) if self.verify is not None else False
            if not verified:
                return RollbackResult(spec.checkpoint_id, True, False, False, False, "rollback restored; post-restore verification failed or unavailable")
            self._completed.add(spec.checkpoint_id)
            return RollbackResult(spec.checkpoint_id, True, True, False, False, "rollback restored and verified")
