"""Deterministic, dependency-safe task graph primitives."""

from __future__ import annotations

from collections.abc import Iterable

from .orchestrator import TaskNode


def validate_dag(nodes: Iterable[TaskNode]) -> tuple[TaskNode, ...]:
    """Validate task IDs/dependencies and return nodes in deterministic order.

    The function is pure: it never mutates tasks or executes them.
    """
    materialized = tuple(nodes)
    if not materialized:
        return ()

    by_id: dict[str, TaskNode] = {}
    for node in materialized:
        task_id = node.task.task_id
        if not task_id:
            raise ValueError("task ID cannot be empty")
        if task_id in by_id:
            raise ValueError(f"duplicate task ID: {task_id}")
        by_id[task_id] = node

    for node in materialized:
        for dependency in node.dependencies:
            if dependency == node.task.task_id:
                raise ValueError("task graph contains a self-cycle")
            if dependency not in by_id:
                raise ValueError(f"unknown dependency: {dependency}")

    visiting: set[str] = set()
    visited: set[str] = set()
    ordered: list[TaskNode] = []

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise ValueError("task graph contains a cycle")
        if task_id in visited:
            return
        visiting.add(task_id)
        node = by_id[task_id]
        for dependency in sorted(node.dependencies):
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)
        ordered.append(node)

    for task_id in sorted(by_id):
        visit(task_id)
    return tuple(ordered)
