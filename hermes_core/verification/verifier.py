"""Independent verification primitives for fork-owned runtime execution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from hermes_core.contracts import VerificationResult, VerificationStatus


CheckCallable = Callable[[Any], bool]


@dataclass(frozen=True)
class VerificationCheck:
    """A deterministic claim that can be evaluated against an execution output."""

    name: str
    check: CheckCallable
    evidence: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("verification check name must not be empty")


class Verifier:
    """Run independent checks without changing the output under verification."""

    verifier_id = "runtime.verifier.v1"

    def verify(
        self,
        output: Any,
        checks: Iterable[VerificationCheck],
    ) -> VerificationResult:
        checks_tuple = tuple(checks)
        if not checks_tuple:
            return VerificationResult(
                status=VerificationStatus.NOT_RUN,
                verifier=self.verifier_id,
            )

        verified_claims: list[str] = []
        failures: list[str] = []
        evidence: list[str] = []

        for check in checks_tuple:
            try:
                passed = bool(check.check(output))
            except Exception:
                passed = False
            if passed:
                verified_claims.append(check.name)
                if check.evidence:
                    evidence.append(check.evidence[:1000])
            else:
                failures.append(check.name)

        if not failures:
            status = VerificationStatus.VERIFIED
        elif verified_claims:
            status = VerificationStatus.PARTIALLY_VERIFIED
        else:
            status = VerificationStatus.FAILED

        return VerificationResult(
            status=status,
            verified_claims=tuple(verified_claims),
            evidence=tuple(evidence),
            failures=tuple(failures),
            verifier=self.verifier_id,
        )
