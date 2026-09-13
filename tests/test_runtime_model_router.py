from hermes_core.contracts import ModelRouteRequest
from hermes_core.routing import ModelCandidate, ModelRouter

def test_router_is_deterministic_and_skips_unavailable():
    r = ModelRouter().route(ModelRouteRequest(task_type="coding", quality_target="quality"), [
        ModelCandidate("a", "slow", quality=.9, reliability=.9, speed=.2, free=True),
        ModelCandidate("b", "fast", quality=.8, reliability=.9, speed=.9, free=True),
        ModelCandidate("c", "down", available=False),
    ])
    assert r.provider == "b"
    assert "down" not in r.fallback_models

def test_router_enforces_privacy_and_tools():
    r = ModelRouter().route(ModelRouteRequest(task_type="research", privacy_required=True, required_tools=("web",)), [
        ModelCandidate("public", "x", privacy=False, tools=frozenset({"web"})),
        ModelCandidate("private", "y", privacy=True, tools=frozenset({"web"})),
    ])
    assert r.model == "y"
