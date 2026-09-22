"""
G1.6 — Unit tests for Error Taxonomy

Tests:
- TradingError base type
- All error subclasses
- Error serialization
- Fail-closed behavior
"""

import pytest
from src.domain.errors import (
    ErrorDefinition,
    ErrorTaxonomy,
    TradingError,
    ValidationError,
    AuthorizationError,
    PolicyError,
    DataQualityError,
    ProviderError,
    NetworkError,
    TimeoutError,
    StateConflictError,
    ReconciliationError,
    PersistenceError,
    ModelError,
    SystemCriticalError,
    get_default_taxonomy,
)
from src.domain.enums import ErrorClass, ReasonCode


class TestTradingError:
    def test_base_error_creation(self):
        """TradingError should be creatable with all fields."""
        error = TradingError(
            error_class=ErrorClass.VALIDATION,
            reason_code=None,
            message="Test error",
        )
        assert error.error_class == ErrorClass.VALIDATION
        assert error.message == "Test error"
        assert error.retryable is False

    def test_str_representation(self):
        """str() should include error class and message."""
        error = TradingError(
            error_class=ErrorClass.POLICY,
            reason_code=ReasonCode.LIMIT,
            message="Limit exceeded",
        )
        assert "[POLICY]" in str(error)
        assert "Limit exceeded" in str(error)

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        error = TradingError(
            error_class=ErrorClass.VALIDATION,
            reason_code=None,
            message="Test error",
            details={"field": "value"},
            correlation_id="corr-123",
        )
        d = error.to_dict()
        assert d["error_class"] == "VALIDATION"
        assert d["message"] == "Test error"
        assert d["details"] == {"field": "value"}
        assert d["correlation_id"] == "corr-123"
        assert d["retryable"] is False

    def test_timestamp_auto_set(self):
        """Timestamp should be auto-set if not provided."""
        error = TradingError(
            error_class=ErrorClass.VALIDATION,
            reason_code=None,
            message="Test",
        )
        assert error.timestamp is not None

    def test_is_exception(self):
        """TradingError should be an Exception subclass."""
        error = TradingError(
            error_class=ErrorClass.VALIDATION,
            reason_code=None,
            message="Test",
        )
        assert isinstance(error, Exception)


class TestValidationError:
    def test_creation(self):
        """ValidationError should set correct error class."""
        error = ValidationError("Invalid input")
        assert error.error_class == ErrorClass.VALIDATION
        assert error.retryable is False

    def test_with_details(self):
        """ValidationError should accept details."""
        error = ValidationError("Invalid input", details={"field": "quantity"})
        assert error.details == {"field": "quantity"}


class TestAuthorizationError:
    def test_creation(self):
        """AuthorizationError should set correct error class."""
        error = AuthorizationError("Access denied")
        assert error.error_class == ErrorClass.AUTHORIZATION
        assert error.retryable is False


class TestPolicyError:
    def test_creation(self):
        """PolicyError should set correct error class and reason code."""
        error = PolicyError("Limit exceeded", reason_code=ReasonCode.LIMIT)
        assert error.error_class == ErrorClass.POLICY
        assert error.reason_code == ReasonCode.LIMIT
        assert error.retryable is False


class TestDataQualityError:
    def test_creation(self):
        """DataQualityError should set correct error class and be retryable."""
        error = DataQualityError("Stale data")
        assert error.error_class == ErrorClass.DATA_QUALITY
        assert error.retryable is True

    def test_default_reason_code(self):
        """DataQualityError should default to STALE_DATA reason code."""
        error = DataQualityError("Stale data")
        assert error.reason_code == ReasonCode.STALE_DATA


class TestProviderError:
    def test_creation(self):
        """ProviderError should set correct error class and be retryable."""
        error = ProviderError("Provider unavailable")
        assert error.error_class == ErrorClass.PROVIDER
        assert error.retryable is True

    def test_non_retryable(self):
        """ProviderError should support non-retryable mode."""
        error = ProviderError("Provider error", retryable=False)
        assert error.retryable is False


class TestNetworkError:
    def test_creation(self):
        """NetworkError should set correct error class and be retryable."""
        error = NetworkError("Connection refused")
        assert error.error_class == ErrorClass.NETWORK
        assert error.retryable is True


class TestTimeoutError:
    def test_creation(self):
        """TimeoutError should set correct error class and be retryable."""
        error = TimeoutError("Request timed out")
        assert error.error_class == ErrorClass.TIMEOUT
        assert error.retryable is True


