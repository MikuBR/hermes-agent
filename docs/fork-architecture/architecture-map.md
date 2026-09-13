# Architecture Map v1

## Target topology

```text
User
  |
  v
Experience Layer ---- profile / appearance / personality / preferences
  |
  v
Hermes Core ---- session / context / provider abstraction / tool runtime
  |
  v
Cognitive Router ---- intent / complexity / domain / required capabilities
  |                         |
  |                         +--> Direct execution
  v
Planner ---- goal / tasks / dependencies / evidence / state / validation
  |
  v
Agent Orchestrator / Agent Graph
  +--> Researcher
  +--> Mapper
  +--> Coder
  +--> Browser
  +--> Computer Use
  +--> QA / Verifier
  +--> future specialists
  |
  v
Execution Layer ---- tools / filesystem / terminal / browser / external systems
  |
  v
Verification Layer ---- assertions / tests / independent review / outcome checks
  |
  +-------------------+----------------------+------------------+
  |                   |                      |
  v                   v                      v
Memory & Learning   Rollback             Audit / Trace
  |                   |                      |
  +-------------------+----------------------+
                      v
               Self-Improvement
```

## Cross-cutting systems

### Safety Governor
Every consequential action is evaluated using capability, risk, permission, reversibility, blast radius, confidence, and available rollback.

### Model Router
Chooses the best currently available provider/model for a concrete task using quality, cost, free availability, privacy, latency, context capacity, tool support, reliability, and historical performance.

### Project Context Resolver
Determines which project/session/user scopes apply before retrieving memory. Ambiguous identity must not cause cross-project writes.

### Experience Pipeline
Completed sessions and important execution traces can be analyzed after the fact. Only validated, appropriately scoped lessons become persistent knowledge.

## Architectural priorities

1. Correctness and verification.
2. User authority and transparent control.
3. Rollback and reversibility.
4. Quality of final outcome.
5. Security and bounded autonomy.
6. Efficient use of context, tokens, latency, and free resources.
7. Modularity and maintainability.
8. Upstream survivability.
9. Progressive architectural independence.

## Dependency rule

Custom systems should consume stable interfaces from the core whenever practical. Core changes require explicit compatibility reasoning and regression coverage.