"""Data models used to describe resolved project context."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ProjectContextSource(str, Enum):
    EXPLICIT = "explicit"
    SESSION = "session"
    GIT = "git"
    WORKTREE = "worktree"
    CWD = "cwd"
    PROFILE = "profile"
    LINEAGE = "lineage"
    ADVISORY = "advisory"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ContextEvidence:
    """One normalized signal contributing to project resolution."""

    source: ProjectContextSource
    value: str
    weight: float
    authoritative: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("evidence weight must be between 0 and 1")
        if not self.value.strip():
            raise ValueError("evidence value cannot be empty")


@dataclass(frozen=True)
class ProjectContext:
    """Resolved project identity and its isolation boundary."""

    project_id: str
    workspace_root: Path | None
    confidence: float
    source: ProjectContextSource
    evidence: tuple[ContextEvidence, ...] = ()
    boundary: Path | None = None
    session_id: str | None = None
    lineage_id: str | None = None
    parent_project_id: str | None = None
    ambiguous: bool = False

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.workspace_root is not None and not self.workspace_root.is_absolute():
            raise ValueError("workspace_root must be absolute")
        if self.boundary is not None and not self.boundary.is_absolute():
            raise ValueError("boundary must be absolute")

    @property
    def isolation_root(self) -> Path | None:
        return self.boundary or self.workspace_root
