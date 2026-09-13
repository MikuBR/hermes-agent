"""Canonical execution result contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


class ExecutionResultStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    APPROVAL_REQUIRED = "approval_required"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ExecutionResult:
    """Normalized result independent of the concrete executor."""

    request_id: str
    status: ExecutionResultStatus
    summary: str
    output: Any = None
    error: str | None = None
    evidence: tuple[str, ...] = ()
    finished_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id cannot be empty")
        if not self.summary.strip():
            raise ValueError("summary cannot be empty")
        if self.finished_at.tzinfo is None:
            raise ValueError("finished_at must be timezone-aware")
