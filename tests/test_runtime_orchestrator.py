import pytest
from hermes_core.orchestration import AgentOrchestrator, OrchestrationPolicy
from hermes_core.orchestration.graph import validate_dag

def test_orchestrator_enforces_budgets():
    o=AgentOrchestrator(OrchestrationPolicy(max_depth=1,max_children=1,max_tasks=1))
    with pytest.raises(RuntimeError): o.admit_child(1,0,0)
    with pytest.raises(RuntimeError): o.admit_child(0,1,0)

def test_graph_rejects_cycles():
    a=o=AgentOrchestrator().plan("x")[0]
    from dataclasses import replace
    n=replace(a, dependencies=(a.task.task_id,))
    with pytest.raises(ValueError): validate_dag((n,))
