"""Independent verification primitives for fork-owned runtime execution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from hermes_core.contracts import VerificationResult, VerificationStatus


@dataclass(frozen=True)
class VerificationCheck:
    """A deterministic claim evaluated against an execution output."""

    name: str
    check: Callable[[Any], bool]
    evidence: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("verification check name must not be empty")


class Verifier:
    """Evaluate independent checks without mutating the verified output."""

    verifier_id = "runtime.verifier.v1"

    def verify(self, output: Any, checks: Iterable[VerificationCheck]) -> VerificationResult:
        checks_tuple = tuple(checks)
        if not checks_tuple:
            return VerificationResult(VerificationStatus.NOT_RUN, verifier=self.verifier_id)
        verified: list[str] = []
        failed: list[str] = []
        evidence: list[str] = []
        for check in checks_tuple:
            try:
                passed = bool(check.check(output))
            except Exception:
                passed = False
            if passed:
                verified.append(check.name)
                if check.evidence:
                    evidence.append(check.evidence[:1000])
            else:
                failed.append(check.name)
        status = (
            VerificationStatus.VERIFIED
            if not failed
            else VerificationStatus.PARTIALLY_VERIFIED
            if verified
            else VerificationStatus.FAILED
        )
        return VerificationResult(
            status=status,
            verified_claims=tuple(verified),
            evidence=tuple(evidence),
            failures=tuple(failed),
            verifier=self.verifier_id,
        )
