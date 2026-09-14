"""Canonical governed execution boundary for the fork-owned runtime.

The gateway is deliberately adapter-driven: it owns authorization ordering and
normalization, while concrete Hermes execution remains injected and dormant.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from hermes_core.governance.governor import (
    GovernanceDecision,
    GovernorContext,
    SafetyGovernor,
)

from .request import ExecutionRequest
from .result import ExecutionResult, ExecutionResultStatus


class ExecutionAdapter(Protocol):
    """Callable boundary for an existing or future concrete executor."""

    def __call__(self, request: ExecutionRequest) -> Any: ...


class VerificationAdapter(Protocol):
    """Optional post-execution verifier consumed by a later verification layer."""

    def __call__(
        self, request: ExecutionRequest, output: Any
    ) -> tuple[bool, tuple[str, ...]]: ...


class AuditSink(Protocol):
    """Optional bounded audit sink; the gateway never owns persistent storage."""

    def __call__(self, event: str, request: ExecutionRequest, detail: str) -> None: ...


@dataclass(frozen=True)
class ExecutionGateway:
    """Single choke point between governance and concrete execution.

    Ordering is intentional and load-bearing:

    1. evaluate governance;
    2. stop immediately for deny/approval-required;
    3. require an injected executor;
    4. execute exactly once;
    5. optionally verify and preserve evidence;
    6. optionally emit audit events.

    The gateway does not retry execution and does not mutate the request.
    """

    governor: SafetyGovernor
    executor: ExecutionAdapter | None = None
    verifier: VerificationAdapter | None = None
    audit: AuditSink | None = None

    def execute(
        self, request: ExecutionRequest, context: GovernorContext
    ) -> ExecutionResult:
        decision = self.governor.evaluate(request, context)

        if decision.decision is GovernanceDecision.DENY:
            self._audit("denied", request, decision.reason)
            return ExecutionResult(
                request.request_id,
                ExecutionResultStatus.BLOCKED,
                decision.reason,
                metadata={"governance_decision": decision.decision.value},
            )

        if decision.decision is GovernanceDecision.REQUIRE_APPROVAL:
            self._audit("approval_required", request, decision.reason)
            return ExecutionResult(
                request.request_id,
                ExecutionResultStatus.APPROVAL_REQUIRED,
                decision.reason,
                metadata={"governance_decision": decision.decision.value},
            )

        if self.executor is None:
            reason = "executor not configured"
            self._audit("executor_missing", request, reason)
            return ExecutionResult(
                request.request_id,
                ExecutionResultStatus.UNKNOWN,
                reason,
                metadata={"governance_decision": decision.decision.value},
            )

        try:
            output = self.executor(request)
        except Exception as exc:
            self._audit("failed", request, type(exc).__name__)
            return ExecutionResult(
                request.request_id,
                ExecutionResultStatus.FAILED,
                "execution failed",
                error=type(exc).__name__,
                metadata={"governance_decision": decision.decision.value},
            )

        if self.verifier is not None:
            try:
                verified, evidence = self.verifier(request, output)
            except Exception as exc:
                self._audit("verification_error", request, type(exc).__name__)
                return ExecutionResult(
                    request.request_id,
                    ExecutionResultStatus.FAILED,
                    "execution verification failed",
                    output,
                    error=type(exc).__name__,
                    metadata={"governance_decision": decision.decision.value},
                )
            if not verified:
                self._audit("verification_failed", request, "verification rejected output")
                return ExecutionResult(
                    request.request_id,
                    ExecutionResultStatus.FAILED,
                    "execution verification failed",
                    output,
                    evidence=evidence,
                    metadata={"governance_decision": decision.decision.value},
                )
            self._audit("verified", request, "execution output verified")

        self._audit("executed", request, decision.reason)
        return ExecutionResult(
            request.request_id,
            ExecutionResultStatus.SUCCEEDED,
            "execution completed",
            output,
            metadata={"governance_decision": decision.decision.value},
        )

    def _audit(self, event: str, request: ExecutionRequest, detail: str) -> None:
        if self.audit is not None:
            self.audit(event, request, detail)
