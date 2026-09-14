"""Bounded self-improvement lifecycle with human-brake enforcement."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Optional, Tuple

from .models import (
    ExperimentResult,
    ImprovementDecision,
    ImprovementObservation,
    ImprovementProposal,
    ImprovementStage,
    ImprovementStatus,
)


class ImprovementManager:
    """Manage an improvement proposal without performing the improvement itself.

    Execution, code changes, deployment, and durable learning are supplied later by
    adapters. This layer only enforces lifecycle prerequisites and evidence gates.
    """

    def __init__(self, *, max_observations: int = 256, max_proposals: int = 128) -> None:
        self._observations: list[ImprovementObservation] = []
        self._proposals: dict[str, ImprovementProposal] = {}
        self._experiments: dict[str, ExperimentResult] = {}
        self._max_observations = max_observations
        self._max_proposals = max_proposals

    def observe(
        self,
        *,
        subject: str,
        symptom: str,
        evidence: Iterable[str] = (),
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> ImprovementObservation:
        observation = ImprovementObservation(
            subject=subject,
            symptom=symptom,
            evidence=_bounded_strings(evidence, 16, 1024),
            project_id=project_id,
            session_id=session_id,
            metadata=_bounded_metadata(metadata or {}),
        )
        self._observations.append(observation)
        if len(self._observations) > self._max_observations:
            del self._observations[: len(self._observations) - self._max_observations]
        return observation

    def observations(self) -> Tuple[ImprovementObservation, ...]:
        return tuple(self._observations)

    def propose(
        self,
        *,
        objective: str,
        hypothesis: str,
        risk: str,
        evidence: Iterable[str] = (),
        expected_outcomes: Iterable[str] = (),
        rollback_checkpoint_id: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> ImprovementProposal:
        proposal = ImprovementProposal(
            objective=objective,
            hypothesis=hypothesis,
            risk=risk,
            evidence=_bounded_strings(evidence, 32, 1024),
            expected_outcomes=_bounded_strings(expected_outcomes, 16, 512),
            rollback_checkpoint_id=rollback_checkpoint_id,
            metadata=_bounded_metadata(metadata or {}),
        )
        self._proposals[proposal.proposal_id] = proposal
        self._trim_proposals()
        return proposal

    def get(self, proposal_id: str) -> Optional[ImprovementProposal]:
        return self._proposals.get(proposal_id)

    def isolate(self, proposal_id: str) -> ImprovementDecision:
        proposal = self._require(proposal_id)
        if proposal is None:
            return ImprovementDecision(proposal_id, ImprovementStage.ISOLATE, False, "proposal not found")
        if not proposal.evidence:
            return ImprovementDecision(proposal_id, ImprovementStage.ISOLATE, False, "isolation requires evidence-backed proposal")
        self._proposals[proposal_id] = replace(proposal, status=ImprovementStatus.EXPERIMENTAL)
        return ImprovementDecision(proposal_id, ImprovementStage.ISOLATE, True, "proposal admitted to isolated experiment")

    def record_experiment(self, result: ExperimentResult) -> ImprovementDecision:
        proposal = self._require(result.proposal_id)
        if proposal is None:
            return ImprovementDecision(result.proposal_id, ImprovementStage.TEST, False, "proposal not found")
        self._experiments[result.proposal_id] = result
        if not result.passed:
            self._proposals[result.proposal_id] = replace(proposal, status=ImprovementStatus.FAILED)
            return ImprovementDecision(result.proposal_id, ImprovementStage.TEST, False, "experiment failed")
        if not result.regression_checks_passed:
            self._proposals[result.proposal_id] = replace(proposal, status=ImprovementStatus.FAILED)
            return ImprovementDecision(result.proposal_id, ImprovementStage.TEST, False, "regression verification failed")
        if not result.adversarial_checks_passed:
            self._proposals[result.proposal_id] = replace(proposal, status=ImprovementStatus.FAILED)
            return ImprovementDecision(result.proposal_id, ImprovementStage.ADVERSARIAL_QA, False, "adversarial verification failed")
        self._proposals[result.proposal_id] = replace(proposal, status=ImprovementStatus.VERIFIED)
        return ImprovementDecision(result.proposal_id, ImprovementStage.COMPARE, True, "experiment and adversarial/regression checks passed")

    def approve(self, proposal_id: str, *, approved: bool, reason: str) -> ImprovementDecision:
        proposal = self._require(proposal_id)
        if proposal is None:
            return ImprovementDecision(proposal_id, ImprovementStage.APPROVE, False, "proposal not found")
        if not approved:
            self._proposals[proposal_id] = replace(proposal, status=ImprovementStatus.REJECTED)
            return ImprovementDecision(proposal_id, ImprovementStage.APPROVE, False, reason or "rejected")
        if proposal.status is not ImprovementStatus.VERIFIED:
            return ImprovementDecision(proposal_id, ImprovementStage.APPROVE, False, "approval requires verified experiment")
        if not reason.strip():
            return ImprovementDecision(proposal_id, ImprovementStage.APPROVE, False, "approval requires an explicit reason")
        self._proposals[proposal_id] = replace(proposal, status=ImprovementStatus.APPROVED)
        return ImprovementDecision(proposal_id, ImprovementStage.APPROVE, True, reason)

    def deploy(self, proposal_id: str) -> ImprovementDecision:
        proposal = self._require(proposal_id)
        if proposal is None:
            return ImprovementDecision(proposal_id, ImprovementStage.DEPLOY, False, "proposal not found")
        if proposal.status is not ImprovementStatus.APPROVED:
            return ImprovementDecision(proposal_id, ImprovementStage.DEPLOY, False, "deployment requires explicit approval")
        experiment = self._experiments.get(proposal_id)
        if experiment is None or not experiment.passed:
            return ImprovementDecision(proposal_id, ImprovementStage.DEPLOY, False, "deployment requires a passing experiment")
        self._proposals[proposal_id] = replace(proposal, status=ImprovementStatus.DEPLOYED)
        return ImprovementDecision(proposal_id, ImprovementStage.DEPLOY, True, "deployment admitted; adapter may apply change")

    def monitor(self, proposal_id: str, *, healthy: bool, evidence: Iterable[str] = ()) -> ImprovementDecision:
        proposal = self._require(proposal_id)
        if proposal is None:
            return ImprovementDecision(proposal_id, ImprovementStage.MONITOR, False, "proposal not found")
        if proposal.status is not ImprovementStatus.DEPLOYED:
            return ImprovementDecision(proposal_id, ImprovementStage.MONITOR, False, "monitoring requires deployment")
        if not healthy:
            self._proposals[proposal_id] = replace(proposal, status=ImprovementStatus.FAILED)
            return ImprovementDecision(proposal_id, ImprovementStage.MONITOR, False, "post-deploy health check failed")
        _ = tuple(_bounded_strings(evidence, 16, 1024))
        self._proposals[proposal_id] = replace(proposal, status=ImprovementStatus.MONITORING)
        return ImprovementDecision(proposal_id, ImprovementStage.MONITOR, True, "post-deploy monitoring healthy")

    def learn(self, proposal_id: str, *, evidence: Iterable[str]) -> ImprovementDecision:
        proposal = self._require(proposal_id)
        if proposal is None:
            return ImprovementDecision(proposal_id, ImprovementStage.LEARN, False, "proposal not found")
        if proposal.status is not ImprovementStatus.MONITORING:
            return ImprovementDecision(proposal_id, ImprovementStage.LEARN, False, "learning requires successful monitoring")
        bounded = tuple(_bounded_strings(evidence, 16, 1024))
        if not bounded:
            return ImprovementDecision(proposal_id, ImprovementStage.LEARN, False, "learning requires post-deploy evidence")
        self._proposals[proposal_id] = replace(proposal, status=ImprovementStatus.LEARNED)
        return ImprovementDecision(proposal_id, ImprovementStage.LEARN, True, "validated outcome may be promoted by a later memory adapter")

    def _require(self, proposal_id: str) -> Optional[ImprovementProposal]:
        return self._proposals.get(proposal_id)

    def _trim_proposals(self) -> None:
        while len(self._proposals) > self._max_proposals:
            oldest_id = next(iter(self._proposals))
            del self._proposals[oldest_id]


def _bounded_strings(values: Iterable[str], limit: int, max_chars: int) -> tuple[str, ...]:
    return tuple(str(value)[:max_chars] for value in values if str(value).strip())[:limit]


def _bounded_metadata(values: dict[str, str], limit: int = 32, max_chars: int = 512) -> dict[str, str]:
    return {str(k)[:128]: str(v)[:max_chars] for k, v in list(values.items())[:limit]}
