"""
G1.6 — Error Taxonomy

Structured error types for the trading system.

Specification references:
- docs/14_reference/01_ERROR_TAXONOMY.md:
  "Validation, authorization, policy, data-quality, provider, network, timeout, state-conflict, reconciliation, persistence, model and system-critical."
- FINAL_SPECIFICATION/02_RUNTIME_CONTRACTS.md (command/event envelopes carry error context)
- FINAL_SPECIFICATION/10_OBSERVABILITY_AND_FAILURES.md (fail-closed conditions)
- docs/02_architecture/08_FAILURE_SEMANTICS.md (failure classes)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .enums import ErrorClass, ReasonCode
from .ids import EntityId
from .time import Instant


@dataclass(frozen=True)
class ErrorDefinition:
    """
    Definition of a canonical error type in the taxonomy.
    Per ERROR_TAXONOMY.md: errors are classified into stable categories.
    """

    code: str
    message_template: str
    error_class: ErrorClass
    reason_code: Optional[ReasonCode] = None
    retryable: bool = False
    scope: str = "domain"

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("code is required")
        if not self.message_template:
            raise ValueError("message_template is required")

    def format_message(self, **kwargs: Any) -> str:
        """Format the message template with provided parameters."""
        return self.message_template.format(**kwargs)


class ErrorTaxonomy:
    """
    Registry of canonical error definitions.
    Per ERROR_TAXONOMY.md: "Validation, authorization, policy, data-quality, provider, network, timeout, state-conflict, reconciliation, persistence, model and system-critical."
    """

    def __init__(self) -> None:
        self._definitions: Dict[str, ErrorDefinition] = {}
        self._by_class: Dict[ErrorClass, List[ErrorDefinition]] = {}
        self._by_scope: Dict[str, List[ErrorDefinition]] = {}

    def register(self, definition: ErrorDefinition) -> None:
        """Register an error definition in the taxonomy."""
        if definition.code in self._definitions:
            raise ValueError(f"Error definition already registered: {definition.code}")
        self._definitions[definition.code] = definition
        self._by_class.setdefault(definition.error_class, []).append(definition)
        self._by_scope.setdefault(definition.scope, []).append(definition)

    def get(self, code: str) -> Optional[ErrorDefinition]:
        """Look up an error definition by code."""
        return self._definitions.get(code)

    def get_by_class(self, error_class: ErrorClass) -> List[ErrorDefinition]:
        """Look up all error definitions for a given error class."""
        return list(self._by_class.get(error_class, []))

    def get_by_scope(self, scope: str) -> List[ErrorDefinition]:
        """Look up all error definitions for a given scope."""
        return list(self._by_scope.get(scope, []))

    def all_codes(self) -> List[str]:
        """Return all registered error codes."""
        return list(self._definitions.keys())

    def __contains__(self, code: str) -> bool:
        return code in self._definitions

    def __len__(self) -> int:
        return len(self._definitions)


# Default taxonomy instance with standard error definitions
_default_taxonomy = ErrorTaxonomy()


def _register_default_errors() -> None:
    """Register the standard set of error definitions."""
    defaults = [
        ErrorDefinition(
            code="VALIDATION_ERROR",
            message_template="Validation failed: {field}",
            error_class=ErrorClass.VALIDATION,
            retryable=False,
        ),
        ErrorDefinition(
            code="AUTHORIZATION_DENIED",
            message_template="Access denied: {reason}",
            error_class=ErrorClass.AUTHORIZATION,
            retryable=False,
        ),
        ErrorDefinition(
            code="POLICY_VIOLATION",
            message_template="Policy violation: {policy}",
            error_class=ErrorClass.POLICY,
            reason_code=ReasonCode.POLICY,
            retryable=False,
        ),
        ErrorDefinition(
            code="DATA_QUALITY_STALE",
            message_template="Data is stale: {source}",
            error_class=ErrorClass.DATA_QUALITY,
            reason_code=ReasonCode.STALE_DATA,
            retryable=True,
        ),
        ErrorDefinition(
            code="DATA_QUALITY_INVALID",
            message_template="Data is invalid: {source}",
            error_class=ErrorClass.DATA_QUALITY,
            reason_code=ReasonCode.STALE_DATA,
            retryable=True,
        ),
        ErrorDefinition(
            code="PROVIDER_UNAVAILABLE",
            message_template="Provider unavailable: {provider}",
            error_class=ErrorClass.PROVIDER,
            retryable=True,
        ),
        ErrorDefinition(
            code="NETWORK_FAILURE",
            message_template="Network failure: {endpoint}",
            error_class=ErrorClass.NETWORK,
            retryable=True,
        ),
        ErrorDefinition(
            code="TIMEOUT",
            message_template="Operation timed out: {operation}",
            error_class=ErrorClass.TIMEOUT,
            retryable=True,
        ),
        ErrorDefinition(
            code="STATE_CONFLICT",
            message_template="State conflict: {state}",
            error_class=ErrorClass.STATE_CONFLICT,
            retryable=False,
        ),
        ErrorDefinition(
            code="RECONCILIATION_MISMATCH",
            message_template="Reconciliation mismatch: {account}",
            error_class=ErrorClass.RECONCILIATION,
            reason_code=ReasonCode.RECONCILIATION,
            retryable=False,
        ),
        ErrorDefinition(
            code="PERSISTENCE_FAILURE",
            message_template="Persistence failure: {operation}",
            error_class=ErrorClass.PERSISTENCE,
            retryable=True,
        ),
        ErrorDefinition(
            code="MODEL_ERROR",
            message_template="Model error: {model}",
            error_class=ErrorClass.MODEL,
            retryable=True,
        ),
        ErrorDefinition(
            code="SYSTEM_CRITICAL",
            message_template="System critical: {component}",
            error_class=ErrorClass.SYSTEM_CRITICAL,
            retryable=False,
        ),
    ]
    for definition in defaults:
        _default_taxonomy.register(definition)


_register_default_errors()


def get_default_taxonomy() -> ErrorTaxonomy:
    """Return the default error taxonomy with standard definitions."""
    return _default_taxonomy


@dataclass(frozen=True)
class TradingError(Exception):
    """
    Base error type for all trading system errors.
    Per ERROR_TAXONOMY.md: errors are classified into stable categories.
    Per FAILURE_SEMANTICS.md: failure classes are Retryable, non-retryable, transient, degraded, unknown-critical, data-invalid and policy-denied.
    """

    error_class: ErrorClass
    reason_code: Optional[ReasonCode]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp: Optional[Instant] = None
    retryable: bool = False

    def __post_init__(self) -> None:
        # Set timestamp if not provided
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", Instant.now())

    def __str__(self) -> str:
        return f"[{self.error_class.value}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize error to dictionary for logging/audit."""
        return {
            "error_class": self.error_class.value,
            "reason_code": self.reason_code.value if self.reason_code else None,
            "message": self.message,
            "details": self.details,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.to_iso8601() if self.timestamp else None,
            "retryable": self.retryable,
        }


