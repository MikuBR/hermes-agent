from hermes_core.context import ProjectContext, ProjectContextSource
from hermes_core.execution import ExecutionGateway, ExecutionRequest, ExecutionResultStatus
from hermes_core.governance import CapabilityRisk, CapabilityPolicy, SafetyGovernor
from hermes_core.governance.governor import GovernorContext


def _project() -> ProjectContext:
    return ProjectContext("project", None, 1.0, ProjectContextSource.EXPLICIT)


def _request(capability: str = "filesystem.read") -> ExecutionRequest:
    return ExecutionRequest(capability, "user", _project())


def test_protected_request_never_reaches_executor() -> None:
    called: list[str] = []
    gateway = ExecutionGateway(SafetyGovernor(), executor=lambda request: called.append(request.capability))
    result = gateway.execute(_request("system.config"), GovernorContext(autonomy_level=10))
    assert result.status is ExecutionResultStatus.APPROVAL_REQUIRED
    assert called == []
    assert result.metadata["governance_decision"] == "require_approval"


def test_unknown_request_requires_approval_and_never_reaches_executor() -> None:
    called: list[str] = []
    gateway = ExecutionGateway(SafetyGovernor(), executor=lambda request: called.append(request.capability))
    result = gateway.execute(_request("unknown.capability"), GovernorContext(autonomy_level=10))
    assert result.status is ExecutionResultStatus.APPROVAL_REQUIRED
    assert called == []
    assert result.metadata["governance_decision"] == "require_approval"


def test_allowed_request_reaches_executor_once() -> None:
    called: list[str] = []
    gateway = ExecutionGateway(
        SafetyGovernor(), executor=lambda request: called.append(request.capability) or {"ok": True}
    )
    result = gateway.execute(_request("filesystem.read"), GovernorContext(autonomy_level=10))
    assert result.status is ExecutionResultStatus.SUCCEEDED
    assert called == ["filesystem.read"]
    assert result.output == {"ok": True}


def test_missing_executor_is_normalized_and_does_not_fake_success() -> None:
    result = ExecutionGateway(SafetyGovernor()).execute(
        _request("filesystem.read"), GovernorContext(autonomy_level=10)
    )
    assert result.status is ExecutionResultStatus.UNKNOWN
    assert result.summary == "executor not configured"


def test_executor_exception_is_normalized_and_audited() -> None:
    events: list[tuple[str, str]] = []

    def executor(_request: ExecutionRequest) -> object:
        raise RuntimeError("secret implementation detail")

    gateway = ExecutionGateway(
        SafetyGovernor(),
        executor=executor,
        audit=lambda event, _request, detail: events.append((event, detail)),
    )
    result = gateway.execute(_request("filesystem.read"), GovernorContext(autonomy_level=10))
    assert result.status is ExecutionResultStatus.FAILED
    assert result.error == "RuntimeError"
    assert result.summary == "execution failed"
    assert "secret implementation detail" not in result.summary
    assert ("failed", "RuntimeError") in events


def test_verification_failure_preserves_evidence_and_does_not_claim_success() -> None:
    events: list[str] = []
    gateway = ExecutionGateway(
        SafetyGovernor(),
        executor=lambda _request: {"value": 42},
        verifier=lambda _request, _output: (False, ("postcondition-x", "observed-y")),
        audit=lambda event, _request, _detail: events.append(event),
    )
    result = gateway.execute(_request("filesystem.read"), GovernorContext(autonomy_level=10))
    assert result.status is ExecutionResultStatus.FAILED
    assert result.evidence == ("postcondition-x", "observed-y")
    assert "verification_failed" in events
    assert "executed" not in events


def test_successful_verification_is_audited_before_completion() -> None:
    events: list[str] = []
    gateway = ExecutionGateway(
        SafetyGovernor(),
        executor=lambda _request: "ok",
        verifier=lambda _request, output: (output == "ok", ("matched-output",)),
        audit=lambda event, _request, _detail: events.append(event),
    )
    result = gateway.execute(_request("filesystem.read"), GovernorContext(autonomy_level=10))
    assert result.status is ExecutionResultStatus.SUCCEEDED
    assert events == ["verified", "executed"]


def test_high_risk_can_execute_only_with_rollback_or_explicit_permission() -> None:
    policy = CapabilityPolicy(
        name="dangerous.action",
        risk=CapabilityRisk.HIGH,
        requires_explicit_approval=False,
        cross_project=False,
    )
    gateway = ExecutionGateway(
        SafetyGovernor({"dangerous.action": policy}),
        executor=lambda request: request.capability,
    )
    blocked = gateway.execute(
        _request("dangerous.action"), GovernorContext(autonomy_level=10, rollback_available=False)
    )
    assert blocked.status is ExecutionResultStatus.APPROVAL_REQUIRED
    allowed = gateway.execute(
        _request("dangerous.action"), GovernorContext(autonomy_level=10, rollback_available=True)
    )
    assert allowed.status is ExecutionResultStatus.SUCCEEDED
