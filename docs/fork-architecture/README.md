# Hermes Fork Architecture

This directory defines the architectural direction of the MikuBR Hermes fork.

## Status

Architecture foundation v1. This is a planning and governance layer; implementation changes must follow the decisions documented here.

## Goals

- Preserve a healthy relationship with the upstream NousResearch Hermes project.
- Gradually introduce an independent cognitive and autonomous-agent architecture.
- Keep the system modular and replaceable at clear boundaries.
- Prioritize correctness, verification, rollback, stability, and user authority.
- Enable long-term migration from upstream dependence toward architectural independence.

## Core documents

- `architecture-map.md` — target system topology and responsibility boundaries.
- `fracture-map.md` — upstream/custom separation points.
- `governance.md` — autonomy, safety, permissions, approvals, rollback, and change control.
- `memory-learning.md` — project/user memory, experiential learning, and contamination prevention.
- `agent-system.md` — Router, Planner, Orchestrator, specialist agents, and model routing.
- `upstream-strategy.md` — safe upstream inspection, simulation, impact analysis, and migration policy.
- `roadmap.md` — implementation order and milestones.

## Foundational rule

The fork may diverge from upstream when necessary, but it must remain understandable, testable, reversible, and observable.