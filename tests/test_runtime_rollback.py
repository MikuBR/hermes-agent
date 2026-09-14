import pytest

from hermes_core.rollback import CheckpointStore, RollbackManager


def test_checkpoint_is_created_without_mutating_target():
    seen = []
    manager = RollbackManager(create=lambda checkpoint: seen.append(checkpoint.target))
    checkpoint = manager.checkpoint("workspace", "/safe")
    assert checkpoint.target == "/safe"
    assert seen == ["/safe"]


def test_checkpoint_requires_scope_and_target():
    with pytest.raises(ValueError):
        RollbackManager().checkpoint("", "/safe")
    with pytest.raises(ValueError):
        RollbackManager().checkpoint("workspace", "")


def test_dry_run_does_not_call_restore():
    restored = []
    manager = RollbackManager(restore=lambda checkpoint: restored.append(checkpoint) or True)
    result = manager.rollback(manager.checkpoint(target="/safe"), dry_run=True)
    assert result.dry_run and not result.restored and restored == []


def test_rollback_requires_post_restore_verification():
    manager = RollbackManager(restore=lambda checkpoint: True, verify=lambda checkpoint: True)
    result = manager.rollback(manager.checkpoint(target="/safe"))
    assert result.restored and result.verified


def test_failed_verification_is_not_marked_complete():
    calls = []
    manager = RollbackManager(
        restore=lambda checkpoint: calls.append("restore") or True,
        verify=lambda checkpoint: False,
    )
    checkpoint = manager.checkpoint(target="/safe")
    result = manager.rollback(checkpoint)
    assert result.restored and not result.verified
    assert calls == ["restore"]


def test_rollback_is_idempotent_after_verified_success():
    calls = []
    manager = RollbackManager(
        restore=lambda checkpoint: calls.append("restore") or True,
        verify=lambda checkpoint: True,
    )
    checkpoint = manager.checkpoint(target="/safe")
    first = manager.rollback(checkpoint)
    second = manager.rollback(checkpoint)
    assert first.verified and second.idempotent
    assert calls == ["restore"]


def test_checkpoint_store_is_bounded_and_fingerprinted():
    store = CheckpointStore(max_records=2)
    first = store.put(RollbackManager().checkpoint(target="/one"))
    store.put(RollbackManager().checkpoint(target="/two"))
    third = store.put(RollbackManager().checkpoint(target="/three"))
    assert store.get(first.spec.checkpoint_id) is None
    assert store.get(third.spec.checkpoint_id).fingerprint == third.fingerprint
    assert len(store.all()) == 2
