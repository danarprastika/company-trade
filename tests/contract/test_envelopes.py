"""
G1 — Contract tests for Event and Command Envelopes

Verifies that event and command envelopes conform to the contracts defined in:
- FINAL_SPECIFICATION/02_RUNTIME_CONTRACTS.md
- docs/02_architecture/03_EVENT_ARCHITECTURE.md
- docs/02_architecture/05_SERVICE_CONTRACTS.md
"""

import pytest
from src.domain.events import EventEnvelope
from src.domain.commands import CommandEnvelope
from src.domain.correlation import TraceContext
from src.domain.ids import EnvironmentId, EventId, CommandId
from src.domain.time import Instant


class TestEventEnvelopeContract:
    """
    Contract: Every event carries: event_id, aggregate_type, aggregate_id,
    event_type, schema_version, occurred_at_utc, recorded_at_utc, producer,
    correlation_id, causation_id, environment, payload_hash and sequence.
    """

    def _make_event(self) -> EventEnvelope:
        return EventEnvelope.create(
            aggregate_type="Order",
            aggregate_id="order-123",
            event_type="OrderSubmitted",
            schema_version="1.0.0",
            occurred_at=Instant.now(),
            producer="risk-engine",
            trace_context=TraceContext.new(),
            environment=EnvironmentId.generate(),
            payload={"order_id": "order-123"},
            sequence=1,
        )

    def test_event_has_event_id(self):
        """Event must have event_id."""
        event = self._make_event()
        assert event.event_id is not None
        assert isinstance(event.event_id, EventId)

    def test_event_has_aggregate_type(self):
        """Event must have aggregate_type."""
        event = self._make_event()
        assert event.aggregate_type == "Order"

    def test_event_has_aggregate_id(self):
        """Event must have aggregate_id."""
        event = self._make_event()
        assert event.aggregate_id == "order-123"

    def test_event_has_event_type(self):
        """Event must have event_type."""
        event = self._make_event()
        assert event.event_type == "OrderSubmitted"

    def test_event_has_schema_version(self):
        """Event must have schema_version."""
        event = self._make_event()
        assert event.schema_version == "1.0.0"

    def test_event_has_occurred_at_utc(self):
        """Event must have occurred_at_utc."""
        event = self._make_event()
        assert event.occurred_at_utc is not None
        assert isinstance(event.occurred_at_utc, Instant)

    def test_event_has_recorded_at_utc(self):
        """Event must have recorded_at_utc."""
        event = self._make_event()
        assert event.recorded_at_utc is not None
        assert isinstance(event.recorded_at_utc, Instant)

    def test_event_has_producer(self):
        """Event must have producer."""
        event = self._make_event()
        assert event.producer == "risk-engine"

    def test_event_has_correlation_id(self):
        """Event must have correlation_id."""
        event = self._make_event()
        assert event.correlation_id is not None
        assert len(event.correlation_id) > 0

    def test_event_has_causation_id(self):
        """Event must have causation_id (can be None for root events)."""
        event = self._make_event()
        assert hasattr(event, "causation_id")

    def test_event_has_environment(self):
        """Event must have environment."""
        event = self._make_event()
        assert event.environment is not None
        assert isinstance(event.environment, EnvironmentId)

    def test_event_has_payload_hash(self):
        """Event must have payload_hash."""
        event = self._make_event()
        assert event.payload_hash is not None
        assert len(event.payload_hash) == 64  # SHA-256

    def test_event_has_sequence(self):
        """Event must have sequence."""
        event = self._make_event()
        assert event.sequence == 1

    def test_event_is_immutable(self):
        """Event must be immutable (AD-003: immutable events)."""
        event = self._make_event()
        with pytest.raises(Exception):
            event.event_type = "OtherEvent"

    def test_event_payload_hash_verifiable(self):
        """Event payload hash must be verifiable (AD-007: hash chaining)."""
        event = self._make_event()
        assert event.verify_integrity() is True


class TestCommandEnvelopeContract:
    """
    Contract: Every command carries: command_id, trace_id, actor_id, actor_type,
    environment, issued_at_utc, schema_version, idempotency_key, authorization_scope
    and payload_hash.
    """

    def _make_command(self) -> CommandEnvelope:
        return CommandEnvelope.create(
            actor_id="agent-123",
            actor_type="agent",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            idempotency_key="idem-key-123",
            authorization_scope="trading:order:submit",
            payload={"order_id": "order-123"},
            trace_context=TraceContext.new(),
        )

    def test_command_has_command_id(self):
        """Command must have command_id."""
        cmd = self._make_command()
        assert cmd.command_id is not None
        assert isinstance(cmd.command_id, CommandId)

    def test_command_has_trace_id(self):
        """Command must have trace_id."""
        cmd = self._make_command()
        assert cmd.trace_id is not None
        assert len(cmd.trace_id) > 0

    def test_command_has_actor_id(self):
        """Command must have actor_id."""
        cmd = self._make_command()
        assert cmd.actor_id == "agent-123"

    def test_command_has_actor_type(self):
        """Command must have actor_type."""
        cmd = self._make_command()
        assert cmd.actor_type == "agent"

    def test_command_has_environment(self):
        """Command must have environment."""
        cmd = self._make_command()
        assert cmd.environment is not None
        assert isinstance(cmd.environment, EnvironmentId)

    def test_command_has_issued_at_utc(self):
        """Command must have issued_at_utc."""
        cmd = self._make_command()
        assert cmd.issued_at_utc is not None
        assert isinstance(cmd.issued_at_utc, Instant)

    def test_command_has_schema_version(self):
        """Command must have schema_version."""
        cmd = self._make_command()
        assert cmd.schema_version == "1.0.0"

    def test_command_has_idempotency_key(self):
        """Command must have idempotency_key (CACHING_AND_IDEMPOTENCY.md)."""
        cmd = self._make_command()
        assert cmd.idempotency_key == "idem-key-123"

    def test_command_has_authorization_scope(self):
        """Command must have authorization_scope (AUTHENTICATION_AUTHORIZATION.md)."""
        cmd = self._make_command()
        assert cmd.authorization_scope == "trading:order:submit"

    def test_command_has_payload_hash(self):
        """Command must have payload_hash."""
        cmd = self._make_command()
        assert cmd.payload_hash is not None
        assert len(cmd.payload_hash) == 64  # SHA-256

    def test_command_is_immutable(self):
        """Command must be immutable."""
        cmd = self._make_command()
        with pytest.raises(Exception):
            cmd.actor_type = "user"

    def test_command_payload_hash_verifiable(self):
        """Command payload hash must be verifiable."""
        cmd = self._make_command()
        assert cmd.verify_integrity() is True

    def test_command_actor_type_must_be_agent_or_user(self):
        """Command actor_type must be 'agent' or 'user'."""
        with pytest.raises(ValueError, match="actor_type"):
            CommandEnvelope.create(
                actor_id="test",
                actor_type="invalid",
                environment=EnvironmentId.generate(),
                schema_version="1.0.0",
                idempotency_key="key",
                authorization_scope="scope",
                payload={},
                trace_context=TraceContext.new(),
            )
