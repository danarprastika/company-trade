"""
G1.1 — Canonical ID Types

Typed identifier wrappers around UUIDv7 (time-ordered for database locality).
Each ID type is a distinct Python type to prevent accidental mixing.

Specification references:
- FINAL_SPECIFICATION/05_DATABASE_CANONICAL_MODEL.md (entity groups)
- FINAL_SPECIFICATION/02_RUNTIME_CONTRACTS.md (command_id, event_id, trace_id, etc.)
- docs/02_architecture/06_DATABASE_ARCHITECTURE.md (persistence strategy)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class EntityId(Generic[T]):
    """
    Base typed identifier. Wraps a UUIDv7 value.
    UUIDv7 is time-ordered, providing database locality for append-only event stores.
    """

    value: uuid.UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise TypeError(f"EntityId value must be uuid.UUID, got {type(self.value).__name__}")

    @classmethod
    def generate(cls) -> "EntityId[T]":
        """Generate a new time-ordered UUIDv7 identifier."""
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, s: str) -> "EntityId[T]":
        """Parse an identifier from its string representation."""
        return cls(uuid.UUID(s))

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value})"


# --- Typed ID variants ---
# Each is a distinct type to prevent mixing at the type-checker level.


class AgentId(EntityId["AgentId"]):
    """Identifier for a runtime AI employee."""


class OrderId(EntityId["OrderId"]):
    """Identifier for a broker-facing order."""


class StrategyId(EntityId["StrategyId"]):
    """Identifier for a trading strategy."""


class InstrumentId(EntityId["InstrumentId"]):
    """Identifier for a financial instrument."""


class AccountId(EntityId["AccountId"]):
    """Identifier for a trading account."""


class PortfolioId(EntityId["PortfolioId"]):
    """Identifier for a portfolio."""


class EnvironmentId(EntityId["EnvironmentId"]):
    """Identifier for a deployment environment."""


class DeploymentId(EntityId["DeploymentId"]):
    """Identifier for a deployment."""


class ExperimentId(EntityId["ExperimentId"]):
    """Identifier for a research experiment."""


class DatasetId(EntityId["DatasetId"]):
    """Identifier for a research dataset."""


class EventId(EntityId["EventId"]):
    """Identifier for a domain event."""


class CommandId(EntityId["CommandId"]):
    """Identifier for a command."""


class TraceId(EntityId["TraceId"]):
    """Identifier for request tracing across the system."""


class ApprovalId(EntityId["ApprovalId"]):
    """Identifier for a risk approval."""


class ChangeRequestId(EntityId["ChangeRequestId"]):
    """Identifier for an architecture change request."""


class MarketId(EntityId["MarketId"]):
    """Identifier for a market."""


class VenueId(EntityId["VenueId"]):
    """Identifier for a trading venue."""


class SignalId(EntityId["SignalId"]):
    """Identifier for a strategy signal."""


class IntentId(EntityId["IntentId"]):
    """Identifier for an order intent."""


class OMSInstructionId(EntityId["OMSInstructionId"]):
    """Identifier for an OMS execution instruction."""


class FillId(EntityId["FillId"]):
    """Identifier for an execution fill."""


class PositionId(EntityId["PositionId"]):
    """Identifier for a position."""


class ReconciliationRunId(EntityId["ReconciliationRunId"]):
    """Identifier for a reconciliation run."""


class ProviderId(EntityId["ProviderId"]):
    """Identifier for an external data/execution provider."""


class UserId(EntityId["UserId"]):
    """Identifier for a human user (owner/operator)."""


class TaskId(EntityId["TaskId"]):
    """Identifier for an AI agent task."""


class IncidentId(EntityId["IncidentId"]):
    """Identifier for a security or operational incident."""


class AlertId(EntityId["AlertId"]):
    """Identifier for a system alert."""


class KillSwitchId(EntityId["KillSwitchId"]):
    """Identifier for a kill switch."""


class ServiceHealthId(EntityId["ServiceHealthId"]):
    """Identifier for a service health record."""


class BackupRunId(EntityId["BackupRunId"]):
    """Identifier for a backup run."""


class RestoreDrillId(EntityId["RestoreDrillId"]):
    """Identifier for a restore drill."""


class DecisionLedgerEntryId(EntityId["DecisionLedgerEntryId"]):
    """Identifier for a decision ledger entry."""


class AgentMemoryId(EntityId["AgentMemoryId"]):
    """Identifier for agent memory."""


class AgentRoleId(EntityId["AgentRoleId"]):
    """Identifier for an agent role."""


class PermissionId(EntityId["PermissionId"]):
    """Identifier for a permission."""


class ToolId(EntityId["ToolId"]):
    """Identifier for an agent tool."""


class DataPointId(EntityId["DataPointId"]):
    """Identifier for a data point."""


class DataQualitySnapshotId(EntityId["DataQualitySnapshotId"]):
    """Identifier for a data quality snapshot."""


class NewsEventId(EntityId["NewsEventId"]):
    """Identifier for a news event."""


class EconomicEventId(EntityId["EconomicEventId"]):
    """Identifier for an economic calendar event."""


class CorporateActionId(EntityId["CorporateActionId"]):
    """Identifier for a corporate action."""


class MarketSessionId(EntityId["MarketSessionId"]):
    """Identifier for a market session."""


class InstrumentVersionId(EntityId["InstrumentVersionId"]):
    """Identifier for an instrument version."""


class StrategyVersionId(EntityId["StrategyVersionId"]):
    """Identifier for a strategy version."""


class DatasetVersionId(EntityId["DatasetVersionId"]):
    """Identifier for a dataset version."""


class EvidenceArtifactId(EntityId["EvidenceArtifactId"]):
    """Identifier for an evidence artifact."""


class PromotionCandidateId(EntityId["PromotionCandidateId"]):
    """Identifier for a promotion candidate."""


class ExposureSnapshotId(EntityId["ExposureSnapshotId"]):
    """Identifier for an exposure snapshot."""


class BalanceSnapshotId(EntityId["BalanceSnapshotId"]):
    """Identifier for a balance snapshot."""


class BacktestRunId(EntityId["BacktestRunId"]):
    """Identifier for a backtest run."""


class WalkForwardRunId(EntityId["WalkForwardRunId"]):
    """Identifier for a walk-forward run."""


class OOSRunId(EntityId["OOSRunId"]):
    """Identifier for an out-of-sample run."""


class StressRunId(EntityId["StressRunId"]):
    """Identifier for a stress test run."""


class ShadowRunId(EntityId["ShadowRunId"]):
    """Identifier for a shadow run."""


class FeatureSetId(EntityId["FeatureSetId"]):
    """Identifier for a feature set."""


class DataFeedId(EntityId["DataFeedId"]):
    """Identifier for a data feed."""


class ProviderCertificationId(EntityId["ProviderCertificationId"]):
    """Identifier for a provider certification."""


class MetricSnapshotId(EntityId["MetricSnapshotId"]):
    """Identifier for a metric snapshot."""


class AgentTaskId(EntityId["AgentTaskId"]):
    """Identifier for an agent task (alias for TaskId)."""


class OOSLockId(EntityId["OOSLockId"]):
    """Identifier for an OOS lock."""


class DatasetFrozenId(EntityId["DatasetFrozenId"]):
    """Identifier for a dataset frozen event."""


__all__ = [
    "EntityId",
    "AgentId",
    "OrderId",
    "StrategyId",
    "InstrumentId",
    "AccountId",
    "PortfolioId",
    "EnvironmentId",
    "DeploymentId",
    "ExperimentId",
    "DatasetId",
    "EventId",
    "CommandId",
    "TraceId",
    "ApprovalId",
    "ChangeRequestId",
    "MarketId",
    "VenueId",
    "SignalId",
    "IntentId",
    "OMSInstructionId",
    "FillId",
    "PositionId",
    "ReconciliationRunId",
    "ProviderId",
    "UserId",
    "TaskId",
    "IncidentId",
    "AlertId",
    "KillSwitchId",
    "ServiceHealthId",
    "BackupRunId",
    "RestoreDrillId",
    "DecisionLedgerEntryId",
    "AgentMemoryId",
    "AgentRoleId",
    "PermissionId",
    "ToolId",
    "DataPointId",
    "DataQualitySnapshotId",
    "NewsEventId",
    "EconomicEventId",
    "CorporateActionId",
    "MarketSessionId",
    "InstrumentVersionId",
    "StrategyVersionId",
    "DatasetVersionId",
    "EvidenceArtifactId",
    "PromotionCandidateId",
    "ExposureSnapshotId",
    "BalanceSnapshotId",
    "BacktestRunId",
    "WalkForwardRunId",
    "OOSRunId",
    "StressRunId",
    "ShadowRunId",
    "FeatureSetId",
    "DataFeedId",
    "ProviderCertificationId",
    "MetricSnapshotId",
    "AgentTaskId",
    "OOSLockId",
    "DatasetFrozenId",
]
