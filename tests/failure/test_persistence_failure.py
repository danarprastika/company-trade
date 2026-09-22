"""
G1 — Failure tests for Persistence Layer

Tests:
- Concurrency conflict handling
- Transaction rollback on failure
- Idempotency duplicate protection
- Migration failure rollback
- Unknown-critical failure semantics
"""

import pytest
from src.domain.events import EventEnvelope
from src.domain.correlation import TraceContext
from src.domain.ids import EnvironmentId
from src.domain.time import Instant
from src.domain.persistence import (
    InMemoryEventStore,
    InMemoryIdempotencyStore,
    InMemoryTransactionManager,
)
from src.domain.errors import PersistenceError
from src.domain.migration import (
    Migration,
    MigrationManager,
    InMemoryMigrationStore,
    InMemoryMigrationExecutor,
)


class TestEventStoreFailure:
    def _make_event(self, aggregate_id="order-1") -> EventEnvelope:
        return EventEnvelope.create(
            aggregate_type="Order",
            aggregate_id=aggregate_id,
            event_type="OrderSubmitted",
            schema_version="1.0.0",
            occurred_at=Instant.now(),
            producer="test",
            trace_context=TraceContext.new(),
            environment=EnvironmentId.generate(),
            payload={"order_id": aggregate_id},
            sequence=1,
        )

    def test_concurrent_append_conflict(self):
        """Concurrent appends with wrong expected_version should fail."""
        store = InMemoryEventStore()
        store.append([self._make_event()])

        # Simulate concurrent write with stale expected_version
        with pytest.raises(PersistenceError, match="Concurrency conflict"):
            store.append([self._make_event(sequence=2)], expected_version=0)

    def test_empty_append_is_noop(self):
        """Appending empty list should not change state."""
        store = InMemoryEventStore()
        store.append([])
        assert store.get_current_version("Order", "order-1") == 0

    def test_read_nonexistent_aggregate(self):
        """Reading events for nonexistent aggregate should return empty list."""
        store = InMemoryEventStore()
        events = store.read_events("Order", "nonexistent")
        assert events == []

    def test_read_all_events_empty(self):
        """read_all_events on empty store should return empty list."""
        store = InMemoryEventStore()
        events = store.read_all_events()
        assert events == []


class TestIdempotencyFailure:
    def test_duplicate_key_rejected(self):
        """Duplicate idempotency key should be rejected."""
        store = InMemoryIdempotencyStore()
        assert store.record_attempt("key-1", "order_submit") is True
        assert store.record_attempt("key-1", "order_submit") is False

    def test_result_not_found(self):
        """Getting result for unknown key should return None."""
        store = InMemoryIdempotencyStore()
        assert store.get_result("unknown") is None


class TestTransactionManagerFailure:
    def test_commit_unknown_transaction(self):
        """Committing unknown transaction should raise."""
        tm = InMemoryTransactionManager()
        ctx = tm.begin()
        tm.commit(ctx)
        with pytest.raises(PersistenceError):
            tm.commit(ctx)

    def test_rollback_unknown_transaction(self):
        """Rolling back unknown transaction should raise."""
        tm = InMemoryTransactionManager()
        ctx = tm.begin()
        tm.rollback(ctx)
        with pytest.raises(PersistenceError):
            tm.rollback(ctx)


class TestMigrationFailure:
    def test_migration_failure_rolls_back(self):
        """Migration failure should rollback and not record."""
        store = InMemoryMigrationStore()

        class FailingExecutor(InMemoryMigrationExecutor):
            def execute(self, sql: str) -> None:
                if "FAIL" in sql:
                    raise RuntimeError("Intentional failure")
                super().execute(sql)

        bad_migration = Migration(
            version="001",
            name="bad",
            description="Will fail",
            up_sql="FAIL",
            down_sql="DROP TABLE test;",
        )

        manager = MigrationManager([bad_migration], store, FailingExecutor())
        with pytest.raises(PersistenceError, match="failed"):
            manager.up()

        # Migration should not be recorded
        assert manager.get_current_version() is None
        assert len(store.get_applied_migrations()) == 0

    def test_rollback_failure_rolls_back(self):
        """Rollback failure should rollback the rollback transaction."""
        store = InMemoryMigrationStore()

        class FailingExecutor(InMemoryMigrationExecutor):
            def execute(self, sql: str) -> None:
                if "FAIL" in sql:
                    raise RuntimeError("Intentional failure")
                super().execute(sql)

        migration = Migration(
            version="001",
            name="test",
            description="Test",
            up_sql="CREATE TABLE test (id TEXT);",
            down_sql="FAIL",
        )

        manager = MigrationManager([migration], store, FailingExecutor())
        manager.up()

        with pytest.raises(PersistenceError, match="failed"):
            manager.down("000")

        # Migration should still be recorded (rollback failed)
        assert manager.get_current_version() == "001"

    def test_checksum_mismatch_detected(self):
        """Checksum mismatch should be detected during validation."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()

        migration = Migration(
            version="001",
            name="test",
            description="Test",
            up_sql="CREATE TABLE test (id TEXT);",
            down_sql="DROP TABLE test;",
        )

        manager = MigrationManager([migration], store, executor)
        manager.up()

        # Tamper with migration content
        tampered = Migration(
            version="001",
            name="test",
            description="Test",
            up_sql="CREATE TABLE different (id TEXT);",
            down_sql="DROP TABLE different;",
        )
        manager._migrations["001"] = tampered

        errors = manager.validate()
        assert any("Checksum mismatch" in e for e in errors)
