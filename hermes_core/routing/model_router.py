"""Deterministic, provider-agnostic model selection policy."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from hermes_core.contracts import ModelRoute, ModelRouteRequest

@dataclass(frozen=True)
class ModelCandidate:
    provider: str
    model: str
    quality: float = .5
    speed: float = .5
    reliability: float = .5
    context_tokens: int = 0
    free: bool = False
    privacy: bool = False
    tools: frozenset[str] = frozenset()
    available: bool = True

class ModelRouter:
    """Scores candidates deterministically; adapters remain outside this class."""
    def route(self, request: ModelRouteRequest, candidates: Iterable[ModelCandidate]) -> ModelRoute:
        pool = []
        for c in candidates:
            if not c.available or c.provider in request.excluded_providers:
                continue
            if request.required_tools and not set(request.required_tools).issubset(c.tools):
                continue
            if request.context_tokens and c.context_tokens < request.context_tokens:
                continue
            if request.privacy_required and not c.privacy:
                continue
            pool.append((self._score(request, c), c))
        if not pool:
            raise LookupError("no model satisfies routing policy")
        pool.sort(key=lambda x: (-x[0][0], x[0][1].provider, x[0][1].model))
        score, best = pool[0]
        preferred = request.preferred_providers
        confidence = max(0.0, min(1.0, score[0]))
        fallbacks = tuple(c.model for _, c in pool[1:4])
        return ModelRoute(best.provider, best.model, score=confidence,
                          score_breakdown=score[1], fallback_models=fallbacks,
                          confidence=confidence)

    @staticmethod
    def _score(r: ModelRouteRequest, c: ModelCandidate) -> tuple[float, dict[str,float]]:
        w = {"quality": .45, "reliability": .2, "speed": .1, "policy": .15, "privacy": .1}
        if r.quality_target == "quality": w["quality"] += .2
        elif r.quality_target == "speed": w["speed"] += .2
        policy = 1.0 if (c.free if r.free_first else True) else 0.0
        if c.provider in r.preferred_providers: policy = min(1.0, policy + .25)
        privacy = 1.0 if c.privacy else 0.0
        parts = {"quality":c.quality,"reliability":c.reliability,"speed":c.speed,"policy":policy,"privacy":privacy}
        return (sum(parts[k]*w[k] for k in w), parts)
