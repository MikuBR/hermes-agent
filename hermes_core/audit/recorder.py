"""Bounded, secret-minimizing audit recorder."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Any

_SECRET_KEYS=frozenset({'token','password','secret','api_key','authorization','cookie'})

def sanitize(metadata: Mapping[str, Any]) -> dict[str, str]:
    return {str(k): '[REDACTED]' if str(k).lower() in _SECRET_KEYS else str(v)[:1000] for k,v in metadata.items()}

@dataclass(frozen=True)
class AuditRecord:
    event_type: str
    actor_id: str
    timestamp: datetime
    request_id: str | None = None
    project_id: str | None = None
    summary: str = ''
    metadata: Mapping[str,str] = None

class AuditRecorder:
    def __init__(self, max_records: int = 1000): self._records=deque(maxlen=max_records)
    def record(self, event_type, actor_id, *, request_id=None, project_id=None, summary='', metadata=None):
        self._records.append(AuditRecord(event_type, actor_id, datetime.now(timezone.utc), request_id, project_id, summary[:1000], sanitize(metadata or {})))
    def snapshot(self): return tuple(self._records)
