"""Typed, dependency-free contracts for the MikuBR Hermes runtime.

Runtime 0 is intentionally inert: these dataclasses describe state and
messages but do not execute tools, select models, mutate files, or alter the
existing Hermes control flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Mapping, Optional, Tuple
from uuid import uuid4


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AutonomyLevel(IntEnum):
    """Ordered autonomy policy levels; authorization remains a later runtime."""
    OBSERVE = 0
    SUGGEST = 1
    APPROVE = 2
    GUARDED = 3
    AUTONOMOUS = 4


class CapabilityRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionStatus(str, Enum):
    REQUESTED = "requested"
    ALLOWED = "allowed"
    EXECUTED = "executed"
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    FAILED = "failed"
    NOT_RUN = "not_run"


class ProjectContextSource(str, Enum):
    EXPLICIT = "explicit"
    GIT = "git"
    WORKSPACE = "workspace"
    SESSION = "session"
    PROFILE = "profile"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProjectContext:
    """Identity/isolation boundary for work; keywords are not authoritative."""
    project_id: str
    workspace_root: Optional[str] = None
    source: ProjectContextSource = ProjectContextSource.UNKNOWN
    confidence: float = 0.0
    evidence: Tuple[str, ...] = ()
    branch: Optional[str] = None
    profile: Optional[str] = None
    session_id: Optional[str] = None
    parent_project_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class RuntimeContext:
    """Immutable snapshot shared by future fork-owned runtime components."""
    session_id: str
    project: ProjectContext
    autonomy: AutonomyLevel = AutonomyLevel.SUGGEST
    created_at: datetime = field(default_factory=_utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Capability:
    """Declarative description of an action the runtime may authorize."""
    name: str
    category: str
    risk: CapabilityRisk = CapabilityRisk.MEDIUM
    reversible: bool = True
    external_side_effect: bool = False
    requires_approval: bool = False
    data_sensitivity: str = "normal"
    description: str = ""


@dataclass(frozen=True)
class ExecutionRequest:
    request_id: str = field(default_factory=lambda: _id("exec"))
    capability: Capability = field(default_factory=lambda: Capability("unknown", "unknown"))
    actor_id: str = ""
    project: Optional[ProjectContext] = None
    arguments: Mapping[str, Any] = field(default_factory=dict)
    requested_autonomy: Optional[AutonomyLevel] = None
    parent_request_id: Optional[str] = None
    created_at: datetime = field(default_factory=_utc_now)


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    reason: str
    decided_by: str = "policy"
    requires_confirmation: bool = False


@dataclass(frozen=True)
class ExecutionDecision:
    status: ExecutionStatus
    allowed: bool
    reason: str
    approval: Optional[ApprovalDecision] = None
    policy_id: Optional[str] = None


@dataclass(frozen=True)
class ModelRouteRequest:
    task_type: str
    quality_target: str = "balanced"
    required_tools: Tuple[str, ...] = ()
    context_tokens: Optional[int] = None
    latency_target_ms: Optional[int] = None
    free_first: bool = True
    privacy_required: bool = False
    preferred_providers: Tuple[str, ...] = ()
    excluded_providers: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str
    route_id: str = field(default_factory=lambda: _id("route"))
    score: float = 0.0
    score_breakdown: Mapping[str, float] = field(default_factory=dict)
    fallback_models: Tuple[str, ...] = ()
    confidence: float = 0.0


@dataclass(frozen=True)
class AgentTask:
    task_id: str = field(default_factory=lambda: _id("task"))
    task_type: str = "general"
    objective: str = ""
    project: Optional[ProjectContext] = None
    parent_task_id: Optional[str] = None
    budget: Mapping[str, int] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    task_id: str
    status: ExecutionStatus
    summary: str = ""
    output: Any = None
    evidence: Tuple[str, ...] = ()
    error: Optional[str] = None


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    verified_claims: Tuple[str, ...] = ()
    evidence: Tuple[str, ...] = ()
    failures: Tuple[str, ...] = ()
    verifier: str = ""


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    actor_id: str
    timestamp: datetime = field(default_factory=_utc_now)
    request_id: Optional[str] = None
    project_id: Optional[str] = None
    status: Optional[ExecutionStatus] = None
    summary: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str = field(default_factory=lambda: _id("checkpoint"))
    scope: str = "workspace"
    target: str = ""
    created_at: datetime = field(default_factory=_utc_now)
    parent_checkpoint_id: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
