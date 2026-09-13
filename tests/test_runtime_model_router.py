import pytest

from hermes_core.contracts import ModelRouteRequest
from hermes_core.routing import ModelCandidate, ModelRouter


def test_router_is_deterministic_and_skips_unavailable():
    result = ModelRouter().route(
        ModelRouteRequest(task_type="coding", quality_target="quality"),
        [
            ModelCandidate("a", "slow", quality=0.9, reliability=0.9, speed=0.2, free=True),
            ModelCandidate("b", "fast", quality=0.8, reliability=0.9, speed=0.9, free=True),
            ModelCandidate("c", "down", available=False),
        ],
    )
    assert result.provider == "b"
    assert "down" not in result.fallback_models
    assert 0.0 <= result.score <= 1.0
    assert result.confidence == result.score


def test_router_enforces_privacy_and_tools():
    result = ModelRouter().route(
        ModelRouteRequest(
            task_type="research", privacy_required=True, required_tools=("web",)
        ),
        [
            ModelCandidate("public", "x", privacy=False, tools=frozenset({"web"})),
            ModelCandidate("private", "y", privacy=True, tools=frozenset({"web"})),
        ],
    )
    assert result.model == "y"


def test_free_first_prefers_free_candidate_when_quality_is_close():
    result = ModelRouter().route(
        ModelRouteRequest(task_type="general", free_first=True),
        [
            ModelCandidate("paid", "premium", quality=0.95, reliability=0.95, free=False),
            ModelCandidate("free", "community", quality=0.90, reliability=0.90, free=True),
        ],
    )
    assert result.provider == "free"


def test_preferred_provider_breaks_a_close_tie():
    result = ModelRouter().route(
        ModelRouteRequest(
            task_type="general",
            free_first=False,
            preferred_providers=("preferred",),
        ),
        [
            ModelCandidate("other", "a", quality=0.8, reliability=0.8),
            ModelCandidate("preferred", "b", quality=0.8, reliability=0.8),
        ],
    )
    assert result.provider == "preferred"


def test_candidate_metrics_must_be_normalized():
    with pytest.raises(ValueError):
        ModelCandidate("bad", "model", quality=1.1)
