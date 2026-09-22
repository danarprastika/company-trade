"""
G1.3 — Unit tests for Money and Quantity Types

Tests:
- Money creation, arithmetic, comparison
- Quantity creation, arithmetic, comparison
- Fixed-precision decimal semantics (no float)
- Currency mismatch rejection
- Scale mismatch rejection
"""

from decimal import Decimal
import pytest
from src.domain.money import Money, Quantity, DEFAULT_MONEY_SCALE, DEFAULT_QUANTITY_SCALE


class TestMoney:
    def test_from_string(self):
        """Money.from_string should create correct Money."""
        m = Money.from_string("100.50", "USD")
        assert m.amount == Decimal("100.50")
        assert m.currency == "USD"

    def test_from_float(self):
        """Money.from_float should convert via string to avoid float artifacts."""
        m = Money.from_float(100.50, "USD")
        assert m.amount == Decimal("100.50")

    def test_zero(self):
        """Money.zero should create zero-value Money."""
        m = Money.zero("USD")
        assert m.amount == Decimal("0.00")
        assert m.currency == "USD"

    def test_addition_same_currency(self):
        """Money addition should work for same currency."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("50.25", "USD")
        result = m1 + m2
        assert result.amount == Decimal("150.75")
        assert result.currency == "USD"

    def test_addition_different_currency_rejected(self):
        """Money addition should reject different currencies."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("50.25", "EUR")
        with pytest.raises(ValueError, match="Cannot add"):
            m1 + m2

    def test_subtraction_same_currency(self):
        """Money subtraction should work for same currency."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("50.25", "USD")
        result = m1 - m2
        assert result.amount == Decimal("50.25")

    def test_subtraction_different_currency_rejected(self):
        """Money subtraction should reject different currencies."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("50.25", "EUR")
        with pytest.raises(ValueError, match="Cannot subtract"):
            m1 - m2

    def test_multiplication_by_int(self):
        """Money multiplication by int should work."""
        m = Money.from_string("100.50", "USD")
        result = m * 3
        assert result.amount == Decimal("301.50")

    def test_multiplication_by_decimal(self):
        """Money multiplication by Decimal should work."""
        m = Money.from_string("100.50", "USD")
        result = m * Decimal("2.5")
        assert result.amount == Decimal("251.25")

    def test_multiplication_by_float_rejected(self):
        """Money multiplication by float should be rejected."""
        m = Money.from_string("100.50", "USD")
        with pytest.raises(TypeError, match="float"):
            m * 2.5

    def test_division_by_int(self):
        """Money division by int should work."""
        m = Money.from_string("100.00", "USD")
        result = m / 4
        assert result.amount == Decimal("25.00")

    def test_division_by_float_rejected(self):
        """Money division by float should be rejected."""
        m = Money.from_string("100.00", "USD")
        with pytest.raises(TypeError, match="float"):
            m / 2.5

    def test_negation(self):
        """Money negation should work."""
        m = Money.from_string("100.50", "USD")
        result = -m
        assert result.amount == Decimal("-100.50")

    def test_comparison(self):
        """Money comparison should work for same currency."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("50.25", "USD")
        assert m1 > m2
        assert m2 < m1
        assert m1 >= m2
        assert m2 <= m1

    def test_comparison_different_currency_rejected(self):
        """Money comparison should reject different currencies."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("50.25", "EUR")
        with pytest.raises(ValueError, match="Cannot compare"):
            m1 < m2

    def test_equality(self):
        """Money equality should compare amount and currency."""
        m1 = Money.from_string("100.50", "USD")
        m2 = Money.from_string("100.50", "USD")
        m3 = Money.from_string("100.50", "EUR")
        assert m1 == m2
        assert m1 != m3

    def test_hashable(self):
        """Money should be hashable."""
        m = Money.from_string("100.50", "USD")
        s = {m}
        assert m in s

    def test_precision_quantization(self):
        """Money should quantize to 2 decimal places."""
        m = Money.from_string("100.555", "USD")
        assert m.amount == Decimal("100.56")  # Rounded half up

    def test_currency_validation(self):
        """Currency must be 3-letter ISO code."""
        with pytest.raises(ValueError, match="3-letter"):
            Money(Decimal("100"), "US")

    def test_amount_must_be_decimal(self):
        """Amount must be Decimal, not float."""
        with pytest.raises(TypeError, match="Decimal"):
            Money(100.50, "USD")  # type: ignore


