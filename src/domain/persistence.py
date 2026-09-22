"""
G1.11 — Persistence Layer

Transactional event store with append-only semantics.
Trading/accounting mutations use transactional boundaries.
Analytical workloads must not corrupt operational state.

Specification references:
- docs/02_architecture/06_DATABASE_ARCHITECTURE.md:
  "Data classes: Operational state, immutable evidence, analytical datasets, event history, audit ledger and caches."
  "Trading/accounting mutations use transactional boundaries. Analytical workloads must not corrupt operational state."
  "Schema changes are versioned, tested and recoverable."
- docs/02_architecture/07_CACHING_AND_IDEMPOTENCY.md:
  "Order submission, command execution, event handling, reconciliation and financial mutations require explicit idempotency strategy."
  "Caches are never authoritative for risk, balances, positions or broker state."
- FINAL_SPECIFICATION/01_ARCHITECTURE_DECISIONS.md AD-007:
  "Decision/audit ledger is append-only with hash chaining and periodic signed checkpoints."
- FINAL_SPECIFICATION/02_RUNTIME_CONTRACTS.md:
  Event envelope with sequence, payload_hash, correlation_id, causation_id.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from .commands import CommandEnvelope
from .enums import ErrorClass
from .errors import PersistenceError
from .events import EventEnvelope
from .ids import EntityId


@dataclass(frozen=True)
class EventRecord:
    """
    A stored event record with metadata.
    """

    envelope: EventEnvelope
    stored_at: str  # ISO timestamp
    storage_version: int = 1


@dataclass(frozen=True)
class IdempotencyRecord:
    """
    Record of an idempotent operation to prevent duplicates.
    Per CACHING_AND_IDEMPOTENCY.md: "Order submission, command execution, event handling, reconciliation and financial mutations require explicit idempotency strategy."
    """

    idempotency_key: str
    operation_type: str
    result: str  # SUCCESS, FAILURE, PENDING
    created_at: str
    result_data: Optional[Dict[str, Any]] = None


class EventStore(ABC):
    """
    Abstract event store interface.
    Per DATABASE_ARCHITECTURE.md: "Event history" data class.
    Per AD-007: "Decision/audit ledger is append-only with hash chaining."
    """

    @abstractmethod
    def append(
        self,
        events: List[EventEnvelope],
        expected_version: Optional[int] = None,
    ) -> None:
        """
        Append events to the store for an aggregate.
        Uses optimistic concurrency control via expected_version.
        Raises PersistenceError on conflict or failure.
        """
        pass

    @abstractmethod
    def read_events(
        self,
        aggregate_type: str,
        aggregate_id: str,
        from_version: int = 0,
    ) -> List[EventEnvelope]:
        """
        Read events for an aggregate, optionally from a specific version.
        """
        pass

    @abstractmethod
    def read_all_events(
        self,
        from_sequence: int = 0,
        limit: int = 1000,
    ) -> List[EventEnvelope]:
        """
        Read all events globally, for projection or replay.
        """
        pass

    @abstractmethod
    def get_current_version(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> int:
        """
        Get the current version (event count) for an aggregate.
        """
        pass


class IdempotencyStore(ABC):
    """
    Abstract idempotency store interface.
    Per CACHING_AND_IDEMPOTENCY.md: "Order submission, command execution, event handling, reconciliation and financial mutations require explicit idempotency strategy."
    """

    @abstractmethod
    def record_attempt(self, idempotency_key: str, operation_type: str) -> bool:
        """
        Record an idempotency attempt. Returns True if this is a new attempt,
        False if the key already exists (duplicate).
        """
        pass

    @abstractmethod
    def record_result(
        self,
        idempotency_key: str,
        result: str,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record the result of an idempotent operation."""
        pass

    @abstractmethod
    def get_result(self, idempotency_key: str) -> Optional[IdempotencyRecord]:
        """Get the result of a previously completed idempotent operation."""
        pass


