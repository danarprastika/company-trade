"""
G1.1 — Unit tests for Canonical ID Types

Tests:
- ID generation produces unique, time-ordered UUIDv7
- ID parsing from string
- Typed ID variants are distinct types
- ID immutability
"""

import uuid
import pytest
from src.domain.ids import (
    EntityId,
    AgentId,
    OrderId,
    StrategyId,
    InstrumentId,
    AccountId,
    PortfolioId,
    EnvironmentId,
    DeploymentId,
    ExperimentId,
    DatasetId,
    EventId,
    CommandId,
    TraceId,
    ApprovalId,
    ChangeRequestId,
)


class TestEntityId:
    def test_generate_creates_uuidv7(self):
        """Generated IDs should be UUIDv7 (time-ordered)."""
        id1 = EntityId.generate()
        id2 = EntityId.generate()
        assert isinstance(id1.value, uuid.UUID)
        assert isinstance(id2.value, uuid.UUID)
        assert id1.value != id2.value

    def test_from_string_parses_valid_uuid(self):
        """from_string should parse a valid UUID string."""
        uuid_str = "01890a5c-6f3e-7d2e-8000-000000000001"
        id_obj = EntityId.from_string(uuid_str)
        assert str(id_obj.value) == uuid_str

    def test_from_string_rejects_invalid_uuid(self):
        """from_string should reject invalid UUID strings."""
        with pytest.raises(ValueError):
            EntityId.from_string("not-a-uuid")

    def test_immutable(self):
        """EntityId should be immutable."""
        id_obj = EntityId.generate()
        with pytest.raises(Exception):
            id_obj.value = uuid.uuid7()

    def test_str_representation(self):
        """str() should return the UUID string."""
        id_obj = EntityId.generate()
        assert str(id_obj) == str(id_obj.value)

    def test_repr_includes_class_name(self):
        """repr() should include the class name."""
        id_obj = AgentId.generate()
        assert "AgentId" in repr(id_obj)


class TestTypedIds:
    def test_typed_ids_are_distinct(self):
        """Different ID types should not be equal even with same UUID."""
        uuid_val = uuid.uuid7()
        agent_id = AgentId(uuid_val)
        order_id = OrderId(uuid_val)
        assert agent_id != order_id

    def test_typed_id_generation(self):
        """Each typed ID should generate correctly."""
        agent_id = AgentId.generate()
        order_id = OrderId.generate()
        strategy_id = StrategyId.generate()
        assert isinstance(agent_id.value, uuid.UUID)
        assert isinstance(order_id.value, uuid.UUID)
        assert isinstance(strategy_id.value, uuid.UUID)

    def test_all_typed_ids_can_generate(self):
        """All typed ID variants should be generatable."""
        ids = [
            AgentId.generate(),
            OrderId.generate(),
            StrategyId.generate(),
            InstrumentId.generate(),
            AccountId.generate(),
            PortfolioId.generate(),
            EnvironmentId.generate(),
            DeploymentId.generate(),
            ExperimentId.generate(),
            DatasetId.generate(),
            EventId.generate(),
            CommandId.generate(),
            TraceId.generate(),
            ApprovalId.generate(),
            ChangeRequestId.generate(),
        ]
        assert len(ids) == 15
        # All should be unique
        values = [str(i) for i in ids]
        assert len(set(values)) == 15

    def test_typed_id_from_string(self):
        """Typed IDs should parse from strings."""
        uuid_str = "01890a5c-6f3e-7d2e-8000-000000000001"
        agent_id = AgentId.from_string(uuid_str)
        assert str(agent_id) == uuid_str

    def test_typed_id_hashable(self):
        """Typed IDs should be hashable (usable as dict keys)."""
        agent_id = AgentId.generate()
        d = {agent_id: "test"}
        assert d[agent_id] == "test"
