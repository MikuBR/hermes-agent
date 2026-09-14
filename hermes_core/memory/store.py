"""Bounded, thread-safe fork-owned memory store."""

from __future__ import annotations

from collections import OrderedDict
import threading
from typing import Iterable, Optional, Tuple

from .models import LearningCandidate, MemoryRecord, MemoryScope


class MemoryStore:
    """In-memory control-plane store with explicit scope filtering.

    The store is intentionally bounded and process-local in Runtime 8. Persistence,
    encryption, external providers, and legacy MemoryProvider integration are adapter work.
    """

    def __init__(self, *, max_memories: int = 512, max_candidates: int = 256) -> None:
        if max_memories <= 0 or max_candidates <= 0:
            raise ValueError("store bounds must be positive")
        self._memories: OrderedDict[str, MemoryRecord] = OrderedDict()
        self._candidates: OrderedDict[str, LearningCandidate] = OrderedDict()
        self._max_memories = max_memories
        self._max_candidates = max_candidates
        self._lock = threading.RLock()

    def put_memory(self, record: MemoryRecord) -> None:
        with self._lock:
            self._memories.pop(record.memory_id, None)
            self._memories[record.memory_id] = record
            self._trim(self._memories, self._max_memories)

    def get_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        with self._lock:
            return self._memories.get(memory_id)

    def memories(self) -> Tuple[MemoryRecord, ...]:
        with self._lock:
            return tuple(self._memories.values())

    def recall(
        self,
        query: str,
        *,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[MemoryRecord, ...]:
        """Return only memories visible in the supplied scope, ranked deterministically."""
        if limit <= 0:
            return ()
        terms = {part for part in query.casefold().split() if part}
        with self._lock:
            visible = [
                record
                for record in self._memories.values()
                if _visible(record, user_id=user_id, project_id=project_id, session_id=session_id)
            ]
        def score(record: MemoryRecord) -> tuple[int, float, str]:
            haystack = f"{record.key} {record.content}".casefold()
            overlap = sum(1 for term in terms if term in haystack)
            return overlap, record.confidence, record.memory_id
        visible.sort(key=score, reverse=True)
        return tuple(record for record in visible if not terms or score(record)[0] > 0)[:limit]

    def put_candidate(self, candidate: LearningCandidate) -> None:
        with self._lock:
            self._candidates.pop(candidate.candidate_id, None)
            self._candidates[candidate.candidate_id] = candidate
            self._trim(self._candidates, self._max_candidates)

    def get_candidate(self, candidate_id: str) -> Optional[LearningCandidate]:
        with self._lock:
            return self._candidates.get(candidate_id)

    def candidates(self) -> Tuple[LearningCandidate, ...]:
        with self._lock:
            return tuple(self._candidates.values())

    @staticmethod
    def _trim(mapping: OrderedDict, limit: int) -> None:
        while len(mapping) > limit:
            mapping.popitem(last=False)


def _visible(
    record: MemoryRecord,
    *,
    user_id: Optional[str],
    project_id: Optional[str],
    session_id: Optional[str],
) -> bool:
    """Enforce isolation: narrower scopes never leak into sibling projects/sessions."""
    if record.scope is MemoryScope.GLOBAL:
        return True
    if record.scope is MemoryScope.USER:
        return bool(user_id and record.user_id == user_id)
    if record.scope is MemoryScope.PROJECT:
        return bool(project_id and record.project_id == project_id)
    if record.scope is MemoryScope.SESSION:
        return bool(session_id and record.session_id == session_id)
    return False