class ReadModel(ABC):
    """
    Abstract read model interface.
    Per DATABASE_ARCHITECTURE.md: "Analytical workloads must not corrupt operational state."
    Read models are projections from the event store, never directly mutated.
    """

    @abstractmethod
    def project(self, event: EventEnvelope) -> None:
        """Apply an event to update the read model."""
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the read model."""
        pass


class TransactionManager(ABC):
    """
    Abstract transaction manager for trading/accounting mutations.
    Per DATABASE_ARCHITECTURE.md: "Trading/accounting mutations use transactional boundaries."
    """

    @abstractmethod
    def begin(self) -> "TransactionContext":
        """Begin a new transaction."""
        pass

    @abstractmethod
    def commit(self, ctx: "TransactionContext") -> None:
        """Commit a transaction."""
        pass

    @abstractmethod
    def rollback(self, ctx: "TransactionContext") -> None:
        """Rollback a transaction."""
        pass


@dataclass
class TransactionContext:
    """
    Transaction context for trading/accounting mutations.
    """

    transaction_id: str
    started_at: str
    operations: List[Dict[str, Any]] = field(default_factory=list)

    def add_operation(self, operation: Dict[str, Any]) -> None:
        """Record an operation within this transaction."""
        self.operations.append(operation)


class InMemoryEventStore(EventStore):
    """
    In-memory event store implementation for G1 foundation.
    Append-only with sequence numbers and optimistic concurrency control.
    """

    def __init__(self) -> None:
        self._events: Dict[str, List[EventEnvelope]] = {}  # aggregate_key -> events
        self._global_sequence: int = 0
        self._versions: Dict[str, int] = {}  # aggregate_key -> version

    def _aggregate_key(self, aggregate_type: str, aggregate_id: str) -> str:
        return f"{aggregate_type}:{aggregate_id}"

    def append(
        self,
        events: List[EventEnvelope],
        expected_version: Optional[int] = None,
    ) -> None:
        if not events:
            return

        aggregate_key = self._aggregate_key(
            events[0].aggregate_type, events[0].aggregate_id
        )

        # Optimistic concurrency check
        current_version = self._versions.get(aggregate_key, 0)
        if expected_version is not None and current_version != expected_version:
            raise PersistenceError(
                message=f"Concurrency conflict: expected version {expected_version}, got {current_version}",
                correlation_id=events[0].correlation_id,
            )

        # Append events with sequence numbers
        for event in events:
            self._global_sequence += 1
            # Create a new event with the global sequence
            updated_event = EventEnvelope(
                event_id=event.event_id,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                schema_version=event.schema_version,
                occurred_at_utc=event.occurred_at_utc,
                recorded_at_utc=event.recorded_at_utc,
                producer=event.producer,
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
                environment=event.environment,
                payload_hash=event.payload_hash,
                sequence=self._global_sequence,
                payload=event.payload,
            )
            if aggregate_key not in self._events:
                self._events[aggregate_key] = []
            self._events[aggregate_key].append(updated_event)

        self._versions[aggregate_key] = current_version + len(events)

    def read_events(
        self,
        aggregate_type: str,
        aggregate_id: str,
        from_version: int = 0,
    ) -> List[EventEnvelope]:
        aggregate_key = self._aggregate_key(aggregate_type, aggregate_id)
        events = self._events.get(aggregate_key, [])
        return events[from_version:]

    def read_all_events(
        self,
        from_sequence: int = 0,
        limit: int = 1000,
    ) -> List[EventEnvelope]:
        all_events: List[EventEnvelope] = []
        for events in self._events.values():
            all_events.extend(events)
        all_events.sort(key=lambda e: e.sequence)
        return [e for e in all_events if e.sequence >= from_sequence][:limit]

    def get_current_version(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> int:
        aggregate_key = self._aggregate_key(aggregate_type, aggregate_id)
        return self._versions.get(aggregate_key, 0)


class InMemoryIdempotencyStore(IdempotencyStore):
    """
    In-memory idempotency store implementation for G1 foundation.
    """

    def __init__(self) -> None:
        self._records: Dict[str, IdempotencyRecord] = {}

    def record_attempt(self, idempotency_key: str, operation_type: str) -> bool:
        if idempotency_key in self._records:
            return False
        # Record as pending
        from .time import Instant
        self._records[idempotency_key] = IdempotencyRecord(
            idempotency_key=idempotency_key,
            operation_type=operation_type,
            result="PENDING",
            created_at=Instant.now().to_iso8601(),
        )
        return True

    def record_result(
        self,
        idempotency_key: str,
        result: str,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        from .time import Instant
        if idempotency_key not in self._records:
            self._records[idempotency_key] = IdempotencyRecord(
                idempotency_key=idempotency_key,
                operation_type="",
                result=result,
                created_at=Instant.now().to_iso8601(),
                result_data=result_data,
            )
        else:
            existing = self._records[idempotency_key]
            self._records[idempotency_key] = IdempotencyRecord(
                idempotency_key=idempotency_key,
                operation_type=existing.operation_type,
                result=result,
                created_at=existing.created_at,
                result_data=result_data,
            )

    def get_result(self, idempotency_key: str) -> Optional[IdempotencyRecord]:
        return self._records.get(idempotency_key)


class InMemoryTransactionManager(TransactionManager):
    """
    In-memory transaction manager for G1 foundation.
    """

    def __init__(self) -> None:
        self._active_transactions: Dict[str, TransactionContext] = {}

    def begin(self) -> TransactionContext:
        from .ids import CommandId
        from .time import Instant
        ctx = TransactionContext(
            transaction_id=str(CommandId.generate()),
            started_at=Instant.now().to_iso8601(),
        )
        self._active_transactions[ctx.transaction_id] = ctx
        return ctx

    def commit(self, ctx: TransactionContext) -> None:
        if ctx.transaction_id not in self._active_transactions:
            raise PersistenceError(
                message=f"Transaction {ctx.transaction_id} not found or already completed",
            )
        del self._active_transactions[ctx.transaction_id]

    def rollback(self, ctx: TransactionContext) -> None:
        if ctx.transaction_id not in self._active_transactions:
            raise PersistenceError(
                message=f"Transaction {ctx.transaction_id} not found or already completed",
            )
        del self._active_transactions[ctx.transaction_id]


__all__ = [
    "EventStore",
    "IdempotencyStore",
    "ReadModel",
    "TransactionManager",
    "TransactionContext",
    "EventRecord",
    "IdempotencyRecord",
    "InMemoryEventStore",
    "InMemoryIdempotencyStore",
    "InMemoryTransactionManager",
]
