"""
G1.8 — Command Envelope

Immutable command envelope with all required fields for the command path.

Specification references:
- FINAL_SPECIFICATION/02_RUNTIME_CONTRACTS.md:
  "Every command carries: command_id, trace_id, actor_id, actor_type, environment, issued_at_utc, schema_version, idempotency_key, authorization_scope and payload_hash."
- FINAL_SPECIFICATION/01_ARCHITECTURE_DECISIONS.md AD-003:
  "Domain state changes are represented by immutable events; commands request changes and events record accepted changes."
- docs/02_architecture/03_EVENT_ARCHITECTURE.md:
  "Commands request actions; events report facts."
- docs/02_architecture/07_CACHING_AND_IDEMPOTENCY.md:
  "Order submission, command execution, event handling, reconciliation and financial mutations require explicit idempotency strategy."
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict

from .correlation import TraceContext
from .ids import CommandId, EnvironmentId
from .time import Instant


@dataclass(frozen=True)
class CommandEnvelope:
    """
    Immutable command envelope.
    Per RUNTIME_CONTRACTS.md: "Every command carries: command_id, trace_id, actor_id, actor_type, environment, issued_at_utc, schema_version, idempotency_key, authorization_scope and payload_hash."
    """

    command_id: CommandId
    trace_id: str
    actor_id: str
    actor_type: str  # "agent" or "user"
    environment: EnvironmentId
    issued_at_utc: Instant
    schema_version: str
    idempotency_key: str
    authorization_scope: str
    payload_hash: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validate required fields
        if not self.trace_id:
            raise ValueError("trace_id is required")
        if not self.actor_id:
            raise ValueError("actor_id is required")
        if self.actor_type not in ("agent", "user"):
            raise ValueError(f"actor_type must be 'agent' or 'user', got {self.actor_type!r}")
        if not self.schema_version:
            raise ValueError("schema_version is required")
        if not self.idempotency_key:
            raise ValueError("idempotency_key is required")
        if not self.authorization_scope:
            raise ValueError("authorization_scope is required")

        # Validate payload hash matches payload
        computed_hash = self._compute_payload_hash(self.payload)
        if computed_hash != self.payload_hash:
            raise ValueError("payload_hash does not match payload content")

    @staticmethod
    def _compute_payload_hash(payload: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of the payload."""
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    @classmethod
    def create(
        cls,
        actor_id: str,
        actor_type: str,
        environment: EnvironmentId,
        schema_version: str,
        idempotency_key: str,
        authorization_scope: str,
        payload: Dict[str, Any],
        trace_context: TraceContext,
    ) -> "CommandEnvelope":
        """
        Create a new command envelope with computed payload hash.
        """
        issued_at = Instant.now()
        payload_hash = cls._compute_payload_hash(payload)

        return cls(
            command_id=CommandId.generate(),
            trace_id=str(trace_context.trace_id),
            actor_id=actor_id,
            actor_type=actor_type,
            environment=environment,
            issued_at_utc=issued_at,
            schema_version=schema_version,
            idempotency_key=idempotency_key,
            authorization_scope=authorization_scope,
            payload_hash=payload_hash,
            payload=payload,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize command envelope to dictionary."""
        return {
            "command_id": str(self.command_id),
            "trace_id": self.trace_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "environment": str(self.environment),
            "issued_at_utc": self.issued_at_utc.to_iso8601(),
            "schema_version": self.schema_version,
            "idempotency_key": self.idempotency_key,
            "authorization_scope": self.authorization_scope,
            "payload_hash": self.payload_hash,
            "payload": self.payload,
        }

    def verify_integrity(self) -> bool:
        """
        Verify that the payload hash matches the payload content.
        """
        computed_hash = self._compute_payload_hash(self.payload)
        return computed_hash == self.payload_hash


__all__ = [
    "CommandEnvelope",
]
