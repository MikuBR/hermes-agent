# Runtime 8 — Memory + Learning

Runtime 8 establishes a dormant fork-owned memory/learning control plane. It models memory as scoped claims rather than treating every model statement or session output as durable truth.

## Scope model

- `global`: reusable knowledge not tied to a user or project.
- `user`: preferences/facts bound to one user identity.
- `project`: knowledge bound to one project identity.
- `session`: ephemeral knowledge bound to one conversation session.

Project and session records are never returned by recall for unrelated projects or sessions. User records require the matching user identity.

## Learning lifecycle

Session-end extraction is adapter-owned. The control plane accepts a `LearningCandidate`, records provenance/evidence, and does not promote it automatically. Supporting and contradicting evidence can be added independently.

Normal promotion requires at least two supporting observations and confidence of at least 0.80. Any contradiction blocks promotion until a later policy explicitly resolves it.

A project-associated candidate cannot become user/global knowledge merely because a model is confident. Generalization needs explicit authorization, stronger support/confidence, and evidence spanning at least two projects. This prevents one project's conventions or mistakes from becoming global memory.

## Safety boundaries

- Bounded, thread-safe in-memory state in this phase.
- No automatic writes into `MEMORY.md`, `USER.md`, external providers, or existing memory tools.
- No LLM calls are hidden inside the store or promotion policy.
- Provenance, confidence, and evidence remain attached to every learned record.
- Persistence, encryption, retention policy, semantic retrieval, and provider adapters are later integration work.

## Upstream relationship

Upstream Hermes already has `MemoryProvider`/`MemoryManager` lifecycle hooks, persistent built-in memory, and optional external provider plugins. Runtime 8 deliberately sits beside that system first so the fork can validate isolation and learning policy before replacing or intercepting legacy memory behavior.

## Validation gate

The phase requires focused memory/learning regression tests, repository CI on the PR merge ref, and later guarded integration with Verification, Audit, Rollback, and the approval governor. No automatic promotion or legacy memory rewiring is introduced here.
