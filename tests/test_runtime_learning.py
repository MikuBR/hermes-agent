from hermes_core.learning import LearningStore, Scope

def test_learning_is_scope_isolated():
    s=LearningStore(); s.observe('x','bad','project', '/a'); s.observe('x','good','project','/b')
    assert s.get('x',Scope.PROJECT,'/a').observation=='bad'
    assert s.get('x',Scope.PROJECT,'/b').observation=='good'

def test_unvalidated_learning_does_not_become_global_rule():
    s=LearningStore(); s.observe('x','failure',Scope.ENVIRONMENT,'env-a')
    assert s.get('x',Scope.GLOBAL) is None
