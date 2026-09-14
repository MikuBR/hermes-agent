"""Fork-owned memory and learning contracts.

This module is deliberately independent from Hermes' existing MemoryProvider API. It
models safe state transitions first; adapters and guarded runtime wiring come later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping, Optional, Tuple
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class MemoryScope(str, Enum):
    """Visibility boundary for a memory record."""

    GLOBAL = "global"
    USER = "user"
    PROJECT = "project"
    SESSION = "session"


class MemoryOrigin(str, Enum):
    """Where a memory/learning fact came from."""

    USER = "user"
    TOOL = "tool"
    OBSERVATION = "observation"
    SESSION_SUMMARY = "session_summary"
    LEARNED = "learned"
    IMPORTED = "imported"


@dataclass(frozen=True)
class MemoryRecord:
    """Durable memory claim with explicit provenance and isolation metadata."""

    key: str
    content: str
    scope: MemoryScope
    memory_id: str = field(default_factory=lambda: _id("mem"))
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    origin: MemoryOrigin = MemoryOrigin.OBSERVATION
    evidence: Tuple[str, ...] = ()
    confidence: float = 0.0
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("memory key must not be empty")
        if not self.content.strip():
            raise ValueError("memory content must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.scope is MemoryScope.USER and not self.user_id:
            raise ValueError("user-scoped memory requires user_id")
        if self.scope is MemoryScope.PROJECT and not self.project_id:
            raise ValueError("project-scoped memory requires project_id")
        if self.scope is MemoryScope.SESSION and not self.session_id:
            raise ValueError("session-scoped memory requires session_id")


@dataclass(frozen=True)
class LearningCandidate:
    """A proposed memory change that is not trusted until evidence supports it."""

    key: str
    content: str
    source_scope: MemoryScope
    candidate_id: str = field(default_factory=lambda: _id("learn"))
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    supporting_evidence: Tuple[str, ...] = ()
    contradicting_evidence: Tuple[str, ...] = ()
    observed_project_ids: Tuple[str, ...] = ()
    confidence: float = 0.0
    origin: MemoryOrigin = MemoryOrigin.LEARNED
    created_at: datetime = field(default_factory=_utc_now)
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.content.strip():
            raise ValueError("learning candidate key/content must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.source_scope is MemoryScope.USER and not self.user_id:
            raise ValueError("user-origin candidate requires user_id")
        if self.source_scope is MemoryScope.PROJECT and not self.project_id:
            raise ValueError("project-origin candidate requires project_id")
        if self.source_scope is MemoryScope.SESSION and not self.session_id:
            raise ValueError("session-origin candidate requires session_id")


@dataclass(frozen=True)
class LearningDecision:
    """Result of a guarded promotion/evaluation attempt."""

    accepted: bool
    reason: str
    candidate_id: str
    target_scope: Optional[MemoryScope] = None
    memory_id: Optional[str] = None
