"""
G1.5 — Unit tests for Enum Definitions

Tests:
- All enum values are correct
- State machine properties (is_terminal, is_active, etc.)
- Kill switch hierarchy levels
- Environment type properties
"""

import pytest
from src.domain.enums import (
    OrderStatus,
    StrategyStatus,
    ReconciliationStatus,
    ProviderStatus,
    AgentStatus,
    EnvironmentStatus,
    EnvironmentType,
    KillSwitchScope,
    ReasonCode,
    ErrorClass,
    Side,
    OrderType,
    TimeInForce,
    AssetClass,
    DataQualityStatus,
    NotificationSeverity,
)


class TestOrderStatus:
    def test_all_states_present(self):
        """All order states from FINAL_SPECIFICATION/03_STATE_MACHINES.md should be present."""
        expected = {
            "DRAFT", "RISK_PENDING", "RISK_APPROVED", "OMS_ACCEPTED",
            "SUBMITTING", "ACKNOWLEDGED", "PARTIALLY_FILLED", "FILLED",
            "CANCEL_PENDING", "CANCELLED", "REJECTED", "EXPIRED", "FAILED", "UNKNOWN",
        }
        actual = {s.value for s in OrderStatus}
        assert actual == expected

    def test_terminal_states(self):
        """Terminal states should be correctly identified."""
        terminal = {
            OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED,
            OrderStatus.EXPIRED, OrderStatus.FAILED, OrderStatus.UNKNOWN,
        }
        for status in OrderStatus:
            if status in terminal:
                assert status.is_terminal is True
                assert status.is_active is False
            else:
                assert status.is_terminal is False
                assert status.is_active is True

    def test_str_enum(self):
        """OrderStatus should be a string enum."""
        assert OrderStatus.DRAFT.value == "DRAFT"
        assert isinstance(OrderStatus.DRAFT.value, str)


class TestStrategyStatus:
    def test_all_states_present(self):
        """All strategy states from FINAL_SPECIFICATION/03_STATE_MACHINES.md should be present."""
        expected = {
            "RESEARCH", "CANDIDATE", "BACKTESTED", "WALK_FORWARD_VALIDATED",
            "OOS_VALIDATED", "STRESS_VALIDATED", "SHADOW", "DEMO",
            "VALIDATION", "APPROVAL_PENDING", "LIVE_CANDIDATE", "LIVE",
            "DEGRADED", "SUSPENDED", "RETIRED",
        }
        actual = {s.value for s in StrategyStatus}
        assert actual == expected

    def test_is_live(self):
        """Live states should be correctly identified."""
        live_states = {StrategyStatus.LIVE, StrategyStatus.DEGRADED, StrategyStatus.SUSPENDED}
        for status in StrategyStatus:
            if status in live_states:
                assert status.is_live is True
            else:
                assert status.is_live is False

    def test_can_transition_to_live(self):
        """Only LIVE_CANDIDATE can transition to LIVE."""
        assert StrategyStatus.LIVE_CANDIDATE.can_transition_to_live is True
        assert StrategyStatus.LIVE.can_transition_to_live is False
        assert StrategyStatus.RESEARCH.can_transition_to_live is False


class TestReconciliationStatus:
    def test_all_states_present(self):
        """All reconciliation states should be present."""
        expected = {"HEALTHY", "CHECKING", "MATCHED", "MISMATCHED", "UNKNOWN"}
        actual = {s.value for s in ReconciliationStatus}
        assert actual == expected

    def test_blocks_live_mutation(self):
        """MISMATCHED and UNKNOWN should block live mutation."""
        assert ReconciliationStatus.MISMATCHED.blocks_live_mutation is True
        assert ReconciliationStatus.UNKNOWN.blocks_live_mutation is True
        assert ReconciliationStatus.HEALTHY.blocks_live_mutation is False
        assert ReconciliationStatus.MATCHED.blocks_live_mutation is False


class TestProviderStatus:
    def test_all_states_present(self):
        """All provider states should be present."""
        expected = {
            "DISCOVERED", "EVALUATED", "SANDBOX", "DEMO", "CERTIFIED",
            "PRODUCTION_APPROVED", "DEGRADED", "SUSPENDED", "RETired",
        }
        # Note: RETIRED is uppercase in spec
        expected = {
            "DISCOVERED", "EVALUATED", "SANDBOX", "DEMO", "CERTIFIED",
            "PRODUCTION_APPROVED", "DEGRADED", "SUSPENDED", "RETIRED",
        }
        actual = {s.value for s in ProviderStatus}
        assert actual == expected

    def test_is_production_ready(self):
        """Only PRODUCTION_APPROVED is production ready."""
        assert ProviderStatus.PRODUCTION_APPROVED.is_production_ready is True
        assert ProviderStatus.CERTIFIED.is_production_ready is False
        assert ProviderStatus.DEMO.is_production_ready is False


class TestAgentStatus:
    def test_all_states_present(self):
        """All agent states should be present."""
        expected = {"REGISTERED", "ENABLED", "RUNNING", "DEGRADED", "QUARANTINED", "DISABLED"}
        actual = {s.value for s in AgentStatus}
        assert actual == expected

    def test_is_active(self):
        """ENABLED, RUNNING, DEGRADED should be active."""
        active = {AgentStatus.ENABLED, AgentStatus.RUNNING, AgentStatus.DEGRADED}
        for status in AgentStatus:
            if status in active:
                assert status.is_active is True
            else:
                assert status.is_active is False


