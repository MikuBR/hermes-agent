# Dependency & Data-Flow Map — Fork Architecture

Status: architecture analysis only. No runtime behavior is changed by this document.

## 1. Primary execution flow

```text
User / platform
    ↓
Experience adapter (CLI/TUI/Gateway/ACP/API/cron)
    ↓
AIAgent lifecycle
    ↓
Context + memory preparation
    ↓
Model/provider route
    ↓
Model response
    ↓
Tool-definition resolution
    ↓
Tool-call guard / future Safety Governor
    ↓
Approval policy (when required)
    ↓
Registry dispatch
    ↓
Tool handler / external capability
    ↓
Result classification + verification
    ↓
Conversation/session persistence
    ↓
User-visible result + audit metadata
```

## 2. Multi-agent flow

```text
Primary AIAgent
   ↓
Cognitive Router (planned)
   ├─ direct answer
   ├─ Planner
   ├─ Researcher
   ├─ Mapper
   ├─ Coder
   ├─ Browser / Computer Use
   ├─ QA / verifier
   └─ composed graph
          ↓
     Agent Orchestrator (planned)
          ↓
     delegate_task execution fabric
          ↓
     isolated child AIAgent(s)
          ↓
     result + provenance + confidence
          ↓
     parent verification / synthesis
```

The current delegation stack already separates child lifecycle, dispatch, progress, registry/control, results, tasks and toolset resolution. The fork should therefore wrap and govern it rather than duplicate it.

## 3. Tool flow

`tools.registry` is the central capability registry. `model_tools.py` resolves model-visible definitions and bridges dispatch, including async execution. Individual tool modules register themselves.

Target fork boundary:

```text
Tool request
   ↓
Canonical call representation
   ↓
Capability metadata
   ↓
Safety Governor
   ├─ permission
   ├─ autonomy level
   ├─ risk
   ├─ blast radius
   ├─ reversibility
   ├─ confidence
   └─ approval requirement
   ↓
Approval / deny / allow-with-log
   ↓
Existing registry dispatch
   ↓
Result classifier
   ↓
Verification policy
   ↓
Audit + memory/learning hooks
```

## 4. Context and memory flow

```text
Incoming turn
   ↓
Project Context Resolver (planned)
   ├─ explicit project
   ├─ git repository
   ├─ cwd/workspace
   ├─ branch
   ├─ project metadata
   └─ contextual signals
   ↓
Scope selection
   ├─ session
   ├─ project
   ├─ global/user
   └─ external optional
   ↓
MemoryProvider lifecycle
   ↓
Prefetch / context injection
   ↓
Model turn
   ↓
Session persistence
   ↓
Session-end learning pipeline (planned)
```

Keywords must never be the sole project selector. Ambiguous context should remain session-local rather than being promoted into project/global memory.

## 5. Learning flow

```text
Completed session
   ↓
Observe evidence
   ↓
Separate fact / preference / decision / failure / hypothesis
   ↓
Diagnose root cause
   ↓
Generalize conditionally
   ↓
Validate against existing knowledge
   ↓
Choose scope
   ↓
Persist with provenance
   ↓
Future retrieval
```

Anti-trauma invariant: a failed strategy becomes a conditional lesson tied to the conditions that produced the failure, not an unconditional prohibition.

## 6. Self-improvement flow

```text
Observe
  ↓
Diagnose
  ↓
Research
  ↓
Propose
  ↓
Isolate
  ↓
Implement
  ↓
Unit/integration/regression/security/upstream tests
  ↓
Adversarial QA
  ↓
Compare against baseline
  ↓
Approval gate
  ↓
Deploy
  ↓
Monitor
  ↓
Learn
```

Self-modification must operate through the same Safety Governor and rollback infrastructure as ordinary high-impact changes.

## 7. Dependency-direction rules

### Allowed high-level direction

- Experience adapters may call the core/runtime.
- Core may call cognitive policy interfaces.
- Cognitive policy may request agents/tools through orchestrator interfaces.
- Governance may inspect requests and authorize execution.
- Tool implementations may depend on low-level utilities and external services.
- State/memory may record execution, but storage must not become the owner of cognitive policy.
- Provider adapters implement provider contracts; they must not own global routing policy.

### Forbidden architectural shortcuts

- Platform adapter directly bypassing Safety Governor for a capability with side effects.
- Provider adapter deciding global agent strategy.
- Tool handler directly mutating project/global memory without provenance.
- Child agent silently escalating its authority beyond inherited policy.
- Planner directly executing privileged operations without the same tool governance path.
- Project resolver using keywords as authoritative identity.

## 8. Highest-risk dependency clusters

1. `run_agent.py` ↔ `agent/*` — central runtime coupling.
2. `model_tools.py` ↔ `tools.registry` ↔ tool modules — capability dispatch.
3. `tools/delegate_tool*` ↔ `run_agent.py` — multi-agent lifecycle.
4. `hermes_state*` ↔ session/memory/context — persistence compatibility.
5. `gateway/*` ↔ runtime/state — long-lived concurrency and platform isolation.
6. provider/config/auth modules ↔ runtime — model route correctness.
7. updater/recovery modules ↔ installation/runtime — self-update blast radius.

These clusters should be changed only with focused commits and regression coverage.
