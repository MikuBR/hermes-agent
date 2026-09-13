"""Bounded task planning and admission; execution stays behind existing APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from hermes_core.contracts import AgentTask, ProjectContext


@dataclass(frozen=True)
class OrchestrationPolicy:
    """Hard limits applied before a graph is admitted for execution."""

    max_depth: int = 3
    max_children: int = 10
    max_tasks: int = 50
    max_tokens: int = 100_000
    max_context_tokens: int = 200_000
    require_plan_for: frozenset[str] = frozenset(
        {"system.change", "multi_step", "research"}
    )

    def __post_init__(self) -> None:
        for field_name in (
            "max_depth",
            "max_children",
            "max_tasks",
            "max_tokens",
            "max_context_tokens",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} cannot be negative")


@dataclass(frozen=True)
class TaskNode:
    """Immutable planned task plus IDs of tasks that must precede it."""

    task: AgentTask
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdmissionSnapshot:
    """Bounded resource estimate for a graph; no execution is performed."""

    task_count: int
    depth: int
    estimated_tokens: int
    estimated_context_tokens: int


class AgentOrchestrator:
    """Own planning/admission while leaving execution to existing primitives."""

    def __init__(self, policy: Optional[OrchestrationPolicy] = None) -> None:
        self.policy = policy or OrchestrationPolicy()

    def plan(
        self,
        objective: str,
        task_type: str = "general",
        project: Optional[ProjectContext] = None,
        parent_task_id: Optional[str] = None,
        budget: Optional[dict[str, int]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> tuple[TaskNode, ...]:
        if not objective.strip():
            raise ValueError("objective cannot be empty")
        root = AgentTask(
            task_type=task_type,
            objective=objective.strip(),
            project=project,
            parent_task_id=parent_task_id,
            budget=dict(budget or {}),
            metadata=dict(metadata or {}),
        )
        self._validate_task_budget(root)
        return (TaskNode(root),)

    def requires_plan(self, task_type: str, estimated_steps: int = 1) -> bool:
        if estimated_steps < 1:
            raise ValueError("estimated_steps must be at least 1")
        return estimated_steps > 1 or task_type in self.policy.require_plan_for

    def admit_child(self, parent_depth: int, current_children: int, total_tasks: int) -> None:
        if parent_depth < 0 or current_children < 0 or total_tasks < 0:
            raise ValueError("budget counters cannot be negative")
        if parent_depth >= self.policy.max_depth:
            raise RuntimeError("orchestration depth budget exceeded")
        if current_children >= self.policy.max_children:
            raise RuntimeError("child budget exceeded")
        if total_tasks >= self.policy.max_tasks:
            raise RuntimeError("task budget exceeded")

    def admit_graph(self, nodes: tuple[TaskNode, ...]) -> AdmissionSnapshot:
        """Validate a planned graph and enforce aggregate resource budgets."""
        from .graph import validate_dag

        ordered = validate_dag(nodes)
        if len(ordered) > self.policy.max_tasks:
            raise RuntimeError("task budget exceeded")

        children: dict[str, int] = {node.task.task_id: 0 for node in ordered}
        for node in ordered:
            for dependency in node.dependencies:
                children[dependency] += 1
                if children[dependency] > self.policy.max_children:
                    raise RuntimeError("child budget exceeded")

        depths: dict[str, int] = {}
        estimated_tokens = 0
        estimated_context = 0
        for node in ordered:
            dependency_depth = max((depths[d] for d in node.dependencies), default=-1)
            depth = dependency_depth + 1
            if depth > self.policy.max_depth:
                raise RuntimeError("orchestration depth budget exceeded")
            depths[node.task.task_id] = depth
            estimated_tokens += self._budget_value(node.task, "tokens")
            estimated_context += self._budget_value(node.task, "context_tokens")

        if estimated_tokens > self.policy.max_tokens:
            raise RuntimeError("token budget exceeded")
        if estimated_context > self.policy.max_context_tokens:
            raise RuntimeError("context token budget exceeded")

        return AdmissionSnapshot(
            task_count=len(ordered),
            depth=max(depths.values(), default=0),
            estimated_tokens=estimated_tokens,
            estimated_context_tokens=estimated_context,
        )

    @staticmethod
    def _budget_value(task: AgentTask, key: str) -> int:
        value = int(task.budget.get(key, 0))
        if value < 0:
            raise ValueError(f"task budget '{key}' cannot be negative")
        return value

    def _validate_task_budget(self, task: AgentTask) -> None:
        self._budget_value(task, "tokens")
        self._budget_value(task, "context_tokens")
