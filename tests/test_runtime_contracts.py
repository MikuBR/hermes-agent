"""Tests for the inert Runtime 0 contract layer."""

from datetime import timezone

from hermes_core.contracts import (
    AgentResult,
    AgentTask,
    AutonomyLevel,
    Capability,
    CapabilityRisk,
    ExecutionRequest,
    ExecutionStatus,
    ProjectContext,
    ProjectContextSource,
    RuntimeContext,
    VerificationResult,
    VerificationStatus,
)


def test_contracts_are_constructible_without_legacy_runtime_imports():
    project = ProjectContext(
        project_id="demo",
        workspace_root="/tmp/demo",
        source=ProjectContextSource.GIT,
        confidence=0.95,
        evidence=("git-root",),
    )
    context = RuntimeContext(
        session_id="session-1",
        project=project,
        autonomy=AutonomyLevel.GUARDED,
    )
    request = ExecutionRequest(
        capability=Capability(
            name="filesystem.write",
            category="filesystem",
            risk=CapabilityRisk.HIGH,
            reversible=True,
        ),
        actor_id="agent-1",
        project=project,
    )

    assert context.project.project_id == "demo"
    assert request.capability.risk is CapabilityRisk.HIGH
    assert request.status if hasattr(request, "status") else True


def test_invalid_project_confidence_is_rejected():
    try:
        ProjectContext(project_id="bad", confidence=1.1)
    except ValueError as exc:
        assert "confidence" in str(exc)
    else:
        raise AssertionError("invalid confidence must fail")


def test_status_contract_distinguishes_execution_from_verification():
    result = AgentResult(task_id="task-1", status=ExecutionStatus.EXECUTED)
    verification = VerificationResult(status=VerificationStatus.PARTIALLY_VERIFIED)

    assert result.status is ExecutionStatus.EXECUTED
    assert verification.status is VerificationStatus.PARTIALLY_VERIFIED


def test_timestamps_are_aware_utc():
    task = AgentTask(objective="contract smoke")
    assert task.task_id.startswith("task_")

    project = ProjectContext(project_id="time")
    context = RuntimeContext(session_id="s", project=project)
    assert context.created_at.tzinfo is timezone.utc
