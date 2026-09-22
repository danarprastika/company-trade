"""
G1.5 — Enum Definitions

Stable, versioned enums for status codes, reason codes, and error classes.

Specification references:
- FINAL_SPECIFICATION/03_STATE_MACHINES.md (Order, Strategy, Reconciliation, Provider, Agent, Environment states)
- FINAL_SPECIFICATION/04_EVENT_CATALOG.md (event types)
- docs/14_reference/03_STATUS_CODE_CATALOG.md (status codes)
- docs/14_reference/02_REASON_CODE_CATALOG.md (reason codes)
- docs/14_reference/01_ERROR_TAXONOMY.md (error classes)
- docs/06_trading/03_RISK_REASON_CODES.md (risk reason code categories)
"""

from __future__ import annotations

from enum import Enum


class OrderStatus(str, Enum):
    """
    Order lifecycle states.
    Per FINAL_SPECIFICATION/03_STATE_MACHINES.md:
    DRAFT → RISK_PENDING → RISK_APPROVED → OMS_ACCEPTED → SUBMITTING → ACKNOWLEDGED → PARTIALLY_FILLED → FILLED
    Terminal/exception: CANCEL_PENDING, CANCELLED, REJECTED, EXPIRED, FAILED, UNKNOWN
    """

    DRAFT = "DRAFT"
    RISK_PENDING = "RISK_PENDING"
    RISK_APPROVED = "RISK_APPROVED"
    OMS_ACCEPTED = "OMS_ACCEPTED"
    SUBMITTING = "SUBMITTING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"

    @property
    def is_terminal(self) -> bool:
        """States from which no further transitions are expected."""
        return self in {
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
            OrderStatus.FAILED,
            OrderStatus.UNKNOWN,
        }

    @property
    def is_active(self) -> bool:
        """States where the order is still being processed."""
        return not self.is_terminal


class StrategyStatus(str, Enum):
    """
    Strategy lifecycle states.
    Per FINAL_SPECIFICATION/03_STATE_MACHINES.md:
    RESEARCH → CANDIDATE → BACKTESTED → WALK_FORWARD_VALIDATED → OOS_VALIDATED → STRESS_VALIDATED → SHADOW → DEMO → VALIDATION → APPROVAL_PENDING → LIVE_CANDIDATE → LIVE → DEGRADED → SUSPENDED → RETIRED
    """

    RESEARCH = "RESEARCH"
    CANDIDATE = "CANDIDATE"
    BACKTESTED = "BACKTESTED"
    WALK_FORWARD_VALIDATED = "WALK_FORWARD_VALIDATED"
    OOS_VALIDATED = "OOS_VALIDATED"
    STRESS_VALIDATED = "STRESS_VALIDATED"
    SHADOW = "SHADOW"
    DEMO = "DEMO"
    VALIDATION = "VALIDATION"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    LIVE_CANDIDATE = "LIVE_CANDIDATE"
    LIVE = "LIVE"
    DEGRADED = "DEGRADED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"

    @property
    def is_live(self) -> bool:
        """Whether this strategy state is in a live environment."""
        return self in {StrategyStatus.LIVE, StrategyStatus.DEGRADED, StrategyStatus.SUSPENDED}

    @property
    def can_transition_to_live(self) -> bool:
        """Whether this state can transition to LIVE."""
        return self == StrategyStatus.LIVE_CANDIDATE


class ReconciliationStatus(str, Enum):
    """
    Reconciliation lifecycle states.
    Per FINAL_SPECIFICATION/03_STATE_MACHINES.md:
    HEALTHY → CHECKING → MATCHED or MISMATCHED or UNKNOWN
    """

    HEALTHY = "HEALTHY"
    CHECKING = "CHECKING"
    MATCHED = "MATCHED"
    MISMATCHED = "MISMATCHED"
    UNKNOWN = "UNKNOWN"

    @property
    def blocks_live_mutation(self) -> bool:
        """Whether this state blocks live trading."""
        return self in {ReconciliationStatus.MISMATCHED, ReconciliationStatus.UNKNOWN}


class ProviderStatus(str, Enum):
    """
    Provider lifecycle states.
    Per FINAL_SPECIFICATION/03_STATE_MACHINES.md:
    DISCOVERED → EVALUATED → SANDBOX → DEMO → CERTIFIED → PRODUCTION_APPROVED → DEGRADED → SUSPENDED → RETIRED
    """

    DISCOVERED = "DISCOVERED"
    EVALUATED = "EVALUATED"
    SANDBOX = "SANDBOX"
    DEMO = "DEMO"
    CERTIFIED = "CERTIFIED"
    PRODUCTION_APPROVED = "PRODUCTION_APPROVED"
    DEGRADED = "DEGRADED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"

    @property
    def is_production_ready(self) -> bool:
        """Whether this provider is approved for production use."""
        return self == ProviderStatus.PRODUCTION_APPROVED


class AgentStatus(str, Enum):
    """
    Agent lifecycle states.
    Per FINAL_SPECIFICATION/03_STATE_MACHINES.md:
    REGISTERED → ENABLED → RUNNING → DEGRADED → QUARANTINED → DISABLED
    """

    REGISTERED = "REGISTERED"
    ENABLED = "ENABLED"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    QUARANTINED = "QUARANTINED"
    DISABLED = "DISABLED"

    @property
    def is_active(self) -> bool:
        """Whether this agent is active and can perform tasks."""
        return self in {AgentStatus.ENABLED, AgentStatus.RUNNING, AgentStatus.DEGRADED}