class TestQuantity:
    def test_from_string(self):
        """Quantity.from_string should create correct Quantity."""
        q = Quantity.from_string("100", scale=2)
        assert q.value == Decimal("100.00")
        assert q.scale == 2

    def test_from_float(self):
        """Quantity.from_float should convert via string."""
        q = Quantity.from_float(100.5, scale=2)
        assert q.value == Decimal("100.50")

    def test_zero(self):
        """Quantity.zero should create zero-value Quantity."""
        q = Quantity.zero(scale=2)
        assert q.value == Decimal("0.00")
        assert q.scale == 2

    def test_addition_same_scale(self):
        """Quantity addition should work for same scale."""
        q1 = Quantity.from_string("100.50", scale=2)
        q2 = Quantity.from_string("50.25", scale=2)
        result = q1 + q2
        assert result.value == Decimal("150.75")

    def test_addition_different_scale_rejected(self):
        """Quantity addition should reject different scales."""
        q1 = Quantity.from_string("100.50", scale=2)
        q2 = Quantity.from_string("50", scale=0)
        with pytest.raises(ValueError, match="scale"):
            q1 + q2

    def test_subtraction_same_scale(self):
        """Quantity subtraction should work for same scale."""
        q1 = Quantity.from_string("100.50", scale=2)
        q2 = Quantity.from_string("50.25", scale=2)
        result = q1 - q2
        assert result.value == Decimal("50.25")

    def test_multiplication_by_int(self):
        """Quantity multiplication by int should work."""
        q = Quantity.from_string("100.50", scale=2)
        result = q * 3
        assert result.value == Decimal("301.50")

    def test_multiplication_by_float_rejected(self):
        """Quantity multiplication by float should be rejected."""
        q = Quantity.from_string("100.50", scale=2)
        with pytest.raises(TypeError, match="float"):
            q * 2.5

    def test_division_by_int(self):
        """Quantity division by int should work."""
        q = Quantity.from_string("100.00", scale=2)
        result = q / 4
        assert result.value == Decimal("25.00")

    def test_division_by_float_rejected(self):
        """Quantity division by float should be rejected."""
        q = Quantity.from_string("100.00", scale=2)
        with pytest.raises(TypeError, match="float"):
            q / 2.5

    def test_negation(self):
        """Quantity negation should work."""
        q = Quantity.from_string("100.50", scale=2)
        result = -q
        assert result.value == Decimal("-100.50")

    def test_comparison(self):
        """Quantity comparison should work for same scale."""
        q1 = Quantity.from_string("100.50", scale=2)
        q2 = Quantity.from_string("50.25", scale=2)
        assert q1 > q2
        assert q2 < q1

    def test_comparison_different_scale_rejected(self):
        """Quantity comparison should reject different scales."""
        q1 = Quantity.from_string("100.50", scale=2)
        q2 = Quantity.from_string("50", scale=0)
        with pytest.raises(ValueError, match="scale"):
            q1 < q2

    def test_equality(self):
        """Quantity equality should compare value and scale."""
        q1 = Quantity.from_string("100.50", scale=2)
        q2 = Quantity.from_string("100.50", scale=2)
        q3 = Quantity.from_string("100.50", scale=0)
        assert q1 == q2
        assert q1 != q3

    def test_is_zero(self):
        """is_zero should return True for zero quantity."""
        q = Quantity.zero(scale=2)
        assert q.is_zero() is True

    def test_is_positive(self):
        """is_positive should return True for positive quantity."""
        q = Quantity.from_string("100.50", scale=2)
        assert q.is_positive() is True

    def test_is_negative(self):
        """is_negative should return True for negative quantity."""
        q = Quantity.from_string("-100.50", scale=2)
        assert q.is_negative() is True

    def test_hashable(self):
        """Quantity should be hashable."""
        q = Quantity.from_string("100.50", scale=2)
        s = {q}
        assert q in s

    def test_precision_quantization(self):
        """Quantity should quantize to specified scale."""
        q = Quantity.from_string("100.555", scale=2)
        assert q.value == Decimal("100.56")

    def test_scale_validation(self):
        """Scale must be non-negative integer."""
        with pytest.raises(ValueError, match="non-negative"):
            Quantity(Decimal("100"), -1)

    def test_value_must_be_decimal(self):
        """Value must be Decimal, not float."""
        with pytest.raises(TypeError, match="Decimal"):
            Quantity(100.50, 2)  # type: ignore
