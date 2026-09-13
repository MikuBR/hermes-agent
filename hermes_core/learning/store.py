"""Scoped learning store with anti-trauma generalization rules."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone

class Scope(str,Enum): SESSION='session'; PROJECT='project'; GLOBAL='global'; STRATEGY='strategy'; ENVIRONMENT='environment'
@dataclass(frozen=True)
class Learning:
    key:str; observation:str; scope:Scope; confidence:float=.5; environment:str|None=None; validated:bool=False; created_at:datetime=datetime.now(timezone.utc)

class LearningStore:
    def __init__(self): self._items={}
    def observe(self,key,observation,scope=Scope.SESSION,environment=None):
        item=Learning(key,observation,scope,.5,environment,False)
        self._items[(scope,key,environment)]=item; return item
    def validate(self,key,scope,environment=None,confidence=.8):
        k=(scope,key,environment); old=self._items.get(k)
        if not old: raise KeyError(key)
        item=Learning(old.key,old.observation,old.scope,max(0,min(1,confidence)),old.environment,True,old.created_at)
        self._items[k]=item; return item
    def get(self,key,scope,environment=None): return self._items.get((scope,key,environment))
