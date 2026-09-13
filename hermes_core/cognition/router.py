"""Cognitive routing: direct answer versus bounded specialist planning."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
class Mode(str,Enum): DIRECT='direct'; PLAN='plan'; RESEARCH='research'; MULTI_AGENT='multi_agent'; APPROVAL='approval'
@dataclass(frozen=True)
class CognitiveDecision:
    mode:Mode; reasons:tuple[str,...]; confidence:float
class CognitiveRouter:
    def decide(self, objective:str, *, task_type='general', explicit_approval=False, steps=1, uncertainty=False, needs_external_research=False)->CognitiveDecision:
        if not objective.strip(): raise ValueError('objective cannot be empty')
        if task_type in {'system.change','destructive'} and not explicit_approval: return CognitiveDecision(Mode.APPROVAL,('high-impact task requires approval',),1.0)
        if needs_external_research: return CognitiveDecision(Mode.RESEARCH,('external evidence required',),.9)
        if uncertainty or steps>3: return CognitiveDecision(Mode.MULTI_AGENT,('uncertainty or decomposition complexity',),.8)
        if steps>1 or task_type in {'coding','multi_step'}: return CognitiveDecision(Mode.PLAN,('multi-step objective',),.85)
        return CognitiveDecision(Mode.DIRECT,('bounded single-step objective',),.9)
