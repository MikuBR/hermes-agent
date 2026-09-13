from hermes_core.governance import CapabilityRegistry, AgentLineage

def test_registry_is_deterministic():
    r=CapabilityRegistry(); assert r.names()==tuple(sorted(r.names()))
def test_lineage_is_explicit():
    x=AgentLineage('child','parent','root','project',1); assert x.parent_id=='parent' and x.depth==1
