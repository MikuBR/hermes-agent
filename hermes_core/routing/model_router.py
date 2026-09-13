"""Deterministic, provider-agnostic model selection policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from hermes_core.contracts import ModelRoute, ModelRouteRequest


@dataclass(frozen=True)
class ModelCandidate:
    provider: str
    model: str
    quality: float = 0.5
    speed: float = 0.5
    reliability: float = 0.5
    context_tokens: int = 0
    free: bool = False
    privacy: bool = False
    tools: frozenset[str] = frozenset()
    available: bool = True

    def __post_init__(self) -> None:
        for name in ("quality", "speed", "reliability"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.context_tokens < 0:
            raise ValueError("context_tokens cannot be negative")


class ModelRouter:
    """Scores candidates deterministically; adapters remain outside this class."""

    def route(self, request: ModelRouteRequest, candidates: Iterable[ModelCandidate]) -> ModelRoute:
        pool = []
        for candidate in candidates:
            if not candidate.available or candidate.provider in request.excluded_providers:
                continue
            if request.required_tools and not set(request.required_tools).issubset(candidate.tools):
                continue
            if request.context_tokens and candidate.context_tokens < request.context_tokens:
                continue
            if request.privacy_required and not candidate.privacy:
                continue
            pool.append((self._score(request, candidate), candidate))

        if not pool:
            raise LookupError("no model satisfies routing policy")

        preferred = {provider: index for index, provider in enumerate(request.preferred_providers)}
        pool.sort(
            key=lambda item: (
                -item[0][0],
                preferred.get(item[1].provider, len(preferred)),
                item[1].provider,
                item[1].model,
            )
        )
        score, best = pool[0]
        confidence = score[0]
        fallbacks = tuple(candidate.model for _, candidate in pool[1:4])
        return ModelRoute(
            best.provider,
            best.model,
            score=confidence,
            score_breakdown=score[1],
            fallback_models=fallbacks,
            confidence=confidence,
        )

    @staticmethod
    def _score(r: ModelRouteRequest, c: ModelCandidate) -> tuple[float, dict[str, float]]:
        weights = {
            "quality": 0.45,
            "reliability": 0.20,
            "speed": 0.10,
            "policy": 0.15,
            "privacy": 0.10,
        }
        if r.quality_target == "quality":
            weights["quality"] += 0.20
        elif r.quality_target == "speed":
            weights["speed"] += 0.20

        policy = 1.0
        if r.free_first and not c.free:
            policy = 0.0

        parts = {
            "quality": c.quality,
            "reliability": c.reliability,
            "speed": c.speed,
            "policy": policy,
            "privacy": 1.0 if c.privacy else 0.0,
        }
        total_weight = sum(weights.values())
        score = sum(parts[key] * weights[key] for key in weights) / total_weight
        return score, parts
