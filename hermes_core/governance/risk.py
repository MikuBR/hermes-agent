"""Risk normalization for governance decisions."""

from __future__ import annotations

from dataclasses import dataclass

from .capabilities import CapabilityPolicy, CapabilityRisk


@dataclass(frozen=True)
class RiskAssessment:
    level: CapabilityRisk
    reversible: bool
    external_side_effect: bool
    sensitive_data: bool
    cross_project: bool
    blast_radius: int

    @property
    def consequential(self) -> bool:
        return self.level in {CapabilityRisk.HIGH, CapabilityRisk.CRITICAL} or self.cross_project


def assess(policy: CapabilityPolicy) -> RiskAssessment:
    radius = 1
    if policy.external_side_effect:
        radius += 2
    if policy.sensitive_data:
        radius += 2
    if policy.cross_project:
        radius += 4
    return RiskAssessment(
        level=policy.risk,
        reversible=policy.reversible,
        external_side_effect=policy.external_side_effect,
        sensitive_data=policy.sensitive_data,
        cross_project=policy.cross_project,
        blast_radius=radius,
    )
