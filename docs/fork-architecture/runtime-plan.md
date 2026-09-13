# Runtime Creation Plan

Status: planning-only. No runtime behavior is enabled by this document.

## Goal
Create the fork-owned runtime/control plane without rewriting Hermes or changing default behavior before each seam is proven.

## Target topology

```text
Experience / Entry Point
        |
        v
Session + Project Context Resolver
        |
        v
Cognitive Router
        |
        +-------------------+
        |                   |
        v                   v
Direct Execution      Planner / Agent Orchestrator
                            |
                  Research / Mapper / Coder /
                     Browser / CU / QA / specialists
                            |
                            v
                     Execution Gateway
                     /               \
                    v                 v
             Safety Governor      Model Router
                    |                 |
                    +--------+--------+
                             v
                   Existing Hermes APIs
                    tools / AIAgent /
                   gateway / ACP / cron
                             |
                             v
                    Verification + Audit
                             |
                     Memory / Learning
                             |
                          Rollback
```

## Fork-owned namespace

Introduce an additive namespace rather than repurposing upstream modules:

```text
hermes_core/
  contracts.py
  runtime.py
  context/{models.py,resolver.py}
  cognition/{router.py,planner.py,policies.py}
  governance/{governor.py,approval.py,capabilities.py,risk.py}
  routing/{model_router.py,scoring.py,capabilities.py}
  orchestration/{orchestrator.py,graph.py,budgets.py,lifecycle.py}
  execution/{gateway.py,request.py,result.py}
  verification/{verifier.py,evidence.py}
  audit/{events.py,recorder.py}
  rollback/{manager.py,checkpoints.py}
  compatibility/{upstream.py,adapters.py}
```

The new namespace is additive. Existing Hermes modules remain the compatibility implementation during migration.

## Runtime 0 — contracts

Create stable data contracts first: `RuntimeContext`, `ProjectContext`, `Capability`, `ExecutionRequest`, `ExecutionDecision`, `ApprovalDecision`, `ModelRouteRequest`, `ModelRoute`, `AgentTask`, `AgentResult`, `VerificationResult`, `AuditEvent`, `Checkpoint`.

Dependency direction: `hermes_core` may consume stable upstream APIs; upstream modules must not depend on `hermes_core` during this phase.

Acceptance: deterministic serialization, import success, zero default behavior change, existing tests unchanged.

## Runtime 1 — Project Context Resolver

Resolve project identity from deterministic evidence first: explicit selection, Git root, canonical cwd, branch/worktree, profile, session lineage. Keywords are advisory only.

`ProjectContext` must carry stable id, confidence, evidence, source, workspace boundary, and lineage fields.

First integration seam: `agent/agent_init.py` / `run_agent.py` lifecycle, because initialization already centralizes ordered runtime assembly.

Acceptance: same repository gives the same project id; different repositories remain isolated even with similar keywords; ambiguity stays explicit instead of becoming a silent guess; child agents inherit project identity and lineage.

## Runtime 2 — Safety Governor

One deterministic authorization point before consequential execution. Inputs include capability, autonomy, explicit permission, risk, reversibility, blast radius, confidence, rollback availability, external side effects, data sensitivity, platform, and project boundary.

Outputs: `allow`, `allow_with_audit`, `require_approval`, `deny`.

Core invariant: autonomy never implies permission.

First choke point: `model_tools.py` around the existing registry/dispatch path. Evaluate normalized requests before dispatch; do not embed policy into each tool.

Keep `agent/tool_guardrails.py` active. The Governor composes with low-level loop protection rather than duplicating it.

Acceptance: pure policy matrix passes; `deny` and `require_approval` cannot reach the executor; approvals contain enough context for expert and beginner UX; decisions are auditable without leaking secrets.

## Runtime 3 — Model Router

Central policy layer above provider adapters. Inputs: task type, requested quality, tool support, context capacity, latency, reliability/history, free/freemium policy, privacy policy, provider availability, configured allow/deny/order, and fallback eligibility.

