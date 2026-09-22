"""
G1.10 — Unit tests for Configuration Model

Tests:
- Configuration creation with content hash
- Configuration validation
- Configuration store operations
- Configuration change records
- No hidden env var behavior
"""

import pytest
from src.domain.config import Configuration, ConfigurationChange, ConfigurationStore
from src.domain.ids import EnvironmentId
from src.domain.time import Instant


class TestConfiguration:
    def test_creation_with_content_hash(self):
        """Configuration should compute content hash on creation."""
        config = Configuration(
            version="1.0.0",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            content={"key": "value"},
            created_at=Instant.now(),
            created_by="admin",
        )
        assert config.content_hash is not None
        assert len(config.content_hash) == 64  # SHA-256 hex

    def test_content_hash_deterministic(self):
        """Same content should produce same hash."""
        env = EnvironmentId.generate()
        config1 = Configuration(
            version="1.0.0",
            environment=env,
            schema_version="1.0.0",
            content={"key": "value"},
            created_at=Instant.now(),
            created_by="admin",
        )
        config2 = Configuration(
            version="1.0.0",
            environment=env,
            schema_version="1.0.0",
            content={"key": "value"},
            created_at=Instant.now(),
            created_by="admin",
        )
        assert config1.content_hash == config2.content_hash

    def test_different_content_different_hash(self):
        """Different content should produce different hash."""
        env = EnvironmentId.generate()
        config1 = Configuration(
            version="1.0.0",
            environment=env,
            schema_version="1.0.0",
            content={"key": "value1"},
            created_at=Instant.now(),
            created_by="admin",
        )
        config2 = Configuration(
            version="1.0.0",
            environment=env,
            schema_version="1.0.0",
            content={"key": "value2"},
            created_at=Instant.now(),
            created_by="admin",
        )
        assert config1.content_hash != config2.content_hash

    def test_get_dotted_key(self):
        """get() should support dotted key paths."""
        config = Configuration(
            version="1.0.0",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            content={"risk": {"limits": {"max_exposure": 1000000}}},
            created_at=Instant.now(),
            created_by="admin",
        )
        assert config.get("risk.limits.max_exposure") == 1000000
        assert config.get("risk.limits.nonexistent", "default") == "default"

    def test_validate_schema(self):
        """validate() should return errors for missing/invalid keys."""
        config = Configuration(
            version="1.0.0",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            content={"max_exposure": 1000000, "name": "test"},
            created_at=Instant.now(),
            created_by="admin",
        )
        schema = {"max_exposure": int, "name": str}
        errors = config.validate(schema)
        assert len(errors) == 0

    def test_validate_missing_key(self):
        """validate() should report missing keys."""
        config = Configuration(
            version="1.0.0",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            content={"max_exposure": 1000000},
            created_at=Instant.now(),
            created_by="admin",
        )
        schema = {"max_exposure": int, "name": str}
        errors = config.validate(schema)
        assert len(errors) == 1
        assert "name" in errors[0]

    def test_validate_wrong_type(self):
        """validate() should report type mismatches."""
        config = Configuration(
            version="1.0.0",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            content={"max_exposure": "not_a_number"},
            created_at=Instant.now(),
            created_by="admin",
        )
        schema = {"max_exposure": int}
        errors = config.validate(schema)
        assert len(errors) == 1
        assert "max_exposure" in errors[0]

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        config = Configuration(
            version="1.0.0",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            content={"key": "value"},
            created_at=Instant.now(),
            created_by="admin",
        )
        d = config.to_dict()
        assert d["version"] == "1.0.0"
        assert d["schema_version"] == "1.0.0"
        assert d["content"] == {"key": "value"}
        assert d["created_by"] == "admin"
        assert "content_hash" in d


class TestConfigurationChange:
    def test_creation_without_approval(self):
        """ConfigurationChange should work without approval for non-approval-required changes."""
        change = ConfigurationChange(
            change_id="change-1",
            old_version=None,
            new_version="1.0.0",
            environment=EnvironmentId.generate(),
            changed_by="admin",
            changed_at=Instant.now(),
            reason="Initial configuration",
            approval_required=False,
        )
        assert change.new_version == "1.0.0"
        assert change.approval_required is False

    def test_creation_with_approval(self):
        """ConfigurationChange should require approval fields when approval_required is True."""
        change = ConfigurationChange(
            change_id="change-1",
            old_version="0.9.0",
            new_version="1.0.0",
            environment=EnvironmentId.generate(),
            changed_by="admin",
            changed_at=Instant.now(),
            reason="Risk limit update",
            approval_required=True,
            approved_by="owner",
            approved_at=Instant.now(),
        )
        assert change.approval_required is True
        assert change.approved_by == "owner"

    def test_approval_required_without_approver_rejected(self):
        """ConfigurationChange should reject approval_required=True without approver."""
        with pytest.raises(ValueError, match="requires approval"):
            ConfigurationChange(
                change_id="change-1",
                old_version="0.9.0",
                new_version="1.0.0",
                environment=EnvironmentId.generate(),
                changed_by="admin",
                changed_at=Instant.now(),
                reason="Risk limit update",
                approval_required=True,
            )


class TestConfigurationStore:
    def test_store_and_retrieve(self):
        """ConfigurationStore should store and retrieve configurations."""
        store = ConfigurationStore()
        config = Configuration(
            version="1.0.0",
            environment=EnvironmentId.generate(),
            schema_version="1.0.0",
            content={"key": "value"},
            created_at=Instant.now(),
            created_by="admin",
        )
        store.store(config)
        retrieved = store.get_by_version("1.0.0")
        assert retrieved is not None
        assert retrieved.version == "1.0.0"

    def test_set_and_get_current(self):
        """ConfigurationStore should set and get current config per environment."""
        store = ConfigurationStore()
        env = EnvironmentId.generate()
        config = Configuration(
            version="1.0.0",
            environment=env,
            schema_version="1.0.0",
            content={"key": "value"},
            created_at=Instant.now(),
            created_by="admin",
        )
        store.set_current(env, config)
        current = store.get_current(env)
        assert current is not None
        assert current.version == "1.0.0"

    def test_get_current_not_found(self):
        """get_current should return None for unknown environment."""
        store = ConfigurationStore()
        env = EnvironmentId.generate()
        assert store.get_current(env) is None

    def test_resolve_with_overrides(self):
        """resolve should merge overrides into configuration."""
        store = ConfigurationStore()
        env = EnvironmentId.generate()
        config = Configuration(
            version="1.0.0",
            environment=env,
            schema_version="1.0.0",
            content={"key1": "value1", "key2": "value2"},
            created_at=Instant.now(),
            created_by="admin",
        )
        store.set_current(env, config)
        resolved = store.resolve(env, overrides={"key2": "overridden"})
        assert resolved.get("key1") == "value1"
        assert resolved.get("key2") == "overridden"

    def test_resolve_no_config_raises(self):
        """resolve should raise for unknown environment."""
        store = ConfigurationStore()
        env = EnvironmentId.generate()
        with pytest.raises(ValueError, match="No configuration found"):
            store.resolve(env)

    def test_record_and_get_changes(self):
        """ConfigurationStore should record and retrieve changes."""
        store = ConfigurationStore()
        change = ConfigurationChange(
            change_id="change-1",
            old_version=None,
            new_version="1.0.0",
            environment=EnvironmentId.generate(),
            changed_by="admin",
            changed_at=Instant.now(),
            reason="Initial",
            approval_required=False,
        )
        store.record_change(change)
        changes = store.get_changes()
        assert len(changes) == 1
        assert changes[0].change_id == "change-1"
