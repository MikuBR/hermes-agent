"""Deterministic project-context resolution.

This module is intentionally pure and filesystem-light. Integration with the
Hermes lifecycle belongs to a later runtime stage.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

from .models import ContextEvidence, ProjectContext, ProjectContextSource


class ProjectContextResolver:
    """Resolve a project from authoritative signals before advisory ones."""

    def resolve(
        self,
        *,
        cwd: str | Path | None = None,
        explicit_project_id: str | None = None,
        session_project_id: str | None = None,
        git_root: str | Path | None = None,
        worktree_root: str | Path | None = None,
        profile_project_id: str | None = None,
        lineage_project_id: str | None = None,
        advisory_project_id: str | None = None,
        session_id: str | None = None,
        lineage_id: str | None = None,
        parent_project_id: str | None = None,
    ) -> ProjectContext:
        """Resolve identity using explicit/session/Git evidence first.

        Advisory signals never override authoritative signals. Explicit project
        identity is the strongest semantic override; a conflicting persisted
        session identity remains ambiguous because it may represent a different
        project. Git/worktree paths provide workspace-boundary evidence and do
        not invalidate an explicit project selection.
        """
        normalized_cwd = self._normalize_path(cwd)
        normalized_git = self._normalize_path(git_root)
        normalized_worktree = self._normalize_path(worktree_root)

        signals = [
            (ProjectContextSource.EXPLICIT, explicit_project_id, 1.0, True),
            (ProjectContextSource.SESSION, session_project_id, 0.95, True),
            (ProjectContextSource.GIT, self._identity_from_path(normalized_git), 0.9, True),
            (ProjectContextSource.WORKTREE, self._identity_from_path(normalized_worktree), 0.85, True),
            (ProjectContextSource.PROFILE, profile_project_id, 0.7, False),
            (ProjectContextSource.LINEAGE, lineage_project_id, 0.65, False),
            (ProjectContextSource.ADVISORY, advisory_project_id, 0.2, False),
        ]

        evidence = tuple(
            ContextEvidence(source=s, value=v, weight=w, authoritative=a)
            for s, v, w, a in signals
            if v and v.strip()
        )

        explicit = explicit_project_id.strip() if explicit_project_id else None
        session = session_project_id.strip() if session_project_id else None

        # An explicit user/project selection outranks workspace inference. A
        # session mismatch is still unsafe because it represents persisted
        # semantic state, so surface ambiguity rather than silently mixing it.
        ambiguous = bool(explicit and session and explicit != session)
        if explicit is None:
            subordinate_authoritative = {
                value
                for value in (
                    session,
                    self._identity_from_path(normalized_git),
                    self._identity_from_path(normalized_worktree),
                )
                if value
            }
            ambiguous = len(subordinate_authoritative) > 1

        if explicit_project_id:
            project_id = explicit_project_id.strip()
            source = ProjectContextSource.EXPLICIT
        elif session_project_id:
            project_id = session_project_id.strip()
            source = ProjectContextSource.SESSION
        elif normalized_git:
            project_id = self._identity_from_path(normalized_git)
            source = ProjectContextSource.GIT
        elif normalized_worktree:
            project_id = self._identity_from_path(normalized_worktree)
            source = ProjectContextSource.WORKTREE
        elif profile_project_id:
            project_id = profile_project_id.strip()
            source = ProjectContextSource.PROFILE
        elif lineage_project_id:
            project_id = lineage_project_id.strip()
            source = ProjectContextSource.LINEAGE
        elif advisory_project_id:
            project_id = advisory_project_id.strip()
            source = ProjectContextSource.ADVISORY
        elif normalized_cwd:
            project_id = self._identity_from_path(normalized_cwd)
            source = ProjectContextSource.CWD
        else:
            project_id = "unknown"
            source = ProjectContextSource.UNKNOWN

        confidence = self._confidence(evidence, source, ambiguous)
        workspace_root = normalized_git or normalized_worktree or normalized_cwd
        boundary = normalized_git or normalized_worktree or normalized_cwd

        return ProjectContext(
            project_id=project_id,
            workspace_root=workspace_root,
            boundary=boundary,
            confidence=confidence,
            source=source,
            evidence=evidence,
            session_id=session_id,
            lineage_id=lineage_id,
            parent_project_id=parent_project_id,
            ambiguous=ambiguous,
        )

    @staticmethod
    def _normalize_path(value: str | Path | None) -> Path | None:
        if value is None:
            return None
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve(strict=False)

    @staticmethod
    def _identity_from_path(path: Path | None) -> str | None:
        if path is None:
            return None
        # Stable local identity; no path is exposed as the project identifier.
        digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:20]
        return f"project:{digest}"

    @staticmethod
    def _confidence(
        evidence: Iterable[ContextEvidence],
        source: ProjectContextSource,
        ambiguous: bool,
    ) -> float:
        if ambiguous:
            return 0.0
        source_weights = {e.source: e.weight for e in evidence}
        return min(1.0, source_weights.get(source, 0.0))
