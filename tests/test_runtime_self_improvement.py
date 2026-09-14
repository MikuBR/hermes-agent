from hermes_core.improvement import ExperimentResult, ImprovementManager, ImprovementStatus


def test_improvement_needs_evidence_before_isolation() -> None:
    manager = ImprovementManager()
    proposal = manager.propose(objective="reduce flaky CI", hypothesis="standard runners remove starvation", risk="medium")

    decision = manager.isolate(proposal.proposal_id)

    assert decision.allowed is False
    assert decision.reason == "isolation requires evidence-backed proposal"


def test_full_lifecycle_keeps_deploy_behind_verification_and_approval() -> None:
    manager = ImprovementManager()
    proposal = manager.propose(
        objective="reduce flaky CI",
        hypothesis="remove scarce hosted runners",
        risk="low",
        evidence=("three queued runs",),
        expected_outcomes=("jobs start",),
    )

    assert manager.isolate(proposal.proposal_id).allowed is True
    assert manager.deploy(proposal.proposal_id).allowed is False

    experiment = ExperimentResult(
        proposal_id=proposal.proposal_id,
        passed=True,
        evidence=("run-74", "run-75"),
        verification_id="ver-1",
        adversarial_checks_passed=True,
        regression_checks_passed=True,
        comparison_summary="new path is schedulable and no slower beyond budget",
    )
    assert manager.record_experiment(experiment).allowed is True
    assert manager.get(proposal.proposal_id).status is ImprovementStatus.VERIFIED

    assert manager.approve(proposal.proposal_id, approved=True, reason="Reviewed and accepted").allowed is True
    assert manager.deploy(proposal.proposal_id).allowed is True
    assert manager.get(proposal.proposal_id).status is ImprovementStatus.DEPLOYED

    assert manager.monitor(proposal.proposal_id, healthy=True, evidence=("health=ok",)).allowed is True
    assert manager.learn(proposal.proposal_id, evidence=("stable-after-deploy",)).allowed is True
    assert manager.get(proposal.proposal_id).status is ImprovementStatus.LEARNED


def test_failed_adversarial_check_blocks_promotion() -> None:
    manager = ImprovementManager()
    proposal = manager.propose(
        objective="change router",
        hypothesis="prefer free model",
        risk="high",
        evidence=("cost regression",),
    )
    assert manager.isolate(proposal.proposal_id).allowed is True
    decision = manager.record_experiment(
        ExperimentResult(
            proposal_id=proposal.proposal_id,
            passed=True,
            regression_checks_passed=True,
            adversarial_checks_passed=False,
        )
    )
    assert decision.allowed is False
    assert manager.get(proposal.proposal_id).status is ImprovementStatus.FAILED


def test_rejection_is_terminal_until_a_new_proposal_is_created() -> None:
    manager = ImprovementManager()
    proposal = manager.propose(
        objective="small refactor",
        hypothesis="same behavior",
        risk="low",
        evidence=("existing regression",),
    )
    assert manager.isolate(proposal.proposal_id).allowed is True
    manager.record_experiment(
        ExperimentResult(
            proposal_id=proposal.proposal_id,
            passed=True,
            regression_checks_passed=True,
            adversarial_checks_passed=True,
        )
    )
    rejected = manager.approve(proposal.proposal_id, approved=False, reason="Not worth the risk")
    assert rejected.allowed is False
    assert manager.get(proposal.proposal_id).status is ImprovementStatus.REJECTED
    assert manager.deploy(proposal.proposal_id).allowed is False
