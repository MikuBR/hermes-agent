# Runtime 7 — Rollback

Runtime 7 establishes a dormant rollback control plane with explicit safety boundaries.

## Invariants

- Checkpoint creation does not mutate the target through the core layer.
- Dry-run rollback never invokes a restore adapter.
- Restoration is successful only after post-restore verification passes.
- A verified rollback is idempotent and will not restore the same checkpoint twice.
- Checkpoint metadata is bounded and thread-safe.
- Concrete filesystem, Git, process, and deployment restoration remain adapters outside this core.

## Integration boundary

No automatic checkpoints, Execution Gateway wiring, destructive restoration policy, or deployment behavior is introduced here. Integration requires a later guarded rollout with explicit verification and audit evidence.

## Validation gate

The phase requires focused rollback regression tests and repository CI on the PR merge ref. CI infrastructure fixes must be validated on the current merge ref rather than relying on an older queued run. The legacy executor and human review gate remain untouched.