class EnvironmentStatus(str, Enum):
    """
    Environment lifecycle states.
    Per FINAL_SPECIFICATION/03_STATE_MACHINES.md:
    PROVISIONING → READY → RUNNING → DEGRADED → FROZEN → DRAINING → STOPPED
    """

    PROVISIONING = "PROVISIONING"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    FROZEN = "FROZEN"
    DRAINING = "DRAINING"
    STOPPED = "STOPPED"

    @property
    def is_trading_ready(self) -> bool:
        """Whether this environment is ready for trading."""
        return self == EnvironmentStatus.RUNNING


class EnvironmentType(str, Enum):
    """
    Environment types.
    Per FINAL_SPECIFICATION/01_ARCHITECTURE_DECISIONS.md AD-006:
    Research/Test/Staging/Shadow/Demo/Live are first-class environments.
    """

    RESEARCH = "RESEARCH"
    TEST = "TEST"
    STAGING = "STAGING"
    SHADOW = "SHADOW"
    DEMO = "DEMO"
    LIVE = "LIVE"

    @property
    def is_live(self) -> bool:
        """Whether this is the live (production) environment."""
        return self == EnvironmentType.LIVE

    @property
    def allows_live_credentials(self) -> bool:
        """Whether this environment can access live credentials."""
        return self == EnvironmentType.LIVE


class KillSwitchScope(str, Enum):
    """
    Kill switch hierarchy scopes.
    Per FINAL_SPECIFICATION/06_RISK_AND_LIVE_GATE.md:
    SYSTEM → MARKET → PORTFOLIO → STRATEGY → AGENT → TASK
    """

    SYSTEM = "SYSTEM"
    MARKET = "MARKET"
    PORTFOLIO = "PORTFOLIO"
    STRATEGY = "STRATEGY"
    AGENT = "AGENT"
    TASK = "TASK"

    @property
    def level(self) -> int:
        """Hierarchy level (higher = broader scope)."""
        levels = {
            KillSwitchScope.SYSTEM: 6,
            KillSwitchScope.MARKET: 5,
            KillSwitchScope.PORTFOLIO: 4,
            KillSwitchScope.STRATEGY: 3,
            KillSwitchScope.AGENT: 2,
            KillSwitchScope.TASK: 1,
        }
        return levels[self]


class ReasonCode(str, Enum):
    """
    Risk reason codes.
    Per docs/06_trading/03_RISK_REASON_CODES.md:
    Limit, exposure, liquidity, stale data, reconciliation, environment, policy, provider, strategy state and system health.
    """

    LIMIT = "LIMIT"
    EXPOSURE = "EXPOSURE"
    LIQUIDITY = "LIQUIDITY"
    STALE_DATA = "STALE_DATA"
    RECONCILIATION = "RECONCILIATION"
    ENVIRONMENT = "ENVIRONMENT"
    POLICY = "POLICY"
    PROVIDER = "PROVIDER"
    STRATEGY_STATE = "STRATEGY_STATE"
    SYSTEM_HEALTH = "SYSTEM_HEALTH"


class ErrorClass(str, Enum):
    """
    Error taxonomy classes.
    Per docs/14_reference/01_ERROR_TAXONOMY.md:
    Validation, authorization, policy, data-quality, provider, network, timeout, state-conflict, reconciliation, persistence, model and system-critical.
    """

    VALIDATION = "VALIDATION"
    AUTHORIZATION = "AUTHORIZATION"
    POLICY = "POLICY"
    DATA_QUALITY = "DATA_QUALITY"
    PROVIDER = "PROVIDER"
    NETWORK = "NETWORK"
    TIMEOUT = "TIMEOUT"
    STATE_CONFLICT = "STATE_CONFLICT"
    RECONCILIATION = "RECONCILIATION"
    PERSISTENCE = "PERSISTENCE"
    MODEL = "MODEL"
    SYSTEM_CRITICAL = "SYSTEM_CRITICAL"

    @property
    def is_fail_closed(self) -> bool:
        """Whether this error class triggers fail-closed behavior for live mutation."""
        return self in {
            ErrorClass.RECONCILIATION,
            ErrorClass.SYSTEM_CRITICAL,
            ErrorClass.STATE_CONFLICT,
        }


class Side(str, Enum):
    """Order side."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order types."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    ICEBERG = "ICEBERG"


class TimeInForce(str, Enum):
    """Time-in-force policies."""

    DAY = "DAY"
    GTC = "GTC"  # Good Till Cancelled
    GTD = "GTD"  # Good Till Date
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


class AssetClass(str, Enum):
    """Asset classes supported by the system."""

    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    STOCK = "STOCK"
    COMMODITY = "COMMODITY"


class DataQualityStatus(str, Enum):
    """Data quality status levels."""

    VALID = "VALID"
    STALE = "STALE"
    INVALID = "INVALID"
    MISSING = "MISSING"
    SUSPICIOUS = "SUSPICIOUS"


class NotificationSeverity(str, Enum):
    """Notification severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


__all__ = [
    "OrderStatus",
    "StrategyStatus",
    "ReconciliationStatus",
    "ProviderStatus",
    "AgentStatus",
    "EnvironmentStatus",
    "EnvironmentType",
    "KillSwitchScope",
    "ReasonCode",
    "ErrorClass",
    "Side",
    "OrderType",
    "TimeInForce",
    "AssetClass",
    "DataQualityStatus",
    "NotificationSeverity",
]
