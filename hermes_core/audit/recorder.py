"""Bounded, secret-minimizing audit recording for runtime decisions."""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Mapping

from hermes_core.contracts import AuditEvent, ExecutionStatus

_SECRET_KEY_PARTS = ("token", "password", "secret", "api_key", "apikey", "authorization", "cookie")
_MAX_TEXT = 1000


def _is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in _SECRET_KEY_PARTS)


def _safe_value(value: Any, *, depth: int = 0) -> str:
    if depth > 2:
        return "[TRUNCATED]"
    if isinstance(value, Mapping):
        pairs = []
        for key, item in list(value.items())[:32]:
            key_text = str(key)
            rendered = "[REDACTED]" if _is_secret_key(key_text) else _safe_value(item, depth=depth + 1)
            pairs.append(f"{key_text}={rendered}")
        return "{" + ", ".join(pairs) + "}"
    if isinstance(value, (list, tuple, set, frozenset)):
        return "[" + ", ".join(_safe_value(item, depth=depth + 1) for item in list(value)[:32]) + "]"
    return str(value)[:_MAX_TEXT]


def sanitize_metadata(metadata: Mapping[str, Any] | None) -> dict[str, str]:
    """Remove secret-looking fields and bound every serialized value."""
    if not metadata:
        return {}
    return {
        str(key): "[REDACTED]" if _is_secret_key(str(key)) else _safe_value(value)
        for key, value in list(metadata.items())[:64]
    }


class AuditRecorder:
    """Thread-safe in-memory audit recorder with a hard record bound."""

    def __init__(self, max_records: int = 1000) -> None:
        if max_records < 1:
            raise ValueError("max_records must be >= 1")
        self._records: deque[AuditEvent] = deque(maxlen=max_records)
        self._lock = Lock()

    def record(
        self,
        event_type: str,
        actor_id: str,
        *,
        request_id: str | None = None,
        project_id: str | None = None,
        status: ExecutionStatus | None = None,
        summary: str = "",
        metadata: Mapping[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            actor_id=actor_id,
            timestamp=(timestamp or datetime.now(timezone.utc)),
            request_id=request_id,
            project_id=project_id,
            status=status,
            summary=str(summary)[:_MAX_TEXT],
            metadata=sanitize_metadata(metadata),
        )
        with self._lock:
            self._records.append(event)
        return event

    def snapshot(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return tuple(self._records)

    def latest(self) -> AuditEvent | None:
        with self._lock:
            return self._records[-1] if self._records else None
