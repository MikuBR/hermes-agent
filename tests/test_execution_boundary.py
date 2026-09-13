from datetime import datetime, timezone

import pytest

from hermes_core.context import ProjectContextResolver
from hermes_core.execution import ExecutionRequest, ExecutionResult
from hermes_core.execution.result import ExecutionResultStatus


def test_request_is_provider_neutral() -> None:
    project = ProjectContextResolver().resolve(git_root="/tmp/project")
    request = ExecutionRequest(
        capability="filesystem.read",
        actor_id="agent:test",
        project=project,
        arguments={"path": "README.md"},
    )
    assert request.capability == "filesystem.read"
    assert request.project.project_id == project.project_id
    assert request.created_at.tzinfo is not None


def test_request_rejects_naive_timestamp() -> None:
    project = ProjectContextResolver().resolve(git_root="/tmp/project")
    with pytest.raises(ValueError):
        ExecutionRequest(
            capability="filesystem.read",
            actor_id="agent:test",
            project=project,
            created_at=datetime.now(),
        )


def test_result_normalizes_failure_without_executor_details() -> None:
    result = ExecutionResult(
        request_id="req-1",
        status=ExecutionResultStatus.FAILED,
        summary="Operation failed",
        error="executor reported failure",
    )
    assert result.status is ExecutionResultStatus.FAILED
    assert result.request_id == "req-1"
