"""Self-improvement lifecycle. Production deployment is approval-gated by construction."""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
class Stage(IntEnum): OBSERVE=0; DIAGNOSE=1; RESEARCH=2; PROPOSE=3; ISOLATE=4; IMPLEMENT=5; TEST=6; ADVERSARIAL_QA=7; COMPARE=8; APPROVAL=9; DEPLOY=10; MONITOR=11; LEARN=12
@dataclass(frozen=True)
class Improvement:
    improvement_id:str; stage:Stage=Stage.OBSERVE; evidence:tuple[str,...]=(); approved:bool=False
class SelfImprovement:
    def advance(self, item:Improvement, *, evidence=(), approve=False)->Improvement:
        if item.stage is Stage.DEPLOY and not item.approved and not approve: raise PermissionError('deployment requires explicit approval')
        next_stage=Stage(min(int(item.stage)+1,int(Stage.LEARN)))
        if next_stage is Stage.DEPLOY and not (approve or item.approved): raise PermissionError('deployment requires explicit approval')
        return Improvement(item.improvement_id,next_stage,item.evidence+tuple(evidence),item.approved or approve)
