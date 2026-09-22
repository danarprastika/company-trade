"""
G1.11 — Unit tests for Persistence Layer

Tests:
- Event store append and read
- Optimistic concurrency control
- Idempotency store
- Transaction manager
- Append-only semantics
"""

import pytest
from src.domain.events import EventEnvelope
from src.domain.commands import CommandEnvelope
from src.domain.correlation import TraceContext
from src.domain.ids import EnvironmentId, EventId
from src.domain.time import Instant
from src.domain.persistence import (
    InMemoryEventStore,
    InMemoryIdempotencyStore,
    InMemoryTransactionManager,
    IdempotencyRecord,
)
from src.domain.errors import PersistenceError


class TestInMemoryEventStore:
    def _make_event(self, aggregate_type="Order", aggregate_id="order-1", sequence=1) -> EventEnvelope:
        return EventEnvelope.create(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type="OrderSubmitted",
            schema_version="1.0.0",
            occurred_at=Instant.now(),
            producer="test",
            trace_context=TraceContext.new(),
            environment=EnvironmentId.generate(),
            payload={"order_id": aggregate_id},
            sequence=sequence,
        )

    def test_append_and_read(self):
        """Events should be appendable and readable."""
        store = InMemoryEventStore()
        event = self._make_event()
        store.append([event])
        events = store.read_events("Order", "order-1")
        assert len(events) == 1
        assert events[0].event_type == "OrderSubmitted"

    def test_append_multiple_events(self):
        """Multiple events should be appendable in one call."""
        store = InMemoryEventStore()
        events = [self._make_event(sequence=i) for i in range(1, 4)]
        store.append(events)
        read_events = store.read_events("Order", "order-1")
        assert len(read_events) == 3

    def test_optimistic_concurrency_conflict(self):
        """Append with wrong expected_version should raise PersistenceError."""
        store = InMemoryEventStore()
        event = self._make_event()
        store.append([event])

        # Try to append with wrong expected version
        new_event = self._make_event(sequence=2)
        with pytest.raises(PersistenceError, match="Concurrency conflict"):
            store.append([new_event], expected_version=0)

    def test_optimistic_concurrency_success(self):
        """Append with correct expected_version should succeed."""
        store = InMemoryEventStore()
        event = self._make_event()
        store.append([event])

        new_event = self._make_event(sequence=2)
        store.append([new_event], expected_version=1)
        events = store.read_events("Order", "order-1")
        assert len(events) == 2

    def test_read_events_from_version(self):
        """read_events should support from_version offset."""
        store = InMemoryEventStore()
        events = [self._make_event(sequence=i) for i in range(1, 4)]
        store.append(events)
        read_events = store.read_events("Order", "order-1", from_version=1)
        assert len(read_events) == 2

    def test_get_current_version(self):
        """get_current_version should return event count."""
        store = InMemoryEventStore()
        assert store.get_current_version("Order", "order-1") == 0
        store.append([self._make_event()])
        assert store.get_current_version("Order", "order-1") == 1

    def test_read_all_events(self):
        """read_all_events should return all events globally."""
        store = InMemoryEventStore()
        store.append([self._make_event(aggregate_id="order-1")])
        store.append([self._make_event(aggregate_id="order-2")])
        all_events = store.read_all_events()
        assert len(all_events) == 2

    def test_append_empty_list(self):
        """Appending empty list should be a no-op."""
        store = InMemoryEventStore()
        store.append([])
        assert store.get_current_version("Order", "order-1") == 0

    def test_sequence_numbers_assigned(self):
        """Events should get global sequence numbers."""
        store = InMemoryEventStore()
        store.append([self._make_event()])
        store.append([self._make_event(sequence=2)])
        events = store.read_all_events()
        assert events[0].sequence == 1
        assert events[1].sequence == 2


class TestInMemoryIdempotencyStore:
    def test_record_attempt_new(self):
        """record_attempt should return True for new keys."""
        store = InMemoryIdempotencyStore()
        assert store.record_attempt("key-1", "order_submit") is True

    def test_record_attempt_duplicate(self):
        """record_attempt should return False for duplicate keys."""
        store = InMemoryIdempotencyStore()
        store.record_attempt("key-1", "order_submit")
        assert store.record_attempt("key-1", "order_submit") is False

    def test_record_result(self):
        """record_result should store the result."""
        store = InMemoryIdempotencyStore()
        store.record_attempt("key-1", "order_submit")
        store.record_result("key-1", "SUCCESS", {"order_id": "123"})
        record = store.get_result("key-1")
        assert record is not None
        assert record.result == "SUCCESS"
        assert record.result_data == {"order_id": "123"}

    def test_get_result_not_found(self):
        """get_result should return None for unknown keys."""
        store = InMemoryIdempotencyStore()
        assert store.get_result("unknown-key") is None


class TestInMemoryTransactionManager:
    def test_begin_creates_context(self):
        """begin should create a transaction context."""
        tm = InMemoryTransactionManager()
        ctx = tm.begin()
        assert ctx.transaction_id is not None
        assert ctx.started_at is not None

    def test_commit(self):
        """commit should complete the transaction."""
        tm = InMemoryTransactionManager()
        ctx = tm.begin()
        tm.commit(ctx)

    def test_rollback(self):
        """rollback should complete the transaction."""
        tm = InMemoryTransactionManager()
        ctx = tm.begin()
        tm.rollback(ctx)

    def test_commit_unknown_transaction(self):
        """commit should raise for unknown transaction."""
        tm = InMemoryTransactionManager()
        ctx = tm.begin()
        tm.commit(ctx)
        with pytest.raises(PersistenceError):
            tm.commit(ctx)

    def test_add_operation(self):
        """TransactionContext should track operations."""
        tm = InMemoryTransactionManager()
        ctx = tm.begin()
        ctx.add_operation({"type": "write", "data": "test"})
        assert len(ctx.operations) == 1
