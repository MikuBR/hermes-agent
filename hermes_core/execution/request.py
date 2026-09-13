"""Provider/tool-neutral execution request contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from hermes_core.context import ProjectContext


@dataclass(frozen=True)
class ExecutionRequest:
    """Canonical description of an operation before authorization."""

    capability: str
    actor_id: str
    project: ProjectContext
    arguments: Mapping[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    parent_request_id: str | None = None
    task_id: str | None = None
    session_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.capability.strip():
            raise ValueError("capability cannot be empty")
        if not self.actor_id.strip():
            raise ValueError("actor_id cannot be empty")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
