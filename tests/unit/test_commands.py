"""
G1.8 — Unit tests for Command Envelope

Tests:
- Command envelope creation with all required fields
- Payload hash verification
- Actor type validation
- Idempotency key requirement
- Authorization scope requirement
- Immutability
- Serialization
"""

import pytest
from src.domain.commands import CommandEnvelope
from src.domain.correlation import TraceContext
from src.domain.ids import EnvironmentId


class TestCommandEnvelope:
    def _make_trace_context(self) -> TraceContext:
        return TraceContext.new()

    def _make_command(self, **kwargs) -> CommandEnvelope:
        """Helper to create a valid command envelope."""
        defaults = dict(
            actor_id="agent-123",
            actor_type="agent",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            idempotency_key="idem-key-123",
            authorization_scope="trading:order:submit",
            payload={"order_id": "order-123", "side": "BUY"},
            trace_context=self._make_trace_context(),
        )
        defaults.update(kwargs)
        return CommandEnvelope.create(**defaults)

    def test_create_with_all_fields(self):
        """CommandEnvelope.create should set all required fields."""
        cmd = self._make_command()
        assert cmd.command_id is not None
        assert cmd.trace_id is not None
        assert cmd.actor_id == "agent-123"
        assert cmd.actor_type == "agent"
        assert cmd.environment is not None
        assert cmd.schema_version == "1.0.0"
        assert cmd.idempotency_key == "idem-key-123"
        assert cmd.authorization_scope == "trading:order:submit"
        assert cmd.payload_hash is not None

    def test_payload_hash_computed(self):
        """Payload hash should be computed from payload content."""
        cmd = self._make_command(payload={"key": "value"})
        assert cmd.payload_hash is not None
        assert len(cmd.payload_hash) == 64  # SHA-256 hex

    def test_payload_hash_verification(self):
        """verify_integrity should return True for valid hash."""
        cmd = self._make_command()
        assert cmd.verify_integrity() is True

    def test_payload_hash_mismatch_detected(self):
        """verify_integrity should return False for tampered payload."""
        cmd = self._make_command()
        tampered = CommandEnvelope(
            command_id=cmd.command_id,
            trace_id=cmd.trace_id,
            actor_id=cmd.actor_id,
            actor_type=cmd.actor_type,
            environment=cmd.environment,
            issued_at_utc=cmd.issued_at_utc,
            schema_version=cmd.schema_version,
            idempotency_key=cmd.idempotency_key,
            authorization_scope=cmd.authorization_scope,
            payload_hash=cmd.payload_hash,
            payload={"tampered": True},
        )
        assert tampered.verify_integrity() is False

    def test_actor_type_validation(self):
        """actor_type must be 'agent' or 'user'."""
        with pytest.raises(ValueError, match="actor_type"):
            self._make_command(actor_type="invalid")

    def test_actor_type_user(self):
        """actor_type should accept 'user'."""
        cmd = self._make_command(actor_type="user", actor_id="user-123")
        assert cmd.actor_type == "user"

    def test_actor_type_agent(self):
        """actor_type should accept 'agent'."""
        cmd = self._make_command(actor_type="agent", actor_id="agent-123")
        assert cmd.actor_type == "agent"

    def test_idempotency_key_required(self):
        """idempotency_key must not be empty."""
        with pytest.raises(ValueError, match="idempotency_key"):
            self._make_command(idempotency_key="")

    def test_authorization_scope_required(self):
        """authorization_scope must not be empty."""
        with pytest.raises(ValueError, match="authorization_scope"):
            self._make_command(authorization_scope="")

    def test_trace_id_required(self):
        """trace_id must not be empty."""
        with pytest.raises(ValueError, match="trace_id"):
            self._make_command(trace_context=TraceContext.from_trace_id.__self__ if False else TraceContext.new())

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        cmd = self._make_command()
        d = cmd.to_dict()
        assert "command_id" in d
        assert "trace_id" in d
        assert "actor_id" in d
        assert "actor_type" in d
        assert "environment" in d
        assert "issued_at_utc" in d
        assert "schema_version" in d
        assert "idempotency_key" in d
        assert "authorization_scope" in d
        assert "payload_hash" in d
        assert "payload" in d

    def test_immutable(self):
        """CommandEnvelope should be immutable."""
        cmd = self._make_command()
        with pytest.raises(Exception):
            cmd.actor_type = "user"

    def test_issued_at_auto_set(self):
        """issued_at_utc should be auto-set to current time."""
        cmd = self._make_command()
        assert cmd.issued_at_utc is not None
