"""First-class checkpoint and rollback contracts; adapters perform actual restoration."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Any
from uuid import uuid4

@dataclass(frozen=True)
class CheckpointSpec:
    checkpoint_id: str = field(default_factory=lambda:'cp_'+uuid4().hex)
    scope: str = 'workspace'
    target: str = ''
    created_at: datetime = field(default_factory=lambda:datetime.now(timezone.utc))
    parent_id: str|None = None
    metadata: dict[str,str] = field(default_factory=dict)

@dataclass(frozen=True)
class RollbackResult:
    checkpoint_id: str
    restored: bool
    verified: bool
    summary: str

class RollbackManager:
    def __init__(self, create: Callable[[CheckpointSpec],Any]|None=None, restore: Callable[[CheckpointSpec],bool]|None=None, verify: Callable[[CheckpointSpec],bool]|None=None):
        self.create=create; self.restore=restore; self.verify=verify
    def checkpoint(self, scope='workspace', target=''):
        spec=CheckpointSpec(scope=scope,target=target)
        if self.create: self.create(spec)
        return spec
    def rollback(self, spec: CheckpointSpec) -> RollbackResult:
        if self.restore is None: return RollbackResult(spec.checkpoint_id,False,False,'restore adapter not configured')
        restored=bool(self.restore(spec)); verified=bool(self.verify(spec)) if restored and self.verify else False
        return RollbackResult(spec.checkpoint_id,restored,verified,'rollback verified' if verified else ('rollback restored; verification unavailable/failed' if restored else 'rollback failed'))
