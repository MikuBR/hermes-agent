"""Small DAG validator used by the orchestrator."""
from __future__ import annotations

def validate_dag(nodes) -> None:
    ids = {n.task.task_id for n in nodes}
    deps = {n.task.task_id: set(n.dependencies) for n in nodes}
    if any(d not in ids for ds in deps.values() for d in ds): raise ValueError("unknown dependency")
    visiting, done = set(), set()
    def visit(node):
        if node in visiting: raise ValueError("task graph contains a cycle")
        if node in done: return
        visiting.add(node)
        for dep in deps[node]: visit(dep)
        visiting.remove(node); done.add(node)
    for node in ids: visit(node)