class TestEnvironmentStatus:
    def test_all_states_present(self):
        """All environment states should be present."""
        expected = {"PROVISIONING", "READY", "RUNNING", "DEGRADED", "FROZEN", "DRAINING", "STOPPED"}
        actual = {s.value for s in EnvironmentStatus}
        assert actual == expected

    def test_is_trading_ready(self):
        """Only RUNNING is trading ready."""
        assert EnvironmentStatus.RUNNING.is_trading_ready is True
        assert EnvironmentStatus.READY.is_trading_ready is False
        assert EnvironmentStatus.DEGRADED.is_trading_ready is False


class TestEnvironmentType:
    def test_all_types_present(self):
        """All environment types should be present."""
        expected = {"RESEARCH", "TEST", "STAGING", "SHADOW", "DEMO", "LIVE"}
        actual = {s.value for s in EnvironmentType}
        assert actual == expected

    def test_is_live(self):
        """Only LIVE is live."""
        assert EnvironmentType.LIVE.is_live is True
        assert EnvironmentType.DEMO.is_live is False
        assert EnvironmentType.RESEARCH.is_live is False

    def test_allows_live_credentials(self):
        """Only LIVE allows live credentials."""
        assert EnvironmentType.LIVE.allows_live_credentials is True
        assert EnvironmentType.DEMO.allows_live_credentials is False
        assert EnvironmentType.RESEARCH.allows_live_credentials is False


class TestKillSwitchScope:
    def test_all_scopes_present(self):
        """All kill switch scopes should be present."""
        expected = {"SYSTEM", "MARKET", "PORTFOLIO", "STRATEGY", "AGENT", "TASK"}
        actual = {s.value for s in KillSwitchScope}
        assert actual == expected

    def test_hierarchy_levels(self):
        """Kill switch hierarchy: SYSTEM > MARKET > PORTFOLIO > STRATEGY > AGENT > TASK."""
        assert KillSwitchScope.SYSTEM.level == 6
        assert KillSwitchScope.MARKET.level == 5
        assert KillSwitchScope.PORTFOLIO.level == 4
        assert KillSwitchScope.STRATEGY.level == 3
        assert KillSwitchScope.AGENT.level == 2
        assert KillSwitchScope.TASK.level == 1


class TestReasonCode:
    def test_all_codes_present(self):
        """All risk reason codes should be present."""
        expected = {
            "LIMIT", "EXPOSURE", "LIQUIDITY", "STALE_DATA", "RECONCILIATION",
            "ENVIRONMENT", "POLICY", "PROVIDER", "STRATEGY_STATE", "SYSTEM_HEALTH",
        }
        actual = {s.value for s in ReasonCode}
        assert actual == expected


class TestErrorClass:
    def test_all_classes_present(self):
        """All error classes should be present."""
        expected = {
            "VALIDATION", "AUTHORIZATION", "POLICY", "DATA_QUALITY",
            "PROVIDER", "NETWORK", "TIMEOUT", "STATE_CONFLICT",
            "RECONCILIATION", "PERSISTENCE", "MODEL", "SYSTEM_CRITICAL",
        }
        actual = {s.value for s in ErrorClass}
        assert actual == expected

    def test_is_fail_closed(self):
        """RECONCILIATION, SYSTEM_CRITICAL, STATE_CONFLICT should be fail-closed."""
        assert ErrorClass.RECONCILIATION.is_fail_closed is True
        assert ErrorClass.SYSTEM_CRITICAL.is_fail_closed is True
        assert ErrorClass.STATE_CONFLICT.is_fail_closed is True
        assert ErrorClass.VALIDATION.is_fail_closed is False
        assert ErrorClass.NETWORK.is_fail_closed is False


class TestOtherEnums:
    def test_side(self):
        """Side enum should have BUY and SELL."""
        assert Side.BUY.value == "BUY"
        assert Side.SELL.value == "SELL"

    def test_order_type(self):
        """OrderType enum should have all types."""
        expected = {"MARKET", "LIMIT", "STOP", "STOP_LIMIT", "ICEBERG"}
        actual = {s.value for s in OrderType}
        assert actual == expected

    def test_time_in_force(self):
        """TimeInForce enum should have all types."""
        expected = {"DAY", "GTC", "GTD", "IOC", "FOK"}
        actual = {s.value for s in TimeInForce}
        assert actual == expected

    def test_asset_class(self):
        """AssetClass enum should have all types."""
        expected = {"CRYPTO", "FOREX", "STOCK", "COMMODITY"}
        actual = {s.value for s in AssetClass}
        assert actual == expected

    def test_data_quality_status(self):
        """DataQualityStatus enum should have all types."""
        expected = {"VALID", "STALE", "INVALID", "MISSING", "SUSPICIOUS"}
        actual = {s.value for s in DataQualityStatus}
        assert actual == expected

    def test_notification_severity(self):
        """NotificationSeverity enum should have all types."""
        expected = {"INFO", "WARNING", "CRITICAL", "EMERGENCY"}
        actual = {s.value for s in NotificationSeverity}
        assert actual == expected