Outputs: provider, model, normalized route id, score breakdown, fallback chain, confidence.

Use the existing provider-resolution machinery; do not replace provider adapters.

Acceptance: deterministic route for equal inputs, no policy violations, unavailable providers skipped, fallback remains inside policy, explicit provider/config behavior stays compatible.

## Runtime 4 — Agent Orchestrator

Turn a user objective into an executable graph. Decide direct vs planned execution, select specialists, enforce dependencies, propagate budgets/cancellation, preserve lineage, and require verification where appropriate.

Treat the existing delegation implementation as a stable execution primitive. Relevant surfaces include `tools/delegate_tool.py` plus its child-run, config, dispatch, progress, registry, result, task, and toolset modules.

Acceptance: safe bounded tasks may execute directly; planned tasks preserve attribution; depth/child/token/time/context/loop budgets are enforced; cancellation propagates; every child result includes verification and attribution.

## Runtime 5 — Execution Gateway

Normalize actual execution into:

```text
ExecutionRequest
 -> capability normalization
 -> project boundary check
 -> Safety Governor
 -> approval
 -> Model Router when applicable
 -> existing executor
 -> result normalization
 -> Verification
 -> Audit
```

Initially wrap `model_tools.handle_function_call()` and delegation instead of moving implementation code.

## Runtime 6 — Verification + Audit

Separate "executed" from "verified". Minimum result states: `executed`, `verified`, `partially_verified`, `failed`, `blocked`, `cancelled`.

Attach evidence where practical: tests, file/change checksums or summaries, command exit codes, provider metadata, or human approval records. Keep audit payloads bounded, privacy-aware, and secret-free.

## Runtime 7 — Rollback

Rollback is infrastructure, not merely a Git helper. Define contracts for file/worktree restoration, config restoration, state/database checkpoints, safe session rewind, compound-operation rollback, pre-change metadata, and post-rollback verification.

First implementation should expose contracts and checkpoint semantics before enabling automatic rollback.

## Runtime 8 — Memory + Learning

Only after context, governance, verification, audit, and rollback are stable should learning become a control-plane function.

Pipeline: `observe -> diagnose -> generalize -> validate -> propose -> persist`.

Strict separation between session, project, global, reusable strategy, and environment-specific failure knowledge. The anti-trauma rule is mandatory: one failure does not become a global prohibition without evidence of generality.

Preserve the existing `agent/memory_provider.py` compatibility contract during migration.

## Runtime 9 — Self-improvement

Last to become capable of modifying production behavior:

`observe -> diagnose -> research -> propose -> isolate -> implement -> test -> adversarial QA -> compare -> approval -> deploy -> monitor -> learn`.

Existence of lower runtime layers must never implicitly enable self-modification.

## Rollout

**A — dormant:** contracts and pure runtime modules, no behavior change.

**B — shadow:** Project Context, Model Router, and Governor observe and record predicted decisions only.

**C — guarded:** one seam enabled at a time behind configuration; old execution remains the fallback.

**D — default:** enable after regression parity, integration coverage, and real smoke validation.

**E — decouple:** gradually migrate responsibilities out of upstream-heavy modules only after seams have proven stable.

## Implementation order

1. Contracts
2. Project Context Resolver
3. Execution request/result normalization
4. Safety Governor
5. Model Router
6. Agent Orchestrator
7. Execution Gateway
8. Verification/Audit
9. Rollback
10. Memory/Learning integration
11. Self-improvement

This ordering prevents autonomous mutation from outrunning the control, evidence, and recovery planes.

## Branch/PR policy

One focused branch/PR per runtime. Suggested names:

- `runtime/contracts-v1`
- `runtime/project-context-v1`
- `runtime/governor-v1`
- `runtime/model-router-v1`
- `runtime/orchestrator-v1`
- `runtime/execution-gateway-v1`
- `runtime/verification-audit-v1`
- `runtime/rollback-v1`
- `runtime/memory-learning-v1`

No runtime branch may silently rewrite unrelated upstream code. Cross-cutting changes require an explicit compatibility note.