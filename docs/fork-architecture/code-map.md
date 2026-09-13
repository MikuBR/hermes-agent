# Code Map — Fork Architecture

Status: observed against `architecture/fork-foundation-v1` (upstream-derived baseline).

This document maps the planned fork architecture to concrete code surfaces. It is intentionally descriptive: no runtime behavior is changed by this mapping.

## 1. System entry and experience surfaces

| Area | Current surface | Planned role | Disposition |
|---|---|---|---|
| CLI entry | `hermes_cli/main.py` | command boundary, startup/recovery, orchestration entry | `UPSTREAM-STABLE`; keep thin |
| Interactive CLI | `cli.py`, `hermes_cli/*` | user interaction/config/commands | `UPSTREAM-STABLE`; add fork commands through extension seams |
| TUI | `ui-tui/`, `tui_gateway/` | rich interactive UX | `UPSTREAM-STABLE` initially |
| Gateway | `gateway/run.py`, `gateway/*` | persistent remote/channel runtime | `UPSTREAM-STABLE`; Safety Governor must apply below platform adapters |
| ACP | `acp_adapter/` | external agent protocol surface | `UPSTREAM-CLEAN`; keep protocol adapter independent of cognitive policy |
| Batch / SWE | `batch_runner.py`, `mini_swe_runner.py` | non-interactive execution surfaces | `UPSTREAM-STABLE`; reuse common governance |

## 2. Cognitive/runtime center

| Area | Current surface | Planned role | Disposition |
|---|---|---|---|
| Core agent object | `run_agent.py:AIAgent` | conversation/tool/session runtime | `MIKU-CORE` seam candidate; avoid replacing wholesale initially |
| Agent construction | `agent/agent_init.py` | ordered initialization pipeline | `MIKU-EXTENSION` seam; ideal injection point for project context, governance and model routing |
| Runtime helpers | `agent/agent_runtime_helpers.py` | shared runtime helper layer | `UPSTREAM-STABLE` until dependency graph is isolated |
| Conversation loop | `agent/conversation_loop.py` and related `agent/*` mixins | turn/iteration execution | `MIKU-CORE` long-term seam for Planner/Router/verification lifecycle |
| Context/compression | `agent/context_compressor.py`, `agent/conversation_compression.py`, `trajectory_compressor.py` | context budget and retention | `UPSTREAM-STABLE` initially; later expose policy interface |
| Iteration budget | `agent/iteration_budget.py` | local turn budget | `MIKU-EXTENSION` to become one input to global execution budget |
| Tool loop guard | `agent/tool_guardrails.py` | repeat/failure loop control | `MIKU-EXTENSION`; promote into global Safety Governor policy |

## 3. Delegation / multi-agent fabric

The current delegation implementation is already componentized:

- `tools/delegate_tool.py` — public orchestration façade and compatibility surface.
- `tools/delegate_tool_child_run.py` — child lifecycle.
- `tools/delegate_tool_config.py` — delegation/runtime config.
- `tools/delegate_tool_dispatch.py` — batch dispatch.
- `tools/delegate_tool_progress.py` — progress/events.
- `tools/delegate_tool_registry.py` — live child registry/control.
- `tools/delegate_tool_results.py` — result lifecycle/summarization.
- `tools/delegate_tool_tasks.py` — task normalization/schema handling.
- `tools/delegate_tool_toolsets.py` — child capability resolution.

Disposition: `MIKU-EXTENSION` rather than rewrite. Add a fork-level **Agent Orchestrator** above this fabric, preserving `delegate_task` as an execution primitive.

Required future controls:

1. max depth;
2. max children per parent/turn;
3. global active-agent cap;
4. token/time/context budgets;
5. cancellation propagation;
6. loop/cycle detection;
7. parent-child attribution;
8. approval authority inheritance;
9. project-context inheritance with explicit isolation;
10. result confidence and verification status.

## 4. Tool plane

`model_tools.py` is a thin orchestration layer over `tools.registry` and is therefore an important architectural seam.

- `tools/registry.py` — central tool discovery/registration/dispatch metadata.
- `model_tools.py` — tool definition resolution, dispatch bridge, async execution bridge.
- `toolsets.py`, `toolset_distributions.py` — capability grouping and distribution.
- `registration_lifecycle.py` — registration lifecycle coordination.

The registry is a strong **extension boundary** because built-in tools self-register and the model-facing schema is resolved centrally. The fork should add governance around dispatch rather than duplicate tool metadata.

Planned pipeline:

`model request → tool resolver → Safety Governor → approval policy → tool dispatch → result classification → verification/audit`

## 5. Memory/state plane

The codebase already has strong separation in state persistence:

- `hermes_state.py` — state façade/compatibility surface.
- `hermes_state_common.py` — shared state structures.
- `hermes_state_dbfile.py` — DB lifecycle/file handling.
- `hermes_state_schema.py` — schema definitions.
- `hermes_state_sessions.py` — sessions.
- `hermes_state_messages.py` — messages/transcript persistence.
- `hermes_state_fts.py`, `hermes_state_search.py` — search/FTS.
- `hermes_state_registry.py` — shared DB/resource acquisition.
- `hermes_state_rewind.py`, `hermes_state_repair.py` — recovery/rewind.
- `hermes_state_wal.py`, `hermes_state_readpool.py` — persistence/concurrency support.

`agent/memory_provider.py` defines an explicit pluggable provider contract with lifecycle hooks and optional external providers.

Disposition: `UPSTREAM-STABLE` for storage primitives. Add fork-level scope/learning metadata through additive schema evolution, not by breaking the existing session model.

## 6. Model/provider plane

- `providers/` — provider contracts and provider-facing definitions.
- `hermes_cli/providers*`, `hermes_cli/auth*`, `hermes_cli/models*` — provider selection/configuration surfaces.
- `agent/model_metadata.py` and request/adapter modules — model capability metadata and protocol adaptation.

Disposition: keep provider adapters independent. Add **Model Router** as a policy layer that consumes provider capabilities, user policy, historical success, latency, cost/free status, privacy and tool support. Do not embed routing logic in each provider adapter.

## 7. Gateway/platform plane

`gateway/run.py` owns long-lived runtime lifecycle and platform orchestration. Platform-specific modules should remain adapters. Safety/Governance must sit beneath the gateway and above executable capabilities, so the same rules apply to CLI, TUI, API, cron and messaging channels.

Disposition: `UPSTREAM-STABLE` runtime; `MIKU-EXTENSION` governance injection.

## 8. Fork-critical seams

The first implementation seams are:

1. `run_agent.AIAgent` lifecycle boundary.
2. `agent/agent_init.py` ordered initialization phases.
3. conversation/turn execution loop.
4. `tools.registry` / `model_tools.py` dispatch boundary.
5. delegation façade and child-run lifecycle.
6. memory provider contract + state persistence.
7. gateway lifecycle.
8. provider/model selection.
9. CLI update/upstream synchronization.

These seams minimize invasive changes while preserving the upstream code path.

## 9. First protected invariants

Before runtime refactoring, preserve:

- existing tool names and schemas unless a migration is explicit;
- existing session identifiers and persistence compatibility;
- provider configuration semantics;
- gateway platform isolation;
- delegation attribution and cancellation;
- startup/recovery behavior;
- rollback/recovery mechanisms already present;
- upstream updateability.

Any change that breaks one of these invariants must be classified as `MIKU-CRITICAL` and require an explicit migration plan.
