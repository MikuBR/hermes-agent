from hermes_core.context import ProjectContext, ProjectContextSource
from hermes_core.execution.gateway import ExecutionGateway
from hermes_core.execution import ExecutionRequest
from hermes_core.governance import SafetyGovernor, CapabilityPolicy, CapabilityRisk
from hermes_core.governance.governor import GovernorContext, GovernanceDecision

def ctx(): return ProjectContext('p', None, 1.0, ProjectContextSource.EXPLICIT)
def test_denied_never_executes():
    called=[]
    g=ExecutionGateway(SafetyGovernor(), lambda r: called.append(r))
    req=ExecutionRequest('system.config','user',ctx())
    out=g.execute(req, GovernorContext(10))
    assert out.status.value == 'blocked' and not called

def test_allowed_reaches_executor():
    called=[]
    g=ExecutionGateway(SafetyGovernor(), lambda r: called.append(r.capability))
    req=ExecutionRequest('filesystem.read','user',ctx())
    out=g.execute(req, GovernorContext(10))
    assert called == ['filesystem.read'] and out.status.value == 'succeeded'
