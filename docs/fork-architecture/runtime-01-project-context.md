# Runtime 1 — Project Context Resolver

Status: implementation started; integration disabled.

## Purpose

Provide a deterministic project/session identity before the control plane makes decisions. Project identity is an isolation boundary for memory, tasks, agents, artifacts, permissions, learning, and rollback.

## Resolution precedence

1. Explicit project selection
2. Existing session project identity
3. Git root
4. Worktree root
5. Profile identity
6. Parent/lineage identity
7. Advisory context
8. Canonical cwd
9. Explicit `unknown` state

Advisory signals can support a decision but cannot override authoritative signals.

## Invariants

- Same canonical repository root produces the same local project identifier.
- Different roots produce different identifiers.
- Conflicting authoritative identities become `ambiguous=True` rather than being silently resolved.
- A child task can inherit project and lineage identity.
- The resolver does not read or write memory.
- The resolver does not execute commands.
- The resolver does not change the existing Hermes lifecycle.

## Boundary model

`ProjectContext.boundary` identifies the filesystem scope that later governance and execution layers must respect. The context object itself does not enforce that boundary; Runtime 2/5 will consume it as policy input.

## Integration plan

The first integration seam is the existing initialization lifecycle (`agent/agent_init.py` / `run_agent.py`). Integration will be introduced only after the pure resolver passes repository CI and an isolated integration test demonstrates that legacy behavior is unchanged when the resolver is disabled.

## Next hardening

- Add repository/worktree discovery adapter without embedding Git subprocesses in the pure resolver.
- Define explicit project-selection persistence contract.
- Define child-agent lineage inheritance adapter.
- Add ambiguity policy consumed by the Safety Governor.
- Add integration and regression tests in the actual Hermes initialization path.
