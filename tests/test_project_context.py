from pathlib import Path

import pytest

from hermes_core.context import ProjectContextResolver, ProjectContextSource


@pytest.fixture
def resolver() -> ProjectContextResolver:
    return ProjectContextResolver()


def test_explicit_identity_wins(resolver: ProjectContextResolver) -> None:
    result = resolver.resolve(
        cwd="/tmp/other",
        git_root="/tmp/repo",
        explicit_project_id="project:explicit",
    )
    assert result.project_id == "project:explicit"
    assert result.source is ProjectContextSource.EXPLICIT
    assert result.confidence == 1.0


def test_git_identity_is_stable(resolver: ProjectContextResolver) -> None:
    first = resolver.resolve(git_root="/tmp/repo")
    second = resolver.resolve(git_root=Path("/tmp/repo"))
    assert first.project_id == second.project_id
    assert first.source is ProjectContextSource.GIT
    assert first.boundary == Path("/tmp/repo").resolve()


def test_different_repositories_are_isolated(resolver: ProjectContextResolver) -> None:
    first = resolver.resolve(git_root="/tmp/repo-a")
    second = resolver.resolve(git_root="/tmp/repo-b")
    assert first.project_id != second.project_id


def test_advisory_signal_cannot_override_git(resolver: ProjectContextResolver) -> None:
    result = resolver.resolve(
        git_root="/tmp/repo",
        advisory_project_id="project:untrusted",
    )
    assert result.source is ProjectContextSource.GIT
    assert result.project_id != "project:untrusted"


def test_conflicting_authoritative_signals_are_explicit(resolver: ProjectContextResolver) -> None:
    result = resolver.resolve(
        explicit_project_id="project:a",
        session_project_id="project:b",
    )
    assert result.ambiguous is True
    assert result.confidence == 0.0


def test_relative_paths_are_normalized(resolver: ProjectContextResolver) -> None:
    result = resolver.resolve(git_root="./repo")
    assert result.workspace_root is not None
    assert result.workspace_root.is_absolute()


def test_unknown_context_is_explicit(resolver: ProjectContextResolver) -> None:
    result = resolver.resolve()
    assert result.project_id == "unknown"
    assert result.source is ProjectContextSource.UNKNOWN
    assert result.confidence == 0.0
