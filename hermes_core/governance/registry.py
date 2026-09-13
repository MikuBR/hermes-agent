"""Canonical capability registry and lineage metadata."""
from __future__ import annotations
from dataclasses import dataclass
from .capabilities import CapabilityPolicy, DEFAULT_CAPABILITIES
@dataclass(frozen=True)
class AgentLineage:
    agent_id:str; parent_id:str|None=None; root_id:str|None=None; project_id:str|None=None; depth:int=0
class CapabilityRegistry:
    def __init__(self, policies=None): self._policies=dict(policies or DEFAULT_CAPABILITIES)
    def get(self,name): return self._policies.get(name)
    def names(self): return tuple(sorted(self._policies))
