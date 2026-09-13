"""Verification primitives: execution and verification are distinct states."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any
from hermes_core.contracts import VerificationResult, VerificationStatus

@dataclass(frozen=True)
class VerificationCheck:
    name: str
    check: Callable[[Any], bool]
    evidence: str = ""

class Verifier:
    def verify(self, output: Any, checks: tuple[VerificationCheck, ...]) -> VerificationResult:
        if not checks: return VerificationResult(VerificationStatus.NOT_RUN, verifier="none")
        failures=[]; evidence=[]; claims=[]
        for c in checks:
            try:
                ok=c.check(output)
            except Exception:
                ok=False
            if ok:
                claims.append(c.name)
                if c.evidence: evidence.append(c.evidence)
            else: failures.append(c.name)
        status = VerificationStatus.VERIFIED if not failures else (VerificationStatus.PARTIALLY_VERIFIED if claims else VerificationStatus.FAILED)
        return VerificationResult(status, tuple(claims), tuple(evidence), tuple(failures), "runtime.verifier")
