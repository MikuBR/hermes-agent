"""Capability metadata consumed by the Safety Governor."""

from __future__ import annotations

from dataclasses import dataclass

from hermes_core.contracts import CapabilityRisk


@dataclass(frozen=True)
class CapabilityPolicy:
    """Static metadata; authorization remains a runtime decision."""

    name: str
    risk: CapabilityRisk = CapabilityRisk.MEDIUM
    reversible: bool = True
    external_side_effect: bool = False
    sensitive_data: bool = False
    cross_project: bool = False
    requires_explicit_approval: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("capability name cannot be empty")


DEFAULT_CAPABILITIES: dict[str, CapabilityPolicy] = {
    "filesystem.read": CapabilityPolicy(
        "filesystem.read", risk=CapabilityRisk.LOW, reversible=True
    ),
    "filesystem.write": CapabilityPolicy(
        "filesystem.write", risk=CapabilityRisk.MEDIUM, reversible=True
    ),
    "filesystem.delete": CapabilityPolicy(
        "filesystem.delete", risk=CapabilityRisk.HIGH, reversible=False
    ),
    "shell.execute": CapabilityPolicy(
        "shell.execute", risk=CapabilityRisk.HIGH, reversible=False, external_side_effect=True
    ),
    "system.config": CapabilityPolicy(
        "system.config", risk=CapabilityRisk.CRITICAL, reversible=True,
        requires_explicit_approval=True
    ),
}
