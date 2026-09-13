# Runtime 6 — Verification + Audit

Runtime 6 adds a fork-owned verification and audit plane without wiring it into the legacy executor or changing existing Hermes lifecycle behavior.

## Verification

Verification is independent from execution status. Results are `verified`, `partially_verified`, `failed`, or `not_run`. Checks must not mutate the output; exceptions become failed claims.

## Audit

Audit records use the canonical `AuditEvent` contract. The recorder is bounded and thread-safe. Secret-looking metadata keys are redacted and nested/large values are bounded before retention.

## Integration boundary

The plane remains dormant until a guarded rollout wires it into the Execution Gateway. The existing executor remains untouched in this phase.
