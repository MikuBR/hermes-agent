import pytest
from hermes_core.self_improvement import Improvement, SelfImprovement, Stage

def test_pipeline_advances_with_evidence():
    x=SelfImprovement().advance(Improvement('i'),evidence=('observation',)); assert x.stage is Stage.DIAGNOSE and x.evidence==('observation',)

def test_deploy_transition_requires_approval():
    s=SelfImprovement(); x=Improvement('i',Stage.COMPARE)
    with pytest.raises(PermissionError): s.advance(x)
    assert s.advance(x,approve=True).approved
