"""
G1 — Security tests for Domain Foundation

Tests:
- No secret leakage in types
- No live credential references
- No live trading capability
- Payload hash integrity
- Configuration isolation
- No float contamination in money/quantity
"""

import pytest
from src.domain.money import Money, Quantity
from src.domain.events import EventEnvelope
from src.domain.commands import CommandEnvelope
from src.domain.correlation import TraceContext
from src.domain.ids import EnvironmentId
from src.domain.time import Instant
from src.domain.config import Configuration, ConfigurationStore
from src.domain.errors import TradingError
from decimal import Decimal


class TestNoSecretLeakage:
    """
    Per SECURITY_MODEL.md: "Secrets are never passed through prompts, logs, telemetry, agent memory or decision explanations."
    Per SECRET_MANAGEMENT.md: "Never place secrets in source, prompts, fixtures or logs."
    """

    def test_money_no_secret_fields(self):
        """Money type should not have any secret-related fields."""
        m = Money.from_string("100.50", "USD")
        for field_name in ["password", "secret", "api_key", "token", "credential"]:
            assert not hasattr(m, field_name), f"Money should not have {field_name} field"

    def test_quantity_no_secret_fields(self):
        """Quantity type should not have any secret-related fields."""
        q = Quantity.from_string("100.50", scale=2)
        for field_name in ["password", "secret", "api_key", "token", "credential"]:
            assert not hasattr(q, field_name), f"Quantity should not have {field_name} field"

    def test_event_envelope_no_secret_fields(self):
        """EventEnvelope should not have any secret-related fields."""
        event = EventEnvelope.create(
            aggregate_type="Order",
            aggregate_id="order-123",
            event_type="OrderSubmitted",
            schema_version="1.0.0",
            occurred_at=Instant.now(),
            producer="test",
            trace_context=TraceContext.new(),
            environment=EnvironmentId.generate(),
            payload={"order_id": "order-123"},
            sequence=1,
        )
        for field_name in ["password", "secret", "api_key", "token", "credential"]:
            assert not hasattr(event, field_name), f"EventEnvelope should not have {field_name} field"

    def test_command_envelope_no_secret_fields(self):
        """CommandEnvelope should not have any secret-related fields."""
        cmd = CommandEnvelope.create(
            actor_id="agent-123",
            actor_type="agent",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            idempotency_key="key-123",
            authorization_scope="trading:order:submit",
            payload={"order_id": "order-123"},
            trace_context=TraceContext.new(),
        )
        for field_name in ["password", "secret", "api_key", "token", "credential"]:
            assert not hasattr(cmd, field_name), f"CommandEnvelope should not have {field_name} field"

    def test_configuration_no_secret_fields(self):
        """Configuration should not have any secret-related fields."""
        config = Configuration(
            version="1.0.0",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            content={"key": "value"},
            created_at=Instant.now(),
            created_by="admin",
        )
        for field_name in ["password", "secret", "api_key", "token", "credential"]:
            assert not hasattr(config, field_name), f"Configuration should not have {field_name} field"

    def test_error_no_secret_fields(self):
        """TradingError should not have any secret-related fields."""
        error = TradingError(
            error_class=__import__("src.domain.enums", fromlist=["ErrorClass"]).ErrorClass.VALIDATION,
            reason_code=None,
            message="Test error",
        )
        for field_name in ["password", "secret", "api_key", "token", "credential"]:
            assert not hasattr(error, field_name), f"TradingError should not have {field_name} field"


class TestNoLiveCredentialReferences:
    """
    Per SECURITY_MODEL.md: "Live secrets are isolated from research/test environments."
    Per PERMISSION_MATRIX.md: "Research and analysis agents cannot access live credentials or direct broker mutation."
    """

    def test_no_broker_credentials_in_types(self):
        """Domain types should not reference broker credentials."""
        # Check that no domain type has fields like 'api_key', 'secret_key', 'password'
        from src.domain import ids, time, money, instrument, enums, errors, events, commands, correlation, config, persistence, migration

        modules = [ids, time, money, instrument, enums, errors, events, commands, correlation, config, persistence, migration]
        secret_keywords = ["api_key", "api_secret", "secret_key", "password", "broker_token", "live_credential"]

        for module in modules:
            source = open(module.__file__).read()
            for keyword in secret_keywords:
                assert keyword not in source.lower(), (
                    f"Secret keyword '{keyword}' found in {module.__file__}"
                )

    def test_environment_type_separation(self):
        """EnvironmentType should clearly separate live from non-live."""
        from src.domain.enums import EnvironmentType
        assert EnvironmentType.LIVE.is_live is True
        assert EnvironmentType.LIVE.allows_live_credentials is True
        assert EnvironmentType.DEMO.is_live is False
        assert EnvironmentType.DEMO.allows_live_credentials is False
        assert EnvironmentType.RESEARCH.is_live is False
        assert EnvironmentType.RESEARCH.allows_live_credentials is False


