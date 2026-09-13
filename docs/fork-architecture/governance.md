# Governance, Autonomy and Rollback v1

## Autonomy model

The fork supports ten capability levels. Capability does not equal unconditional permission.

1. Observe and reason.
2. Use read-only tools.
3. Perform reversible file changes.
4. Execute controlled commands.
5. Modify project artifacts.
6. Modify infrastructure with appropriate permissions.
7. Modify Hermes-related components.
8. Create or modify skills/plugins/agents.
9. Install or modify dependencies under governed policy.
10. Perform governed self-improvement cycles.

## Safety Governor

Before consequential execution, evaluate:

- capability requested;
- risk class;
- permission source;
- reversibility;
- blast radius;
- confidence;
- rollback availability;
- external side effects;
- data sensitivity.

The result is an execution policy: allow, allow-with-log, require-approval, or deny.

## Human brakes

High-risk operations must produce an approval record before execution. The user can choose an expert presentation or a beginner-friendly explanation.

Beginner mode should show:

- the action/command;
- what it does in plain language;
- why Hermes wants to do it;
- immediate expected consequence;
- relevant risk;
- rollback availability.

## Rollback

Rollback is a first-class infrastructure concern.

```text
checkpoint -> execute -> verify -> commit
                     \-> fail -> rollback
```

Possible checkpoint backends include git worktrees/commits, filesystem backups, database backups, configuration snapshots, and versioned plugins/skills. The mechanism must be selected according to the resource being changed.

## Verification

A successful process exit is not enough. Actions should be verified against the intended outcome whenever technically possible.

## Self-modification

Self-modification follows:

```text
observe -> diagnose -> research -> propose -> isolate -> implement -> test -> adversarial QA -> compare -> approve -> deploy -> monitor
```

The old state must remain recoverable until the new state passes its acceptance criteria.

## Agent-loop controls

Nested agents are allowed, but all agent execution is bounded by maximum depth, calls, tokens/context, cost, time, and loop/repetition detection. Quality of final outcome takes priority over blindly minimizing calls.