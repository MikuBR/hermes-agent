# Integration & Validation Phase — Runtime Architecture

Status: phase started; no production runtime is enabled by this document.

## Objective

Turn the independently implemented Runtime blocks into one verifiable control plane without making the existing Hermes path depend on unproven code. Integration is progressive, observable, reversible, and gated by CI and explicit human approval.

## Phase gates

### Gate 0 — Stack integrity

- Normalize PR dependency order.
- Keep `main` untouched.
- Ensure each runtime remains independently reviewable.
- Detect duplicate/conflicting contracts before integration.

### Gate 1 — Deterministic validation

- Import all `hermes_core` modules.
- Run focused Runtime tests.
- Run full Python test suite.
- Run lint/type/static checks already required by the repository.
- Run security/supply-chain checks for affected Python changes.
- Validate that no existing Hermes module imports `hermes_core` unless explicitly marked as an integration adapter.

### Gate 2 — Aggregate staging

Build a single integration candidate through the stacked PR chain. Validate that the full tree imports and that cross-runtime contracts agree.

Required invariants:

- no circular dependency from legacy Hermes into `hermes_core` outside adapters;
- no executor access from pure policy/decision modules;
- project identity is attached to consequential work;
- governance precedes execution;
- verification follows execution;
- audit does not become a secret store;
- rollback remains available before automatic mutation is enabled;
- self-improvement cannot authorize itself.

### Gate 3 — Shadow mode

Introduce opt-in shadow evaluation. New Context, Cognitive Router, Model Router and Governor compute predicted decisions beside legacy behavior without changing execution.

Record only bounded, secret-free comparison data:

- predicted decision;
- legacy outcome category;
- project id;
- capability/model category;
- latency class;
- mismatch reason.

Shadow mode must never execute a second side effect merely to compare behavior.

### Gate 4 — Guarded execution

Enable one execution seam at a time behind an explicit feature flag/configuration. Start with low-risk, reversible operations. Legacy execution remains the fallback for unsupported operations.

Every enabled action passes:

`Context -> Request normalization -> Governor -> Approval when required -> Executor -> Verification -> Audit`.

### Gate 5 — Failure injection

Exercise denial, ambiguity, executor failure, provider failure, cancellation, timeout, missing rollback, verification failure, stale approval, project-boundary violation and partial multi-agent failure.

Expected result is controlled degradation, not silent continuation.

### Gate 6 — Production-readiness review

Only after the above gates pass:

- review integration diffs;
- verify rollback from the candidate;
- compare legacy and fork behavior for representative workflows;
- promote selected seams from guarded to default;
- leave self-improvement production mutation disabled until a separate explicit review.

## Integration order

`Contracts -> Project Context -> Request/Result -> Capability/Lineage -> Model Router -> Cognitive Router -> Orchestrator -> Execution Gateway -> Verification/Audit -> Rollback -> Memory/Learning -> Compatibility -> Self-Improvement`.

## CI requirements

The repository's existing CI orchestrator already runs Python tests and linting on Python changes. This phase adds a focused Runtime validation lane rather than duplicating the whole CI system.

Required Runtime lane:

1. Compile/import `hermes_core`.
2. Run all `tests/test_runtime_*.py`.
3. Run a dependency-direction guard that rejects legacy imports of `hermes_core` except approved adapters.
4. Run serialization/contract smoke checks.
5. Emit a machine-readable validation summary.

The lane must not receive secrets and must execute untrusted PR code only through the normal `pull_request` security model.

## Human brakes

No stage automatically merges a runtime into `main` merely because CI is green. A green build proves technical checks, not authorization to change the production control plane.

High-impact integration remains explicitly reviewable. Self-improvement never receives an implicit deployment capability from lower layers.

## Rollback policy

Every guarded integration has:

- a feature flag/config switch;
- a known legacy fallback;
- a checkpoint/rollback strategy where mutation is possible;
- post-change verification;
- an audit event describing activation/deactivation.

## Success criteria

The phase is complete only when the integrated candidate can be tested as one tree, denies unsafe operations deterministically, verifies successful operations, preserves project isolation, and can revert to the legacy path without data loss or silent policy bypass.
