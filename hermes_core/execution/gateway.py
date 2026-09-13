"""Single execution boundary. Adapters inject legacy executor, verifier and audit sinks."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any
from .request import ExecutionRequest
from .result import ExecutionResult, ExecutionResultStatus
from hermes_core.governance.governor import SafetyGovernor, GovernorContext, GovernanceDecision

@dataclass
class ExecutionGateway:
    governor: SafetyGovernor
    executor: Callable[[ExecutionRequest], Any] | None = None
    verifier: Callable[[ExecutionRequest, Any], tuple[bool, tuple[str,...]]] | None = None
    audit: Callable[[str, ExecutionRequest, str], None] | None = None

    def execute(self, request: ExecutionRequest, context: GovernorContext) -> ExecutionResult:
        decision = self.governor.evaluate(request, context)
        if decision.decision in {GovernanceDecision.DENY, GovernanceDecision.REQUIRE_APPROVAL}:
            status = ExecutionResultStatus.BLOCKED
            if self.audit: self.audit(decision.decision.value, request, decision.reason)
            return ExecutionResult(request.request_id, status, decision.reason)
        if self.executor is None:
            return ExecutionResult(request.request_id, ExecutionResultStatus.UNKNOWN, "executor not configured")
        try:
            output = self.executor(request)
            if self.verifier:
                ok, evidence = self.verifier(request, output)
                if not ok:
                    return ExecutionResult(request.request_id, ExecutionResultStatus.FAILED, "execution verification failed", output, evidence=evidence)
            if self.audit: self.audit("executed", request, decision.reason)
            return ExecutionResult(request.request_id, ExecutionResultStatus.SUCCEEDED, "execution completed", output)
        except Exception as exc:
            if self.audit: self.audit("failed", request, type(exc).__name__)
            return ExecutionResult(request.request_id, ExecutionResultStatus.FAILED, "execution failed", error=type(exc).__name__)
