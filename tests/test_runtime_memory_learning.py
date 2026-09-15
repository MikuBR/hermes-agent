from hermes_core.memory import (
    LearningDecision,
    MemoryLearningManager,
    MemoryScope,
    MemoryStore,
)


def test_scope_isolation_never_leaks_project_memory() -> None:
    manager = MemoryLearningManager(MemoryStore())
    manager.remember(
        key="style",
        content="Project A uses tabs.",
        scope=MemoryScope.PROJECT,
        project_id="A",
        confidence=0.9,
    )
    manager.remember(
        key="style",
        content="User prefers concise output.",
        scope=MemoryScope.USER,
        user_id="u1",
        confidence=0.9,
    )

    visible_a = manager.recall("style", user_id="u1", project_id="A")
    visible_b = manager.recall("style", user_id="u1", project_id="B")

    assert {record.content for record in visible_a} == {
        "Project A uses tabs.",
        "User prefers concise output.",
    }
    assert {record.content for record in visible_b} == {"User prefers concise output."}


def test_session_candidate_requires_evidence_before_promotion() -> None:
    manager = MemoryLearningManager(MemoryStore())
    candidate = manager.propose_from_session(
        key="format",
        content="Use markdown headings.",
        session_id="s1",
        user_id="u1",
        evidence=("one observation",),
        confidence=0.9,
    )

    denied = manager.promote(candidate.candidate_id, target_scope=MemoryScope.USER, user_id="u1")

    assert denied == LearningDecision(False, "generalization requires explicit authorization", candidate.candidate_id)

    manager.support(candidate.candidate_id, evidence="second observation", confidence=0.9)
    manager.support(candidate.candidate_id, evidence="third observation", confidence=0.9)
    approved = manager.promote(
        candidate.candidate_id,
        target_scope=MemoryScope.USER,
        user_id="u1",
        allow_generalization=True,
    )

    assert approved.accepted is True
    assert approved.memory_id


def test_contradiction_blocks_learning() -> None:
    manager = MemoryLearningManager(MemoryStore())
    candidate = manager.propose_from_session(
        key="preference",
        content="Use dark mode.",
        session_id="s1",
        user_id="u1",
        evidence=("asked twice", "confirmed once"),
        confidence=0.95,
    )
    manager.contradict(candidate.candidate_id, evidence="user explicitly requested light mode")
    decision = manager.promote(
        candidate.candidate_id,
        target_scope=MemoryScope.USER,
        user_id="u1",
        allow_generalization=True,
    )

    assert decision.accepted is False
    assert decision.reason == "contradicting evidence blocks promotion"


def test_project_to_global_generalization_needs_two_projects_and_stronger_evidence() -> None:
    manager = MemoryLearningManager(MemoryStore())
    candidate = manager.propose_from_session(
        key="rule",
        content="Run formatter before commit.",
        session_id="s1",
        project_id="A",
        evidence=("A observation", "A confirmation", "A repeated confirmation"),
        confidence=0.95,
        observed_project_ids=("A",),
    )
    denied = manager.promote(
        candidate.candidate_id,
        target_scope=MemoryScope.GLOBAL,
        allow_generalization=True,
    )
    assert denied.accepted is False
    assert denied.reason == "generalization requires explicit authorization"

    manager.support(candidate.candidate_id, evidence="B observation", confidence=0.95, project_id="B")
    approved = manager.promote(
        candidate.candidate_id,
        target_scope=MemoryScope.GLOBAL,
        allow_generalization=True,
    )
    assert approved.accepted is True


def test_store_is_bounded() -> None:
    store = MemoryStore(max_memories=2, max_candidates=2)
    manager = MemoryLearningManager(store)
    for index in range(3):
        manager.remember(
            key=f"k{index}",
            content=f"v{index}",
            scope=MemoryScope.GLOBAL,
            confidence=0.5,
        )

    assert len(store.memories()) == 2
    assert {item.key for item in store.memories()} == {"k1", "k2"}
