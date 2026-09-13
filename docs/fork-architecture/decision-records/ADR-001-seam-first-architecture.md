# ADR-001 — Fork Architecture Strategy

- Status: Accepted
- Date: 2026-09-13
- Scope: MikuBR Hermes fork
- Upstream base: NousResearch/hermes-agent

## Context

The fork must evolve from the upstream Hermes implementation into an independently controlled personal agent without sacrificing upstream compatibility, stability, rollback, or existing functionality.

The codebase is already modular in several important areas: `AIAgent` is decomposed through mixins and initialization helpers; tool registration is centralized; delegation is split across multiple modules; memory has a provider contract; state persistence has dedicated modules; gateway and protocol surfaces are separated.

A wholesale rewrite would create unnecessary divergence and make upstream synchronization harder.

## Decision

Adopt a **seam-first, additive architecture**.

The fork will introduce policy and orchestration layers around stable upstream capabilities instead of immediately replacing them.

### Target layers

1. Experience Layer — CLI, TUI, Gateway, ACP, API and cron adapters.
2. Hermes Core — existing conversation/session/tool runtime.
3. Cognitive Router — chooses direct response, planning, research, mapping, coding, browser/CU, QA or composed execution.
4. Agent Orchestrator — manages graph execution and delegates to isolated agents.
5. Model Router — selects providers/models according to policy and runtime evidence.
6. Safety Governor — evaluates authority, risk, permissions, reversibility, blast radius, confidence and rollback before execution.
7. Execution Plane — existing registry/toolsets/tools and external capabilities.
8. Verification Plane — checks whether intended effects actually occurred.
9. Memory/Learning Plane — scoped memory, provenance, session learning and conditional lessons.
10. Rollback/Audit Plane — snapshots, recovery, audit trail and change provenance.
11. Upstream Integration Plane — safe upstream analysis, migration planning and compatibility verification.

## Why this architecture

- Minimizes upstream conflicts.
- Preserves existing tool and provider contracts.
- Gives the fork explicit control over high-level cognition and governance.
- Allows progressive migration from upstream-derived internals to independently owned interfaces.
- Makes high-risk behavior auditable and reversible.
- Prevents platform-specific entry points from bypassing global safety policy.

## Consequences

### Positive

- Smaller initial changes.
- Easier regression testing.
- Clear ownership boundaries.
- Better upstream diff classification.
- Independent evolution of cognition without rewriting every adapter.

### Negative

- Transitional architecture will temporarily contain compatibility façades and multiple layers.
- Some upstream modules are large and highly coupled; extracting interfaces will require staged refactors.
- Governance must be inserted carefully so existing behavior remains compatible.

## Non-goals for the first phase

- No wholesale rewrite of `run_agent.py`.
- No replacement of the tool registry.
- No immediate replacement of the existing memory/state database.
- No blind upstream merge automation.
- No automatic modification of `main`.

## Migration rule

When a new fork capability can be implemented as an adapter, policy object, hook, interface or separate module, prefer that over modifying a large upstream module directly.

Direct modification is justified when the behavior is intrinsically part of the core runtime or when an explicit compatibility limitation is documented.

## Exit criterion for this ADR

This strategy remains valid until the fork has stable interfaces for runtime, governance, orchestration, model routing, memory/learning, verification and rollback. At that point individual upstream modules may be replaced behind those interfaces without changing external contracts.
