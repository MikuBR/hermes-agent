"""Deterministic authorization point for the fork-owned runtime."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from hermes_core.execution import ExecutionRequest

from .capabilities import CapabilityPolicy, CapabilityRisk, DEFAULT_CAPABILITIES
from .risk import assess


class GovernanceDecision(str, Enum):
    ALLOW = "allow"
    ALLOW_WITH_AUDIT = "allow_with_audit"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


@dataclass(frozen=True)
class GovernorContext:
    autonomy_level: int
    explicit_permission: bool = False
    rollback_available: bool = False
    project_confident: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.autonomy_level <= 10:
            raise ValueError("autonomy_level must be between 0 and 10")


@dataclass(frozen=True)
class GovernanceResult:
    decision: GovernanceDecision
    capability: str
    reason: str
    risk: CapabilityRisk


class SafetyGovernor:
    """Single deterministic policy evaluator; it never executes requests."""

    def __init__(self, capabilities: dict[str, CapabilityPolicy] | None = None) -> None:
        self._capabilities = dict(DEFAULT_CAPABILITIES if capabilities is None else capabilities)

    def evaluate(self, request: ExecutionRequest, context: GovernorContext) -> GovernanceResult:
        policy = self._capabilities.get(request.capability)
        if policy is None:
            return GovernanceResult(
                GovernanceDecision.REQUIRE_APPROVAL,
                request.capability,
                "unknown capability requires explicit review",
                CapabilityRisk.HIGH,
            )

        if not context.project_confident or request.project.ambiguous:
            return GovernanceResult(
                GovernanceDecision.DENY,
                request.capability,
                "project context is ambiguous",
                policy.risk,
            )

        risk = assess(policy)
        if policy.cross_project and not context.explicit_permission:
            return GovernanceResult(
                GovernanceDecision.DENY,
                policy.name,
                "cross-project execution requires explicit permission",
                risk.level,
            )

        if policy.requires_explicit_approval and not context.explicit_permission:
            return GovernanceResult(
                GovernanceDecision.REQUIRE_APPROVAL,
                policy.name,
                "capability requires explicit approval",
                risk.level,
            )

        if risk.level is CapabilityRisk.CRITICAL and not context.explicit_permission:
            return GovernanceResult(
                GovernanceDecision.REQUIRE_APPROVAL,
                policy.name,
                "critical-risk capability requires approval",
                risk.level,
            )

        if risk.level is CapabilityRisk.HIGH:
            if not context.rollback_available and not context.explicit_permission:
                return GovernanceResult(
                    GovernanceDecision.REQUIRE_APPROVAL,
                    policy.name,
                    "high-risk action has no declared rollback",
                    risk.level,
                )
            return GovernanceResult(
                GovernanceDecision.ALLOW_WITH_AUDIT,
                policy.name,
                "high-risk action permitted under bounded policy",
                risk.level,
            )

        if risk.level is CapabilityRisk.MODERATE:
            return GovernanceResult(
                GovernanceDecision.ALLOW_WITH_AUDIT,
                policy.name,
                "moderate-risk action is auditable",
                risk.level,
            )

        return GovernanceResult(
            GovernanceDecision.ALLOW,
            policy.name,
            "low-risk action permitted",
            risk.level,
        )
