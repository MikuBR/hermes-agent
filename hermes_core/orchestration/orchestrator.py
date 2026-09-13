"""Bounded orchestration planner; execution is delegated to existing primitives."""
from __future__ import annotations
from dataclasses import dataclass
from hermes_core.contracts import AgentTask

@dataclass(frozen=True)
class OrchestrationPolicy:
    max_depth: int = 3
    max_children: int = 10
    max_tasks: int = 50
    max_tokens: int = 100_000
    max_context_tokens: int = 200_000
    require_plan_for: frozenset[str] = frozenset({"system.change", "multi_step", "research"})

@dataclass(frozen=True)
class TaskNode:
    task: AgentTask
    dependencies: tuple[str, ...] = ()

class AgentOrchestrator:
    def __init__(self, policy: OrchestrationPolicy | None = None):
        self.policy = policy or OrchestrationPolicy()

    def plan(self, objective: str, task_type: str = "general", project=None, parent_task_id=None) -> tuple[TaskNode, ...]:
        if not objective.strip(): raise ValueError("objective cannot be empty")
        root = AgentTask(task_type=task_type, objective=objective, project=project, parent_task_id=parent_task_id)
        return (TaskNode(root),)

    def requires_plan(self, task_type: str, estimated_steps: int = 1) -> bool:
        return estimated_steps > 1 or task_type in self.policy.require_plan_for

    def admit_child(self, parent_depth: int, current_children: int, total_tasks: int) -> None:
        if parent_depth >= self.policy.max_depth: raise RuntimeError("orchestration depth budget exceeded")
        if current_children >= self.policy.max_children: raise RuntimeError("child budget exceeded")
        if total_tasks >= self.policy.max_tasks: raise RuntimeError("task budget exceeded")