class TestStateConflictError:
    def test_creation(self):
        """StateConflictError should set correct error class and not be retryable."""
        error = StateConflictError("Invalid state transition")
        assert error.error_class == ErrorClass.STATE_CONFLICT
        assert error.retryable is False


class TestReconciliationError:
    def test_creation(self):
        """ReconciliationError should set correct error class and not be retryable."""
        error = ReconciliationError("Mismatch detected")
        assert error.error_class == ErrorClass.RECONCILIATION
        assert error.retryable is False

    def test_default_reason_code(self):
        """ReconciliationError should default to RECONCILIATION reason code."""
        error = ReconciliationError("Mismatch detected")
        assert error.reason_code == ReasonCode.RECONCILIATION


class TestPersistenceError:
    def test_creation(self):
        """PersistenceError should set correct error class and be retryable."""
        error = PersistenceError("Database error")
        assert error.error_class == ErrorClass.PERSISTENCE
        assert error.retryable is True


class TestModelError:
    def test_creation(self):
        """ModelError should set correct error class and be retryable."""
        error = ModelError("Model output invalid")
        assert error.error_class == ErrorClass.MODEL
        assert error.retryable is True


class TestSystemCriticalError:
    def test_creation(self):
        """SystemCriticalError should set correct error class and not be retryable."""
        error = SystemCriticalError("Critical system failure")
        assert error.error_class == ErrorClass.SYSTEM_CRITICAL
        assert error.retryable is False

    def test_fail_closed(self):
        """SystemCriticalError should be fail-closed."""
        error = SystemCriticalError("Critical system failure")
        assert error.error_class.is_fail_closed is True


class TestErrorDefinition:
    def test_creation(self):
        """ErrorDefinition should be creatable with all fields."""
        definition = ErrorDefinition(
            code="TEST_ERROR",
            message_template="Test error: {detail}",
            error_class=ErrorClass.VALIDATION,
            reason_code=ReasonCode.POLICY,
            retryable=False,
            scope="domain",
        )
        assert definition.code == "TEST_ERROR"
        assert definition.message_template == "Test error: {detail}"
        assert definition.error_class == ErrorClass.VALIDATION
        assert definition.reason_code == ReasonCode.POLICY
        assert definition.retryable is False
        assert definition.scope == "domain"

    def test_format_message(self):
        """format_message should substitute template parameters."""
        definition = ErrorDefinition(
            code="TEST_ERROR",
            message_template="Invalid value: {value}",
            error_class=ErrorClass.VALIDATION,
        )
        assert definition.format_message(value="42") == "Invalid value: 42"

    def test_required_code(self):
        """ErrorDefinition should require a code."""
        with pytest.raises(ValueError, match="code is required"):
            ErrorDefinition(
                code="",
                message_template="Test",
                error_class=ErrorClass.VALIDATION,
            )

    def test_required_message_template(self):
        """ErrorDefinition should require a message_template."""
        with pytest.raises(ValueError, match="message_template is required"):
            ErrorDefinition(
                code="TEST",
                message_template="",
                error_class=ErrorClass.VALIDATION,
            )

    def test_default_values(self):
        """ErrorDefinition should have sensible defaults."""
        definition = ErrorDefinition(
            code="TEST",
            message_template="Test",
            error_class=ErrorClass.VALIDATION,
        )
        assert definition.reason_code is None
        assert definition.retryable is False
        assert definition.scope == "domain"

    def test_immutable(self):
        """ErrorDefinition should be immutable."""
        definition = ErrorDefinition(
            code="TEST",
            message_template="Test",
            error_class=ErrorClass.VALIDATION,
        )
        with pytest.raises(Exception):
            definition.code = "OTHER"


