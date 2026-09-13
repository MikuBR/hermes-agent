from hermes_core.cognition import CognitiveRouter, Mode

def test_complexity_routes_to_multi_agent(): assert CognitiveRouter().decide('x',steps=4).mode is Mode.MULTI_AGENT
def test_system_change_requires_approval(): assert CognitiveRouter().decide('x',task_type='system.change').mode is Mode.APPROVAL
def test_research_is_explicit(): assert CognitiveRouter().decide('x',needs_external_research=True).mode is Mode.RESEARCH
