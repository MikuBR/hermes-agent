"""Fork/upstream compatibility metadata and conservative migration planning."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class UpstreamState:
    remote: str='upstream'; version: str='unknown'; commit: str='unknown'; clean: bool=True
@dataclass(frozen=True)
class MigrationPlan:
    compatible: bool; conflicts: tuple[str,...]=(); actions: tuple[str,...]=()
class CompatibilityAnalyzer:
    def analyze(self, state:UpstreamState, *, changed_files=(), conflict_files=()):
        conflicts=tuple(conflict_files); compatible=not conflicts and state.clean
        actions=('review upstream diff','run compatibility suite','stage migration','require human approval before apply') if not compatible else ('run compatibility suite','stage migration')
        return MigrationPlan(compatible,conflicts,actions)
