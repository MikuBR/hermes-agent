from hermes_core.audit import AuditRecorder, sanitize_metadata
from hermes_core.contracts import ExecutionStatus, VerificationStatus
from hermes_core.verification import VerificationCheck, Verifier


def test_verifier_not_run_without_checks() -> None:
    result = Verifier().verify(42, ())
    assert result.status is VerificationStatus.NOT_RUN


def test_verifier_verified_when_all_checks_pass() -> None:
    result = Verifier().verify(
        4,
        (
            VerificationCheck("positive", lambda value: value > 0, "value > 0"),
            VerificationCheck("even", lambda value: value % 2 == 0, "value % 2 == 0"),
        ),
    )
    assert result.status is VerificationStatus.VERIFIED
    assert result.verified_claims == ("positive", "even")
    assert result.failures == ()


def test_verifier_partial_and_failed_claims_are_explicit() -> None:
    result = Verifier().verify(
        3,
        (
            VerificationCheck("positive", lambda value: value > 0),
            VerificationCheck("even", lambda value: value % 2 == 0),
        ),
    )
    assert result.status is VerificationStatus.PARTIALLY_VERIFIED
    assert result.verified_claims == ("positive",)
    assert result.failures == ("even",)


def test_verifier_treats_check_exception_as_failure() -> None:
    def broken(_: object) -> bool:
        raise RuntimeError("internal failure")

    result = Verifier().verify(object(), (VerificationCheck("broken", broken),))
    assert result.status is VerificationStatus.FAILED
    assert result.failures == ("broken",)


def test_sanitize_metadata_redacts_nested_secrets_and_bounds_values() -> None:
    sanitized = sanitize_metadata(
        {
            "api_key": "super-secret",
            "nested": {"authorization": "Bearer secret", "safe": "ok"},
            "long": "x" * 5000,
        }
    )
    assert sanitized["api_key"] == "[REDACTED]"
    assert "[REDACTED]" in sanitized["nested"]
    assert len(sanitized["long"]) <= 1000


def test_audit_recorder_is_bounded_and_returns_contract_event() -> None:
    recorder = AuditRecorder(max_records=2)
    recorder.record("started", "user", request_id="r1")
    recorder.record(
        "completed",
        "user",
        request_id="r2",
        status=ExecutionStatus.EXECUTED,
        metadata={"token": "secret", "safe": "ok"},
    )
    recorder.record("verified", "user", request_id="r3")

    events = recorder.snapshot()
    assert len(events) == 2
    assert [event.request_id for event in events] == ["r2", "r3"]
    assert events[0].metadata["token"] == "[REDACTED]"
    assert recorder.latest() == events[-1]
