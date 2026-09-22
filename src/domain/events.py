"""
G1.7 — Event Envelope

Immutable event envelope with all required fields for the event-driven core.

Specification references:
- FINAL_SPECIFICATION/02_RUNTIME_CONTRACTS.md:
  "Every event carries: event_id, aggregate_type, aggregate_id, event_type, schema_version, occurred_at_utc, recorded_at_utc, producer, correlation_id, causation_id, environment, payload_hash and sequence."
- FINAL_SPECIFICATION/01_ARCHITECTURE_DECISIONS.md AD-003:
  "Domain state changes are represented by immutable events; commands request changes and events record accepted changes."
- FINAL_SPECIFICATION/04_EVENT_CATALOG.md:
  "All events are versioned and immutable. Consumers must tolerate unknown future event fields."
- docs/02_architecture/03_EVENT_ARCHITECTURE.md:
  Envelope: event_id, event_type, schema_version, occurred_at, produced_at, source, correlation_id, causation_id, aggregate_id, payload_hash.
  Rule: "Events are immutable facts. Commands request actions; events report facts."
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .correlation import TraceContext
from .ids import EnvironmentId, EventId
from .time import Instant


@dataclass(frozen=True)
class EventEnvelope:
    """
    Immutable event envelope.
    Per RUNTIME_CONTRACTS.md: "Every event carries: event_id, aggregate_type, aggregate_id, event_type, schema_version, occurred_at_utc, recorded_at_utc, producer, correlation_id, causation_id, environment, payload_hash and sequence."
    Per AD-003: "Domain state changes are represented by immutable events."
    """

    event_id: EventId
    aggregate_type: str
    aggregate_id: str
    event_type: str
    schema_version: str
    occurred_at_utc: Instant
    recorded_at_utc: Instant
    producer: str
    correlation_id: str
    causation_id: Optional[str]
    environment: EnvironmentId
    payload_hash: str
    sequence: int
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validate required fields
        if not self.aggregate_type:
            raise ValueError("aggregate_type is required")
        if not self.aggregate_id:
            raise ValueError("aggregate_id is required")
        if not self.event_type:
            raise ValueError("event_type is required")
        if not self.schema_version:
            raise ValueError("schema_version is required")
        if not self.producer:
            raise ValueError("producer is required")
        if not self.correlation_id:
            raise ValueError("correlation_id is required")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")

        # Validate timestamp ordering
        if self.recorded_at_utc < self.occurred_at_utc:
            raise ValueError("recorded_at_utc must be >= occurred_at_utc")

        # Validate payload hash matches payload
        computed_hash = self._compute_payload_hash(self.payload)
        if computed_hash != self.payload_hash:
            raise ValueError("payload_hash does not match payload content")

    @staticmethod
    def _compute_payload_hash(payload: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of the payload."""
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    @classmethod
    def create(
        cls,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        schema_version: str,
        occurred_at: Instant,
        producer: str,
        trace_context: TraceContext,
        environment: EnvironmentId,
        payload: Dict[str, Any],
        sequence: int = 0,
    ) -> "EventEnvelope":
        """
        Create a new event envelope with computed payload hash.
        """
        recorded_at = Instant.now()
        payload_hash = cls._compute_payload_hash(payload)

        return cls(
            event_id=EventId.generate(),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            schema_version=schema_version,
            occurred_at_utc=occurred_at,
            recorded_at_utc=recorded_at,
            producer=producer,
            correlation_id=str(trace_context.trace_id),
            causation_id=str(trace_context.causation_id) if trace_context.causation_id else None,
            environment=environment,
            payload_hash=payload_hash,
            sequence=sequence,
            payload=payload,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event envelope to dictionary."""
        return {
            "event_id": str(self.event_id),
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "event_type": self.event_type,
            "schema_version": self.schema_version,
            "occurred_at_utc": self.occurred_at_utc.to_iso8601(),
            "recorded_at_utc": self.recorded_at_utc.to_iso8601(),
            "producer": self.producer,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "environment": str(self.environment),
            "payload_hash": self.payload_hash,
            "sequence": self.sequence,
            "payload": self.payload,
        }

    def verify_integrity(self) -> bool:
        """
        Verify that the payload hash matches the payload content.
        Per AD-007: "Decision/audit ledger is append-only with hash chaining and periodic signed checkpoints."
        """
        computed_hash = self._compute_payload_hash(self.payload)
        return computed_hash == self.payload_hash


__all__ = [
    "EventEnvelope",
]
