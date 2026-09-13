import pytest

from hermes_core.context import ProjectContextResolver
from hermes_core.execution import ExecutionRequest
from hermes_core.governance import SafetyGovernor
from hermes_core.governance.capabilities import CapabilityPolicy, CapabilityRisk
from hermes_core.governance.governor import GovernanceDecision, GovernorContext


@pytest.fixture
def request_for():
    project = ProjectContextResolver().resolve(git_root="/tmp/project")

    def build(capability: str) -> ExecutionRequest:
        return ExecutionRequest(capability=capability, actor_id="agent:test", project=project)

    return build


def test_unknown_capability_requires_review(request_for) -> None:
    result = SafetyGovernor().evaluate(request_for("unknown.action"), GovernorContext(10))
    assert result.decision is GovernanceDecision.REQUIRE_APPROVAL


def test_low_risk_is_allowed(request_for) -> None:
    result = SafetyGovernor().evaluate(request_for("filesystem.read"), GovernorContext(10))
    assert result.decision is GovernanceDecision.ALLOW


def test_critical_action_requires_explicit_permission(request_for) -> None:
    result = SafetyGovernor().evaluate(request_for("system.config"), GovernorContext(10))
    assert result.decision is GovernanceDecision.REQUIRE_APPROVAL


def test_high_risk_without_rollback_requires_review(request_for) -> None:
    result = SafetyGovernor().evaluate(request_for("filesystem.delete"), GovernorContext(10))
    assert result.decision is GovernanceDecision.REQUIRE_APPROVAL


def test_ambiguous_project_is_denied(request_for) -> None:
    project = ProjectContextResolver().resolve(
        explicit_project_id="project:a", session_project_id="project:b"
    )
    request = ExecutionRequest(capability="filesystem.read", actor_id="agent:test", project=project)
    result = SafetyGovernor().evaluate(request, GovernorContext(10))
    assert result.decision is GovernanceDecision.DENY


def test_custom_cross_project_capability_is_denied_without_permission(request_for) -> None:
    project = ProjectContextResolver().resolve(git_root="/tmp/project")
    request = ExecutionRequest(capability="cross.project.write", actor_id="agent:test", project=project)
    governor = SafetyGovernor({
        "cross.project.write": CapabilityPolicy(
            "cross.project.write",
            risk=CapabilityRisk.HIGH,
            cross_project=True,
            reversible=True,
        )
    })
    result = governor.evaluate(request, GovernorContext(10))
    assert result.decision is GovernanceDecision.DENY