# --- Specific error subclasses ---


class ValidationError(TradingError):
    """Input validation failure."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.VALIDATION,
            reason_code=None,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=False,
        )


class AuthorizationError(TradingError):
    """Authorization failure — actor lacks required permission."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.AUTHORIZATION,
            reason_code=None,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=False,
        )


class PolicyError(TradingError):
    """Policy violation — action denied by policy."""

    def __init__(
        self,
        message: str,
        reason_code: Optional[ReasonCode] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.POLICY,
            reason_code=reason_code,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=False,
        )


class DataQualityError(TradingError):
    """Data quality failure — stale, invalid, or missing data."""

    def __init__(
        self,
        message: str,
        reason_code: Optional[ReasonCode] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.DATA_QUALITY,
            reason_code=reason_code or ReasonCode.STALE_DATA,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=True,
        )


class ProviderError(TradingError):
    """External provider failure."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        retryable: bool = True,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.PROVIDER,
            reason_code=None,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=retryable,
        )


class NetworkError(TradingError):
    """Network communication failure."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        retryable: bool = True,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.NETWORK,
            reason_code=None,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=retryable,
        )


class TimeoutError(TradingError):
    """Operation timed out."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.TIMEOUT,
            reason_code=None,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=True,
        )


class StateConflictError(TradingError):
    """State machine transition conflict — invalid state for requested action."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.STATE_CONFLICT,
            reason_code=None,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=False,
        )


class ReconciliationError(TradingError):
    """Reconciliation failure — internal state does not match external state."""

    def __init__(
        self,
        message: str,
        reason_code: Optional[ReasonCode] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.RECONCILIATION,
            reason_code=reason_code or ReasonCode.RECONCILIATION,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=False,
        )


class PersistenceError(TradingError):
    """Persistence layer failure."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        retryable: bool = True,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.PERSISTENCE,
            reason_code=None,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=retryable,
        )


class ModelError(TradingError):
    """AI model failure or invalid output."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.MODEL,
            reason_code=None,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=True,
        )


class SystemCriticalError(TradingError):
    """
    System-critical failure.
    Per FAILURE_SEMANTICS.md: "Unknown-critical: Stops live mutation until state is verified."
    Per OBSERVABILITY_AND_FAILURES.md: "Unknown broker state, stale critical data, failed reconciliation, corrupted event sequence, missing risk approval or authorization ambiguity are fail-closed conditions for live mutation."
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_class=ErrorClass.SYSTEM_CRITICAL,
            reason_code=None,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=False,
        )


__all__ = [
    "ErrorDefinition",
    "ErrorTaxonomy",
    "get_default_taxonomy",
    "TradingError",
    "ValidationError",
    "AuthorizationError",
    "PolicyError",
    "DataQualityError",
    "ProviderError",
    "NetworkError",
    "TimeoutError",
    "StateConflictError",
    "ReconciliationError",
    "PersistenceError",
    "ModelError",
    "SystemCriticalError",
]
