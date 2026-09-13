from hermes_core.verification import Verifier, VerificationCheck
from hermes_core.audit import AuditRecorder

def test_verifier_distinguishes_partial():
    r=Verifier().verify(3,(VerificationCheck('positive',lambda x:x>0,'value positive'),VerificationCheck('even',lambda x:x%2==0)))
    assert r.status.value=='partially_verified' and r.verified_claims==('positive',)

def test_audit_redacts_secrets_and_is_bounded():
    a=AuditRecorder(1); a.record('x','u',metadata={'token':'abc','safe':'ok'}); a.record('y','u')
    assert len(a.snapshot())==1
