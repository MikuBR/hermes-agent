from hermes_core.rollback import RollbackManager

def test_checkpoint_is_created_without_mutating_target():
    seen=[]; m=RollbackManager(create=lambda c:seen.append(c.target))
    c=m.checkpoint('workspace','/safe')
    assert c.target=='/safe' and seen==['/safe']

def test_rollback_requires_verification():
    m=RollbackManager(restore=lambda c:True,verify=lambda c:True)
    assert m.rollback(m.checkpoint()).verified
