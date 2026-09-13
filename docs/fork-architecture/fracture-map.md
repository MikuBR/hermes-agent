# Fracture Map v1

A fracture is a deliberate architectural seam that limits the amount of fork-specific code that must conflict with future upstream changes.

## F0 — Upstream foundation

Prefer upstream implementations for provider integrations, gateway/platform adapters, baseline CLI/TUI infrastructure, low-level compatibility, and stable primitives unless a concrete requirement justifies divergence.

Policy: `UPSTREAM-CLEAN` when possible.

## F1 — Agent runtime seam

Boundary around the main agent lifecycle, context assembly, tool execution, and session persistence.

Goal: allow the fork to add routing/planning/orchestration without rewriting every upstream entry point.

Classification: `UPSTREAM-STABLE` with adapters around it.

## F2 — Cognitive control seam

New fork-owned components:

- Task Classifier
- Cognitive Router
- Planner
- Orchestrator
- Agent Graph
- Model Router

Classification: `MIKU-CORE`.

## F3 — Execution governance seam

New fork-owned components:

- Safety Governor
- permission policy
- risk scoring
- approval presentation
- action audit
- loop/token/cost/time limits
- rollback coordination

Classification: `MIKU-CORE`; changes require strong regression testing.

## F4 — Memory and learning seam

New fork-owned interfaces for user, project, session, general, procedural, episodic/experiential, lesson, and error knowledge.

Classification: `MIKU-CORE` with provider adapters. External systems such as Segundo Cérebro remain optional integrations.

## F5 — Self-improvement seam

Own the lifecycle for proposals, experiments, validation, deployment, monitoring, and rollback.

Classification: `MIKU-CRITICAL`.

No self-improvement change becomes permanent merely because a model proposed it.

## F6 — User experience seam

Profiles for appearance, personality, interaction mode, verbosity, and other user-facing preferences.

Classification: `EXTENSION / PROFILE` where possible.

## F7 — Upstream synchronization seam

Independent mechanisms for inspecting upstream diffs, assessing architectural impact, simulating migration, testing, producing a plan, and waiting for user approval when needed.

Classification: `MIKU-CORE` but isolated from normal runtime behavior.

## Divergence labels

- `UPSTREAM-CLEAN` — no meaningful local divergence.
- `UPSTREAM-STABLE` — local adapter/interface wraps upstream behavior.
- `MIKU-EXTENSION` — optional local capability.
- `MIKU-CORE` — fork-specific core subsystem.
- `MIKU-CRITICAL` — safety, persistence, self-modification, or migration subsystem.
- `TEMPORARY-PATCH` — short-lived compatibility workaround.

## Rule

When a requirement can be satisfied at a seam or extension point, do not create unnecessary divergence inside upstream code.