"""Memory/learning control plane with anti-trauma and cross-project safeguards."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Optional, Tuple

from .models import LearningCandidate, LearningDecision, MemoryOrigin, MemoryRecord, MemoryScope
from .store import MemoryStore


class MemoryLearningManager:
    """Explicit API for recall, session-end proposals, evidence and guarded promotion.

    Nothing here calls Hermes' existing memory tool/provider system. The manager is a
    dormant control plane intended for later guarded integration.
    """

    MIN_SUPPORT = 2
    MIN_CONFIDENCE = 0.80
    GENERALIZED_MIN_SUPPORT = 3
    GENERALIZED_MIN_CONFIDENCE = 0.90
    GENERALIZED_MIN_PROJECTS = 2

    def __init__(self, store: Optional[MemoryStore] = None) -> None:
        self.store = store or MemoryStore()

    def remember(
        self,
        *,
        key: str,
        content: str,
        scope: MemoryScope,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        origin: MemoryOrigin = MemoryOrigin.OBSERVATION,
        evidence: Iterable[str] = (),
        confidence: float = 0.0,
        metadata: Optional[dict[str, str]] = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            key=key,
            content=content,
            scope=scope,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            origin=origin,
            evidence=tuple(_bounded_strings(evidence, 32, 1024)),
            confidence=confidence,
            metadata=_bounded_metadata(metadata or {}),
        )
        self.store.put_memory(record)
        return record

    def recall(
        self,
        query: str,
        *,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[MemoryRecord, ...]:
        return self.store.recall(
            query,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            limit=limit,
        )

    def propose_from_session(
        self,
        *,
        key: str,
        content: str,
        session_id: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        evidence: Iterable[str] = (),
        confidence: float = 0.0,
        observed_project_ids: Iterable[str] = (),
    ) -> LearningCandidate:
        """Accept an externally-produced session-end candidate without promoting it."""
        candidate = LearningCandidate(
            key=key,
            content=content,
            source_scope=MemoryScope.SESSION,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            supporting_evidence=tuple(_bounded_strings(evidence, 32, 1024)),
            confidence=confidence,
            observed_project_ids=tuple(dict.fromkeys(p for p in observed_project_ids if p))[:16],
        )
        self.store.put_candidate(candidate)
        return candidate

    def support(self, candidate_id: str, *, evidence: str, confidence: Optional[float] = None,
                project_id: Optional[str] = None) -> LearningDecision:
        candidate = self.store.get_candidate(candidate_id)
        if candidate is None:
            return LearningDecision(False, "candidate not found", candidate_id)
        if not evidence.strip():
            return LearningDecision(False, "supporting evidence must not be empty", candidate_id)
        projects = list(candidate.observed_project_ids)
        if project_id:
            projects.append(project_id)
        updated = replace(
            candidate,
            supporting_evidence=tuple(_bounded_strings((*candidate.supporting_evidence, evidence), 32, 1024)),
            confidence=max(candidate.confidence, confidence) if confidence is not None else candidate.confidence,
            observed_project_ids=tuple(dict.fromkeys(projects))[:16],
        )
        self.store.put_candidate(updated)
        return LearningDecision(True, "support recorded", candidate_id)

    def contradict(self, candidate_id: str, *, evidence: str) -> LearningDecision:
        candidate = self.store.get_candidate(candidate_id)
        if candidate is None:
            return LearningDecision(False, "candidate not found", candidate_id)
        if not evidence.strip():
            return LearningDecision(False, "contradicting evidence must not be empty", candidate_id)
        updated = replace(
            candidate,
            contradicting_evidence=tuple(_bounded_strings((*candidate.contradicting_evidence, evidence), 32, 1024)),
        )
        self.store.put_candidate(updated)
        return LearningDecision(True, "contradiction recorded; promotion is now blocked", candidate_id)

    def promote(
        self,
        candidate_id: str,
        *,
        target_scope: MemoryScope,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        allow_generalization: bool = False,
    ) -> LearningDecision:
        """Promote only after evidence thresholds; refuse project contamination by default."""
        candidate = self.store.get_candidate(candidate_id)
        if candidate is None:
            return LearningDecision(False, "candidate not found", candidate_id)
        if candidate.contradicting_evidence:
            return LearningDecision(False, "contradicting evidence blocks promotion", candidate_id)
        if len(candidate.supporting_evidence) < self.MIN_SUPPORT:
            return LearningDecision(False, "insufficient supporting evidence", candidate_id)
        if candidate.confidence < self.MIN_CONFIDENCE:
            return LearningDecision(False, "confidence below promotion threshold", candidate_id)

        if target_scope in (MemoryScope.GLOBAL, MemoryScope.USER):
            if not allow_generalization:
                return LearningDecision(False, "generalization requires explicit authorization", candidate_id)
            if candidate.source_scope is MemoryScope.PROJECT:
                if len(set(candidate.observed_project_ids)) < self.GENERALIZED_MIN_PROJECTS:
                    return LearningDecision(False, "project learning needs evidence from at least two projects", candidate_id)
                if len(candidate.supporting_evidence) < self.GENERALIZED_MIN_SUPPORT:
                    return LearningDecision(False, "generalized learning needs stronger support", candidate_id)
                if candidate.confidence < self.GENERALIZED_MIN_CONFIDENCE:
                    return LearningDecision(False, "generalized learning needs higher confidence", candidate_id)

        if target_scope is MemoryScope.PROJECT and not project_id:
            return LearningDecision(False, "project promotion requires project_id", candidate_id)
        if target_scope is MemoryScope.USER and not user_id:
            return LearningDecision(False, "user promotion requires user_id", candidate_id)
        if target_scope is MemoryScope.SESSION and not session_id:
            return LearningDecision(False, "session promotion requires session_id", candidate_id)

        record = self.remember(
            key=candidate.key,
            content=candidate.content,
            scope=target_scope,
            user_id=user_id or candidate.user_id,
            project_id=project_id,
            session_id=session_id,
            origin=MemoryOrigin.LEARNED,
            evidence=candidate.supporting_evidence,
            confidence=candidate.confidence,
            metadata={"learning_candidate_id": candidate.candidate_id},
        )
        return LearningDecision(True, "candidate promoted", candidate_id, target_scope, record.memory_id)


def _bounded_strings(values: Iterable[str], limit: int, max_chars: int) -> list[str]:
    return [str(value)[:max_chars] for value in values if str(value).strip()][:limit]


def _bounded_metadata(values: dict[str, str], limit: int = 32, max_chars: int = 512) -> dict[str, str]:
    return {str(k)[:128]: str(v)[:max_chars] for k, v in list(values.items())[:limit]}
