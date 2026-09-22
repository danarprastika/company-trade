"""
G1.7 — Unit tests for Event Envelope

Tests:
- Event envelope creation with all required fields
- Payload hash verification
- Timestamp ordering validation
- Immutability
- Serialization
"""

import pytest
from src.domain.events import EventEnvelope
from src.domain.correlation import TraceContext
from src.domain.ids import EnvironmentId, EventId
from src.domain.time import Instant


class TestEventEnvelope:
    def _make_trace_context(self) -> TraceContext:
        return TraceContext.new()

    def _make_envelope(self, **kwargs) -> EventEnvelope:
        """Helper to create a valid event envelope."""
        defaults = dict(
            aggregate_type="Order",
            aggregate_id="order-123",
            event_type="OrderSubmitted",
            schema_version="1.0.0",
            occurred_at=Instant.now(),
            producer="risk-engine",
            trace_context=self._make_trace_context(),
            environment=EnvironmentId.generate(),
            payload={"order_id": "order-123", "side": "BUY"},
            sequence=1,
        )
        defaults.update(kwargs)
        return EventEnvelope.create(**defaults)

    def test_create_with_all_fields(self):
        """EventEnvelope.create should set all required fields."""
        envelope = self._make_envelope()
        assert envelope.event_id is not None
        assert envelope.aggregate_type == "Order"
        assert envelope.aggregate_id == "order-123"
        assert envelope.event_type == "OrderSubmitted"
        assert envelope.schema_version == "1.0.0"
        assert envelope.producer == "risk-engine"
        assert envelope.correlation_id is not None
        assert envelope.environment is not None
        assert envelope.payload_hash is not None
        assert envelope.sequence == 1

    def test_payload_hash_computed(self):
        """Payload hash should be computed from payload content."""
        envelope = self._make_envelope(payload={"key": "value"})
        assert envelope.payload_hash is not None
        assert len(envelope.payload_hash) == 64  # SHA-256 hex

    def test_payload_hash_verification(self):
        """verify_integrity should return True for valid hash."""
        envelope = self._make_envelope()
        assert envelope.verify_integrity() is True

    def test_payload_hash_mismatch_detected(self):
        """verify_integrity should return False for tampered payload."""
        envelope = self._make_envelope()
        # Tamper with payload by bypassing frozen dataclass restriction
        object.__setattr__(envelope, "payload", {"tampered": True})
        assert envelope.verify_integrity() is False

    def test_recorded_at_must_be_after_occurred_at(self):
        """recorded_at_utc must be >= occurred_at_utc."""
        occurred = Instant.now()
        # Create a recorded_at that is before occurred_at
        from src.domain.time import Instant as InstantClass
        recorded = Instant.from_unix_seconds(occurred.unix_seconds - 10.0)
        with pytest.raises(ValueError, match="recorded_at_utc must be >= occurred_at_utc"):
            EventEnvelope(
                event_id=EventId.generate(),
                aggregate_type="Order",
                aggregate_id="order-123",
                event_type="OrderSubmitted",
                schema_version="1.0.0",
                occurred_at_utc=occurred,
                recorded_at_utc=recorded,
                producer="test",
                correlation_id="trace-123",
                causation_id=None,
                environment=EnvironmentId.generate(),
                payload_hash="abc123",
                sequence=1,
                payload={},
            )

    def test_required_fields_validation(self):
        """Missing required fields should raise ValueError."""
        with pytest.raises(ValueError, match="aggregate_type is required"):
            EventEnvelope(
                event_id=EventId.generate(),
                aggregate_type="",
                aggregate_id="order-123",
                event_type="OrderSubmitted",
                schema_version="1.0.0",
                occurred_at_utc=Instant.now(),
                recorded_at_utc=Instant.now(),
                producer="test",
                correlation_id="trace-123",
                causation_id=None,
                environment=EnvironmentId.generate(),
                payload_hash="abc123",
                sequence=1,
                payload={},
            )

    def test_sequence_non_negative(self):
        """Sequence must be non-negative."""
        with pytest.raises(ValueError, match="non-negative"):
            EventEnvelope(
                event_id=EventId.generate(),
                aggregate_type="Order",
                aggregate_id="order-123",
                event_type="OrderSubmitted",
                schema_version="1.0.0",
                occurred_at_utc=Instant.now(),
                recorded_at_utc=Instant.now(),
                producer="test",
                correlation_id="trace-123",
                causation_id=None,
                environment=EnvironmentId.generate(),
                payload_hash="abc123",
                sequence=-1,
                payload={},
            )

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        envelope = self._make_envelope()
        d = envelope.to_dict()
        assert "event_id" in d
        assert "aggregate_type" in d
        assert "aggregate_id" in d
        assert "event_type" in d
        assert "schema_version" in d
        assert "occurred_at_utc" in d
        assert "recorded_at_utc" in d
        assert "producer" in d
        assert "correlation_id" in d
        assert "causation_id" in d
        assert "environment" in d
        assert "payload_hash" in d
        assert "sequence" in d
        assert "payload" in d

    def test_immutable(self):
        """EventEnvelope should be immutable."""
        envelope = self._make_envelope()
        with pytest.raises(Exception):
            envelope.event_type = "OtherEvent"

    def test_causation_id_optional(self):
        """causation_id should be optional (None for root events)."""
        envelope = self._make_envelope()
        # Root events have no causation
        assert envelope.causation_id is None or isinstance(envelope.causation_id, str)
