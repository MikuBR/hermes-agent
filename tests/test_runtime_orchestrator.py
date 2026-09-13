from dataclasses import replace

import pytest

from hermes_core.contracts import AgentTask
from hermes_core.orchestration import AgentOrchestrator, OrchestrationPolicy
from hermes_core.orchestration.graph import validate_dag


def test_orchestrator_enforces_admission_budgets():
    orchestrator = AgentOrchestrator(
        OrchestrationPolicy(max_depth=1, max_children=1, max_tasks=1)
    )
    with pytest.raises(RuntimeError, match="depth"):
        orchestrator.admit_child(1, 0, 0)
    with pytest.raises(RuntimeError, match="child"):
        orchestrator.admit_child(0, 1, 0)
    with pytest.raises(RuntimeError, match="task"):
        orchestrator.admit_child(0, 0, 1)


def test_requires_plan_is_deterministic():
    orchestrator = AgentOrchestrator()
    assert orchestrator.requires_plan("general") is False
    assert orchestrator.requires_plan("research") is True
    assert orchestrator.requires_plan("general", estimated_steps=2) is True


def test_requires_plan_rejects_invalid_step_estimate():
    with pytest.raises(ValueError, match="at least 1"):
        AgentOrchestrator().requires_plan("general", estimated_steps=0)


def test_plan_normalizes_and_preserves_project_and_budget():
    orchestrator = AgentOrchestrator()
    node = orchestrator.plan(
        "  do the thing  ",
        task_type="research",
        parent_task_id="parent",
        budget={"tokens": 100, "context_tokens": 200},
    )[0]
    assert node.task.objective == "do the thing"
    assert node.task.parent_task_id == "parent"
    assert node.task.budget == {"tokens": 100, "context_tokens": 200}


def test_graph_rejects_duplicate_self_and_unknown_dependencies():
    orchestrator = AgentOrchestrator()
    first = orchestrator.plan("first")[0]
    second = orchestrator.plan("second")[0]

    with pytest.raises(ValueError, match="duplicate"):
        validate_dag((first, replace(first, task=AgentTask(task_id=first.task.task_id))))
    with pytest.raises(ValueError, match="self-cycle"):
        validate_dag((replace(first, dependencies=(first.task.task_id,)),))
    with pytest.raises(ValueError, match="unknown dependency"):
        validate_dag((second, replace(first, dependencies=("missing",))))


def test_graph_returns_dependency_first_deterministic_order():
    orchestrator = AgentOrchestrator()
    root = orchestrator.plan("root")[0]
    child = orchestrator.plan("child")[0]
    grandchild = orchestrator.plan("grandchild")[0]
    child = replace(child, dependencies=(root.task.task_id,))
    grandchild = replace(grandchild, dependencies=(child.task.task_id,))

    ordered = validate_dag((grandchild, child, root))
    assert [node.task.objective for node in ordered] == ["root", "child", "grandchild"]


def test_graph_admission_enforces_aggregate_budgets():
    orchestrator = AgentOrchestrator(
        OrchestrationPolicy(max_tasks=2, max_tokens=100, max_context_tokens=200)
    )
    first = orchestrator.plan(
        "first", budget={"tokens": 40, "context_tokens": 100}
    )[0]
    second = orchestrator.plan(
        "second", budget={"tokens": 50, "context_tokens": 80}
    )[0]
    second = replace(second, dependencies=(first.task.task_id,))

    snapshot = orchestrator.admit_graph((second, first))
    assert snapshot.task_count == 2
    assert snapshot.depth == 1
    assert snapshot.estimated_tokens == 90
    assert snapshot.estimated_context_tokens == 180


def test_graph_admission_rejects_token_overrun():
    orchestrator = AgentOrchestrator(OrchestrationPolicy(max_tokens=10))
    node = orchestrator.plan("too much", budget={"tokens": 11})[0]
    with pytest.raises(RuntimeError, match="token"):
        orchestrator.admit_graph((node,))


def test_graph_admission_rejects_excessive_fanout():
    orchestrator = AgentOrchestrator(OrchestrationPolicy(max_children=1))
    root = orchestrator.plan("root")[0]
    left = replace(orchestrator.plan("left")[0], dependencies=(root.task.task_id,))
    right = replace(orchestrator.plan("right")[0], dependencies=(root.task.task_id,))
    with pytest.raises(RuntimeError, match="child"):
        orchestrator.admit_graph((root, left, right))
