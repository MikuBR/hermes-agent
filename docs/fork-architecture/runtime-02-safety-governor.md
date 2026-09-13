# Runtime 2 — Safety Governor

Status: implementation started; integration disabled.

## Mission

Provide one deterministic authorization point for consequential execution. The Governor decides whether an already-normalized request may proceed; it never executes the request.

## Decision states

- `allow`: low-risk, bounded action.
- `allow_with_audit`: permitted but must produce an audit event.
- `require_approval`: execution is paused pending explicit authorization.
- `deny`: execution must not reach the executor.

## Inputs

The production adapter will eventually provide capability metadata, autonomy level, explicit permission, project confidence, reversibility, rollback availability, blast radius, external side effects, data sensitivity, and project boundary information.

## Invariants

1. Autonomy is not permission.
2. Unknown capabilities never silently execute.
3. Ambiguous project context cannot authorize execution.
4. Cross-project actions require explicit permission.
5. Critical capabilities require explicit approval unless a separately validated policy says otherwise.
6. The Governor has no executor dependency.
7. Existing low-level tool guardrails remain active.

## Integration strategy

The pure Governor is implemented first. Integration will later occur at the normalized execution boundary, initially wrapping the existing Hermes dispatch path. No individual tool should gain bespoke governance logic.

## Acceptance gates

- Unit policy matrix passes.
- Deny/approval paths are proven unable to reach execution in integration tests.
- Decisions are auditable without persisting secrets.
- Existing tool behavior is unchanged while Governor integration is disabled.
- Shadow mode agrees with expected legacy behavior for safe operations.

## Future hardening

- Replace ad-hoc capability metadata with the canonical Runtime 0 capability contract.
- Add configurable policy profiles.
- Add explicit approval tokens with expiry and scope.
- Add project-boundary enforcement at the Execution Gateway.
- Add adversarial tests for confused-deputy and cross-project scenarios.
