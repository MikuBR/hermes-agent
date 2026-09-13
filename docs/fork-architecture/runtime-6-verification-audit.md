# Runtime 6 — Verification + Audit

## Scope

Runtime 6 adds a fork-owned verification and audit plane without wiring it into the legacy executor or changing existing Hermes lifecycle behavior.

## Verification

Verification is independent from execution status. Results are `verified`, `partially_verified`, `failed`, or `not_run`. Checks must not mutate the output; exceptions become failed claims and never count as evidence of success.

## Audit

Audit records use the canonical `AuditEvent` contract. The recorder is bounded and thread-safe. Secret-looking metadata keys are redacted, nested structures are bounded, and large values are truncated before retention.

## Integration boundary

This phase remains dormant until a later guarded rollout wires verification and audit into the Execution Gateway. The existing executor remains untouched in this phase.
