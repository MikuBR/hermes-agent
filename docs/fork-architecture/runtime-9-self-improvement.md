# Runtime 9 — Self-Improvement

Runtime 9 establishes the fork-owned self-improvement lifecycle as a control plane. It does not autonomously modify the repository or deploy changes in this phase.

## Lifecycle

`observe → diagnose → research → propose → isolate → implement → test → adversarial QA → compare → approve → deploy → monitor → learn`

Runtime 9 records observations and evidence, admits proposals into isolated experiments, and requires passing regression and adversarial checks before a proposal can become `verified`.

Deployment remains behind an explicit approval decision with a non-empty human reason. A deployed proposal must pass post-deployment monitoring before its outcome can be learned. Failed experiments, failed adversarial checks, and unhealthy deployments cannot silently progress.

## Human brakes

The manager never executes code, changes files, selects production targets, or deploys an artifact. Those are adapter-owned operations. The core only decides whether the next lifecycle transition is admissible from the evidence already recorded.

This preserves the project's autonomy goal without creating an implicit self-modification or self-deployment path.

## Relationship with prior runtimes

- Runtime 5 supplies governed execution boundaries.
- Runtime 6 supplies verification and audit evidence.
- Runtime 7 supplies rollback/checkpoint primitives.
- Runtime 8 supplies scoped memory/learning with anti-contamination rules.
- Runtime 9 composes those concepts at the policy level but does not wire them into legacy runtime flow yet.

## Safety boundaries

- Bounded in-memory observations/proposals.
- Explicit experiment result with verification, regression, and adversarial evidence.
- Explicit approval required before deployment.
- Post-deploy health gate before learning.
- No automatic promotion into persistent memory in this phase.
- No automatic repository mutation or deployment.
- Existing human review gates remain untouched.

## Validation gate

Focused lifecycle regression tests and repository CI are required before considering Runtime 9 structurally complete. Guarded runtime integration comes later, after the stacked Runtime 5–9 control planes have independently passed validation.
