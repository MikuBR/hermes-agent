# Runtime 7 — Rollback

## Scope

Runtime 7 establishes a dormant rollback control plane. It defines checkpoint metadata, bounded retention, dry-run planning, idempotent verified restoration, and a narrow adapter boundary for actual target mutation.

## Safety invariants

- Creating a checkpoint does not mutate the target through the core control plane.
- Dry-run rollback never invokes the restore adapter.
- Restoration is not reported as successful until post-restore verification passes.
- A verified rollback is idempotent and does not invoke the restore adapter again.
- Checkpoint metadata retention is bounded and thread-safe.
- The core layer does not implement filesystem, Git, process, or deployment restoration itself.

## Integration boundary

The rollback plane is intentionally dormant. Execution Gateway wiring, automatic checkpoints, and destructive restoration policies remain future guarded integration work.

## Validation gate

Runtime 7 requires focused regression tests plus repository CI on the PR merge ref. It must not change the legacy executor or bypass the repository human-review gate.