class TestErrorTaxonomy:
    def test_register_and_get(self):
        """ErrorTaxonomy should register and retrieve definitions by code."""
        taxonomy = ErrorTaxonomy()
        definition = ErrorDefinition(
            code="CUSTOM_ERROR",
            message_template="Custom error",
            error_class=ErrorClass.VALIDATION,
        )
        taxonomy.register(definition)
        assert taxonomy.get("CUSTOM_ERROR") is definition

    def test_get_nonexistent(self):
        """get should return None for unregistered codes."""
        taxonomy = ErrorTaxonomy()
        assert taxonomy.get("NONEXISTENT") is None

    def test_duplicate_registration_raises(self):
        """Registering a duplicate code should raise ValueError."""
        taxonomy = ErrorTaxonomy()
        definition = ErrorDefinition(
            code="DUPLICATE",
            message_template="Test",
            error_class=ErrorClass.VALIDATION,
        )
        taxonomy.register(definition)
        with pytest.raises(ValueError, match="already registered"):
            taxonomy.register(definition)

    def test_get_by_class(self):
        """get_by_class should return all definitions for an error class."""
        taxonomy = ErrorTaxonomy()
        def1 = ErrorDefinition(
            code="ERR1",
            message_template="Error 1",
            error_class=ErrorClass.VALIDATION,
        )
        def2 = ErrorDefinition(
            code="ERR2",
            message_template="Error 2",
            error_class=ErrorClass.VALIDATION,
        )
        def3 = ErrorDefinition(
            code="ERR3",
            message_template="Error 3",
            error_class=ErrorClass.NETWORK,
        )
        taxonomy.register(def1)
        taxonomy.register(def2)
        taxonomy.register(def3)
        validation_errors = taxonomy.get_by_class(ErrorClass.VALIDATION)
        assert len(validation_errors) == 2
        assert def1 in validation_errors
        assert def2 in validation_errors

    def test_get_by_scope(self):
        """get_by_scope should return all definitions for a scope."""
        taxonomy = ErrorTaxonomy()
        def1 = ErrorDefinition(
            code="ERR1",
            message_template="Error 1",
            error_class=ErrorClass.VALIDATION,
            scope="domain",
        )
        def2 = ErrorDefinition(
            code="ERR2",
            message_template="Error 2",
            error_class=ErrorClass.NETWORK,
            scope="infrastructure",
        )
        taxonomy.register(def1)
        taxonomy.register(def2)
        domain_errors = taxonomy.get_by_scope("domain")
        assert len(domain_errors) == 1
        assert def1 in domain_errors

    def test_all_codes(self):
        """all_codes should return all registered codes."""
        taxonomy = ErrorTaxonomy()
        taxonomy.register(ErrorDefinition(
            code="ERR1", message_template="E1", error_class=ErrorClass.VALIDATION
        ))
        taxonomy.register(ErrorDefinition(
            code="ERR2", message_template="E2", error_class=ErrorClass.NETWORK
        ))
        codes = taxonomy.all_codes()
        assert "ERR1" in codes
        assert "ERR2" in codes
        assert len(codes) == 2

    def test_contains(self):
        """__contains__ should check for registered codes."""
        taxonomy = ErrorTaxonomy()
        taxonomy.register(ErrorDefinition(
            code="EXISTS", message_template="Test", error_class=ErrorClass.VALIDATION
        ))
        assert "EXISTS" in taxonomy
        assert "NOT_EXISTS" not in taxonomy

    def test_len(self):
        """__len__ should return the number of registered definitions."""
        taxonomy = ErrorTaxonomy()
        assert len(taxonomy) == 0
        taxonomy.register(ErrorDefinition(
            code="ERR1", message_template="E1", error_class=ErrorClass.VALIDATION
        ))
        assert len(taxonomy) == 1

    def test_get_by_class_empty(self):
        """get_by_class should return empty list for unregistered class."""
        taxonomy = ErrorTaxonomy()
        assert taxonomy.get_by_class(ErrorClass.VALIDATION) == []

    def test_get_by_scope_empty(self):
        """get_by_scope should return empty list for unregistered scope."""
        taxonomy = ErrorTaxonomy()
        assert taxonomy.get_by_scope("nonexistent") == []


class TestDefaultTaxonomy:
    def test_default_taxonomy_has_entries(self):
        """Default taxonomy should have standard error definitions."""
        taxonomy = get_default_taxonomy()
        assert len(taxonomy) > 0

    def test_default_taxonomy_contains_validation(self):
        """Default taxonomy should include validation error."""
        taxonomy = get_default_taxonomy()
        assert "VALIDATION_ERROR" in taxonomy

    def test_default_taxonomy_contains_system_critical(self):
        """Default taxonomy should include system critical error."""
        taxonomy = get_default_taxonomy()
        assert "SYSTEM_CRITICAL" in taxonomy

    def test_default_taxonomy_all_classes_covered(self):
        """Default taxonomy should cover all error classes."""
        taxonomy = get_default_taxonomy()
        codes = taxonomy.all_codes()
        # Verify each error class has at least one definition
        for error_class in ErrorClass:
            definitions = taxonomy.get_by_class(error_class)
            assert len(definitions) > 0, f"No definitions for {error_class}"

    def test_default_taxonomy_definitions_valid(self):
        """All default definitions should have valid fields."""
        taxonomy = get_default_taxonomy()
        for code in taxonomy.all_codes():
            definition = taxonomy.get(code)
            assert definition is not None
            assert definition.code == code
            assert definition.message_template
            assert definition.error_class in ErrorClass
