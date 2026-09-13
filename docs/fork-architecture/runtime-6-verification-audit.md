# Runtime 6 — Verification + Audit

## Scope

Runtime 6 introduces a fork-owned verification and audit plane without wiring it into the legacy executor or changing existing Hermes lifecycle behavior.

## Verification

Verification is separate from execution success. A result may be `verified`, `partially_verified`, `failed`, or `not_run`.

A verifier must not mutate the output under verification. Individual check exceptions become failed claims and never count as successful evidence.

## Audit

Audit records use the canonical `AuditEvent` contract. The in-memory recorder is bounded and thread-safe. Metadata is sanitized before retention: secret-looking keys are redacted, nested structures are bounded, and summaries/values are capped.

## Integration boundary

Runtime 6 remains dormant until a later guarded rollout wires verification and audit into the Execution Gateway. The legacy Hermes executor remains untouched in this phase.
