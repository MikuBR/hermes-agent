"""Dormant composition root for the fork-owned control plane."""
from __future__ import annotations
from dataclasses import dataclass
from .cognition import CognitiveRouter
from .orchestration import AgentOrchestrator
from .routing import ModelRouter
from .governance import SafetyGovernor
from .execution.gateway import ExecutionGateway

@dataclass
class HermesRuntime:
    """Composes policy components without taking over legacy Hermes by default."""
    cognitive: CognitiveRouter
    orchestrator: AgentOrchestrator
    model_router: ModelRouter
    governor: SafetyGovernor
    gateway: ExecutionGateway
    enabled: bool = False

    @classmethod
    def dormant(cls):
        governor=SafetyGovernor()
        return cls(CognitiveRouter(),AgentOrchestrator(),ModelRouter(),governor,ExecutionGateway(governor),False)