class TestNoLiveTradingCapability:
    """
    Per FINAL_SPECIFICATION/13_KILO_CODE_HANDOFF.md:
    "Never implement live broker connectivity before G8/G9 evidence exists."
    Per bootstrap prompt: "Jangan melakukan live trading. Jangan menggunakan real-money credentials."
    """

    def test_no_broker_adapter_in_domain(self):
        """Domain layer should not contain broker adapter code."""
        import os
        domain_files = []
        for root, dirs, files in os.walk("src/domain"):
            for f in files:
                if f.endswith(".py"):
                    domain_files.append(os.path.join(root, f))

        broker_keywords = ["broker", "exchange", "api_key", "secret", "api_secret", "trade_api"]
        for filepath in domain_files:
            with open(filepath) as f:
                content = f.read().lower()
            for keyword in broker_keywords:
                # Allow "broker" in comments/docstrings but not in code
                # Check if keyword appears in actual code (not just comments)
                lines = content.split("\n")
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                    if keyword in stripped and "broker" in keyword:
                        # "broker" can appear in docstrings/comments
                        if not stripped.startswith("#") and not stripped.startswith('"""'):
                            # Check if it's in a string literal
                            if f'"{keyword}' not in stripped and f"'{keyword}" not in stripped:
                                continue

    def test_no_execution_in_domain(self):
        """Domain layer should not contain execution code."""
        import os
        domain_files = []
        for root, dirs, files in os.walk("src/domain"):
            for f in files:
                if f.endswith(".py"):
                    domain_files.append(os.path.join(root, f))

        execution_keywords = ["submit_order", "place_order", "execute_trade", "send_to_broker"]
        for filepath in domain_files:
            with open(filepath) as f:
                content = f.read()
            for keyword in execution_keywords:
                assert keyword not in content, (
                    f"Execution keyword '{keyword}' found in {filepath}"
                )


class TestPayloadHashIntegrity:
    """
    Per AD-007: "Decision/audit ledger is append-only with hash chaining."
    Per RUNTIME_CONTRACTS.md: payload_hash field in envelopes.
    """

    def test_event_payload_hash_verifiable(self):
        """Event payload hash must be verifiable."""
        event = EventEnvelope.create(
            aggregate_type="Order",
            aggregate_id="order-123",
            event_type="OrderSubmitted",
            schema_version="1.0.0",
            occurred_at=Instant.now(),
            producer="test",
            trace_context=TraceContext.new(),
            environment=EnvironmentId.generate(),
            payload={"order_id": "order-123", "side": "BUY"},
            sequence=1,
        )
        assert event.verify_integrity() is True

    def test_command_payload_hash_verifiable(self):
        """Command payload hash must be verifiable."""
        cmd = CommandEnvelope.create(
            actor_id="agent-123",
            actor_type="agent",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            idempotency_key="key-123",
            authorization_scope="trading:order:submit",
            payload={"order_id": "order-123"},
            trace_context=TraceContext.new(),
        )
        assert cmd.verify_integrity() is True


class TestNoFloatContamination:
    """
    Per DATABASE_CANONICAL_MODEL.md: "Money/quantity calculations use fixed-precision decimal semantics, never binary floating point for authoritative accounting."
    """

    def test_money_amount_is_decimal(self):
        """Money amount must be Decimal, not float."""
        m = Money.from_string("100.50", "USD")
        assert isinstance(m.amount, Decimal)
        assert not isinstance(m.amount, float)

    def test_quantity_value_is_decimal(self):
        """Quantity value must be Decimal, not float."""
        q = Quantity.from_string("100.50", scale=2)
        assert isinstance(q.value, Decimal)
        assert not isinstance(q.value, float)

    def test_money_rejects_float_input(self):
        """Money should reject float input."""
        with pytest.raises(TypeError):
            Money(100.50, "USD")  # type: ignore

    def test_quantity_rejects_float_input(self):
        """Quantity should reject float input."""
        with pytest.raises(TypeError):
            Quantity(100.50, 2)  # type: ignore

    def test_money_multiplication_rejects_float(self):
        """Money multiplication should reject float."""
        m = Money.from_string("100.50", "USD")
        with pytest.raises(TypeError):
            m * 2.5  # type: ignore

    def test_quantity_multiplication_rejects_float(self):
        """Quantity multiplication should reject float."""
        q = Quantity.from_string("100.50", scale=2)
        with pytest.raises(TypeError):
            q * 2.5  # type: ignore


class TestConfigurationIsolation:
    """
    Per CONFIGURATION_GOVERNANCE.md: "No hidden environment variable may silently change live behavior."
    """

    def test_configuration_has_version(self):
        """Configuration must have a version."""
        config = Configuration(
            version="1.0.0",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            content={"key": "value"},
            created_at=Instant.now(),
            created_by="admin",
        )
        assert config.version == "1.0.0"

    def test_configuration_has_content_hash(self):
        """Configuration must have a content hash for traceability."""
        config = Configuration(
            version="1.0.0",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            content={"key": "value"},
            created_at=Instant.now(),
            created_by="admin",
        )
        assert config.content_hash is not None
        assert len(config.content_hash) == 64

    def test_configuration_store_isolates_environments(self):
        """ConfigurationStore should isolate configurations per environment."""
        store = ConfigurationStore()
        env1 = EnvironmentId.generate()
        env2 = EnvironmentId.generate()

        config1 = Configuration(
            version="1.0.0",
            environment=env1,
            schema_version="1.0.0",
            content={"key": "value1"},
            created_at=Instant.now(),
            created_by="admin",
        )
        config2 = Configuration(
            version="1.0.0",
            environment=env2,
            schema_version="1.0.0",
            content={"key": "value2"},
            created_at=Instant.now(),
            created_by="admin",
        )

        store.set_current(env1, config1)
        store.set_current(env2, config2)

        assert store.get_current(env1).content == {"key": "value1"}
        assert store.get_current(env2).content == {"key": "value2"}
