"""Contracts for the fork-owned self-improvement control plane (Runtime 9)."""

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


class ImprovementStage(str, Enum):
    OBSERVE = "observe"
    DIAGNOSE = "diagnose"
    RESEARCH = "research"
    PROPOSE = "propose"
    ISOLATE = "isolate"
    IMPLEMENT = "implement"
    TEST = "test"
    ADVERSARIAL_QA = "adversarial_qa"
    COMPARE = "compare"
    APPROVE = "approve"
    DEPLOY = "deploy"
    MONITOR = "monitor"
    LEARN = "learn"


class ImprovementStatus(str, Enum):
    PROPOSED = "proposed"
    EXPERIMENTAL = "experimental"
    VERIFIED = "verified"
    APPROVAL_REQUIRED = "approval_required"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    REJECTED = "rejected"
    FAILED = "failed"
    MONITORING = "monitoring"
    LEARNED = "learned"


@dataclass(frozen=True)
class ImprovementObservation:
    subject: str
    symptom: str
    evidence: Tuple[str, ...] = ()
    observation_id: str = field(default_factory=lambda: _id("obs"))
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = field(default_factory=_utc_now)
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ImprovementProposal:
    objective: str
    hypothesis: str
    risk: str
    proposal_id: str = field(default_factory=lambda: _id("imp"))
    evidence: Tuple[str, ...] = ()
    expected_outcomes: Tuple[str, ...] = ()
    rollback_checkpoint_id: Optional[str] = None
    status: ImprovementStatus = ImprovementStatus.PROPOSED
    created_at: datetime = field(default_factory=_utc_now)
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExperimentResult:
    proposal_id: str
    passed: bool
    evidence: Tuple[str, ...] = ()
    verification_id: Optional[str] = None
    adversarial_checks_passed: bool = False
    regression_checks_passed: bool = False
    comparison_summary: str = ""
    created_at: datetime = field(default_factory=_utc_now)


@dataclass(frozen=True)
class ImprovementDecision:
    proposal_id: str
    stage: ImprovementStage
    allowed: bool
    reason: str
