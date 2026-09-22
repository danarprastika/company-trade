"""
G1.10 — Configuration Model

Versioned, traceable configuration with schema validation.
No hidden environment variable may silently change live behavior.

Specification references:
- docs/00_governance/06_CONFIGURATION_GOVERNANCE.md:
  "Make configuration a versioned and auditable artifact."
  "No hidden environment variable may silently change live behavior."
  "Configuration schema, semantic validation, approval and rollback are required for live-impacting changes."
- FINAL_SPECIFICATION/01_ARCHITECTURE_DECISIONS.md AD-010:
  "Live strategy/model/prompt/config references are content-addressed and immutable during deployment."
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .ids import EnvironmentId
from .time import Instant


@dataclass(frozen=True)
class Configuration:
    """
    Versioned configuration with content hash for traceability.
    Per CONFIGURATION_GOVERNANCE.md: "Effective configuration is resolved, versioned and traceable."
    """

    version: str
    environment: EnvironmentId
    schema_version: str
    content: Dict[str, Any]
    created_at: Instant
    created_by: str  # actor_id
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        # Compute content hash from the configuration content
        content_str = json.dumps(self.content, sort_keys=True, default=str)
        computed_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
        object.__setattr__(self, "content_hash", computed_hash)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dotted key path."""
        keys = key.split(".")
        value: Any = self.content
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def validate(self, schema: Dict[str, Any]) -> List[str]:
        """
        Validate configuration against a schema.
        Returns list of validation errors (empty if valid).
        Per CONFIGURATION_GOVERNANCE.md: "Configuration schema, semantic validation, approval and rollback are required."
        """
        errors: List[str] = []

        for key, expected_type in schema.items():
            if key not in self.content:
                errors.append(f"Missing required key: {key}")
                continue

            value = self.content[key]
            if not self._check_type(value, expected_type):
                errors.append(
                    f"Key '{key}' has type {type(value).__name__}, expected {expected_type}"
                )

        return errors

    @staticmethod
    def _check_type(value: Any, expected_type: Any) -> bool:
        """Check if value matches expected type."""
        if isinstance(expected_type, type):
            return isinstance(value, expected_type)
        if isinstance(expected_type, dict):
            if not isinstance(value, dict):
                return False
            for k, v in expected_type.items():
                if k not in value:
                    return False
                if not Configuration._check_type(value[k], v):
                    return False
            return True
        if isinstance(expected_type, list):
            if not isinstance(value, list):
                return False
            if len(expected_type) == 1:
                return all(Configuration._check_type(v, expected_type[0]) for v in value)
            return True
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to dictionary."""
        return {
            "version": self.version,
            "environment": str(self.environment),
            "schema_version": self.schema_version,
            "content": self.content,
            "created_at": self.created_at.to_iso8601(),
            "created_by": self.created_by,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True)
class ConfigurationChange:
    """
    Record of a configuration change for audit trail.
    Per CONFIGURATION_GOVERNANCE.md: "Effective configuration is resolved, versioned and traceable."
    """

    change_id: str
    old_version: Optional[str]
    new_version: str
    environment: EnvironmentId
    changed_by: str
    changed_at: Instant
    reason: str
    approval_required: bool
    approved_by: Optional[str] = None
    approved_at: Optional[Instant] = None

    def __post_init__(self) -> None:
        if self.approval_required and self.approved_by is None:
            raise ValueError("Configuration change requires approval but no approver was set")
        if self.approval_required and self.approved_at is None:
            raise ValueError("Configuration change requires approval but no approval timestamp was set")


class ConfigurationStore:
    """
    In-memory configuration store for G1 foundation.
    Per CONFIGURATION_GOVERNANCE.md: "No hidden environment variable may silently change live behavior."
    """

    def __init__(self) -> None:
        self._configs: Dict[str, Configuration] = {}  # version -> config
        self._current: Dict[str, Configuration] = {}  # environment -> current config
        self._changes: List[ConfigurationChange] = []

    def store(self, config: Configuration) -> None:
        """Store a configuration version."""
        self._configs[config.version] = config

    def set_current(self, environment: EnvironmentId, config: Configuration) -> None:
        """Set the current configuration for an environment."""
        self._current[str(environment)] = config

    def get_current(self, environment: EnvironmentId) -> Optional[Configuration]:
        """Get the current configuration for an environment."""
        return self._current.get(str(environment))

    def get_by_version(self, version: str) -> Optional[Configuration]:
        """Get a configuration by version."""
        return self._configs.get(version)

    def record_change(self, change: ConfigurationChange) -> None:
        """Record a configuration change."""
        self._changes.append(change)

    def get_changes(self) -> List[ConfigurationChange]:
        """Get all configuration changes."""
        return list(self._changes)

    def resolve(self, environment: EnvironmentId, overrides: Optional[Dict[str, Any]] = None) -> Configuration:
        """
        Resolve effective configuration for an environment.
        Per CONFIGURATION_GOVERNANCE.md: "Effective configuration is resolved, versioned and traceable."
        """
        config = self._current.get(str(environment))
        if config is None:
            raise ValueError(f"No configuration found for environment {environment}")

        if overrides:
            merged_content = {**config.content, **overrides}
            return Configuration(
                version=config.version,
                environment=config.environment,
                schema_version=config.schema_version,
                content=merged_content,
                created_at=config.created_at,
                created_by=config.created_by,
            )

        return config


__all__ = [
    "Configuration",
    "ConfigurationChange",
    "ConfigurationStore",
]
