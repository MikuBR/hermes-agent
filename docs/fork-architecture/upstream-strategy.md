# Upstream Strategy v1

## Relationship

The fork uses its own versioning while recording the upstream base commit/version as build metadata.

Conceptually:

```text
fork_version
upstream_version
upstream_commit
architecture_revision
```

## Safe update pipeline

```text
fetch upstream
  -> inspect diff
  -> classify changed areas
  -> map impact against fork fractures
  -> predict conflicts
  -> create isolated migration workspace
  -> apply/simulate migration
  -> run tests and regression suite
  -> generate compatibility report
  -> generate migration plan
  -> request user approval when required
  -> apply to fork
  -> verify
```

The fork must not blindly pull upstream changes into its working branch.

## Automatic conflict handling

The system may analyze and prepare a resolution, but consequential migration decisions must remain reviewable. For incompatible architectural changes, Hermes should report the conflict, explain the consequences, and present a migration plan rather than silently rewriting the fork.

## Independence trajectory

Phase 1: upstream-derived fork.

Phase 2: clear custom seams and fork-owned subsystems.

Phase 3: increasingly independent cognitive/runtime architecture.

Phase 4: upstream becomes an optional source of improvements rather than an architectural dependency.

## Stability rule

Upstream novelty must never outrank verified stability of the fork.